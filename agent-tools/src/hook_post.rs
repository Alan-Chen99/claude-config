use anyhow::{Context, Result};
use chrono::{Duration, Utc};
use nix::fcntl::{Flock, FlockArg};
use std::collections::{BTreeMap, HashMap, HashSet};
use std::fs;
use std::io::Read;
use std::path::{Path, PathBuf};

use crate::events;
use crate::hook_input;
use crate::meta::ChildMeta;
use crate::paths;

/// Header prefix for late-capture emissions. Quoted verbatim in the system
/// prompt section "Bash Output Recovery (agent-tools run)". Drift between
/// the two breaks agent recognition silently — see agent-tools/CLAUDE.md.
const LATE_CAPTURES_HEADER_PREFIX: &str = "Late captures from prior backgrounded call ";

/// A child_started entry with no matching child_exit is treated as finalized
/// once this many seconds have elapsed. Covers SIGKILL / host-shutdown paths
/// where the agent-tools parent could not write the exit event.
const UNFINALIZED_STALE_SECS: i64 = 300;

/// Per-scope ledger of (toolu_id -> [surfaced child_pid, ...]).
type Ledger = BTreeMap<String, Vec<i64>>;

pub fn run() -> Result<()> {
    let mut buf = String::new();
    std::io::stdin()
        .read_to_string(&mut buf)
        .context("read stdin")?;

    let input = match hook_input::parse_post(&buf) {
        Ok(p) => p,
        Err(e) => {
            eprintln!("agent-tools hook-post: parse error: {e:#}");
            return Ok(());
        }
    };

    // Bash and Monitor produce their own wrap captures and may auto-background.
    // Read produces no captures but is included so the task-notification ->
    // Read .output recovery path also triggers the late-capture scan.
    if input.tool_name != "Bash" && input.tool_name != "Monitor" && input.tool_name != "Read" {
        return Ok(());
    }

    let mut parts: Vec<String> = Vec::new();

    // Per-call captures and backgrounding notice apply only to wrap-producing tools.
    let mut current_captures: Vec<Capture> = Vec::new();
    if input.tool_name != "Read" {
        let parent_dir = paths::parent_dir_for(
            &input.session_id,
            input.agent_id.as_deref(),
            &input.tool_use_id,
        )?;
        current_captures = list_captures(&parent_dir);
        if !current_captures.is_empty() {
            let listing: Vec<String> = current_captures.iter().map(format_capture).collect();
            parts.push(format!(
                "[agent-tools] captures from this Bash call: {}",
                listing.join("; "),
            ));
        }
        if let Some(b) = bg_notice(&input) {
            parts.push(b);
        }
    }

    // Single critical section: seed the ledger with this call's PIDs (so the
    // catch-up scan does not re-emit them later), then scan prior toolu_ids
    // for late captures. Flock on a sibling .lock sentinel serializes parallel
    // hook processes that fire concurrently (Claude Code runs same-message
    // tool calls in parallel; each hook is its own process).
    match update_ledger_and_scan(&input, &current_captures) {
        Ok(late_lines) => parts.extend(late_lines),
        Err(e) => eprintln!("agent-tools hook-post: ledger/scan error: {e:#}"),
    }

    if parts.is_empty() {
        return Ok(());
    }

    let out = serde_json::json!({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": parts.join(" ")
        }
    });
    println!("{}", serde_json::to_string(&out)?);
    Ok(())
}

struct Capture {
    dir: PathBuf,
    desc: Option<String>,
}

fn list_captures(parent_dir: &Path) -> Vec<Capture> {
    if !parent_dir.is_dir() {
        return Vec::new();
    }
    let rd = match fs::read_dir(parent_dir) {
        Ok(r) => r,
        Err(_) => return Vec::new(),
    };
    let mut out = Vec::new();
    for entry in rd.flatten() {
        let p = entry.path();
        if !p.is_dir() {
            continue;
        }
        let desc = fs::read_to_string(p.join("meta.json"))
            .ok()
            .and_then(|s| serde_json::from_str::<ChildMeta>(&s).ok())
            .and_then(|c| c.desc);
        out.push(Capture { dir: p, desc });
    }
    out.sort_by(|a, b| a.dir.cmp(&b.dir));
    out
}

fn format_capture(c: &Capture) -> String {
    let details = format_details(&c.dir, false);
    let path_frag = format!("{}/{{stdout,stderr}}", c.dir.display());
    match &c.desc {
        Some(d) => format!("{d}{details} → {path_frag}"),
        // No-desc: details starts with a leading space; trim so the line begins
        // with the bracket. Result: "[details] → <path>/{stdout,stderr}".
        None => format!("{} → {path_frag}", details.trim_start()),
    }
}

/// Format the bracket containing run details: exit code (or `unfinalized`),
/// elapsed time, and stdout/stderr byte sizes. Returns a leading-space-prefixed
/// string like ` [exit=0 1ms out=12B err=0B]`. Never returns empty — sizes are
/// always available from the filesystem even when meta.json is missing.
///
/// `force_unfinalized` adds an `unfinalized` token when the caller (e.g.
/// `scan_priors`) determined the process is in-flight or stale based on the
/// events.jsonl timeline, but meta.json hasn't been updated to reflect that
/// (e.g. SIGKILL before the parent could write the final meta).
fn format_details(child_dir: &Path, force_unfinalized: bool) -> String {
    let stdout_bytes = file_size(&child_dir.join("stdout"));
    let stderr_bytes = file_size(&child_dir.join("stderr"));
    let meta = fs::read_to_string(child_dir.join("meta.json"))
        .ok()
        .and_then(|s| serde_json::from_str::<ChildMeta>(&s).ok());

    let mut bits: Vec<String> = Vec::new();
    let mut emitted_unfinalized = false;
    if let Some(m) = &meta {
        match m.reaped.map(|r| r.status) {
            Some(code) => {
                bits.push(format!("exit={code}"));
                if let Some(end) = m.reaped.map(|r| r.at) {
                    bits.push(format_duration(end.signed_duration_since(m.started_at)));
                }
            }
            None => {
                bits.push("unfinalized".to_string());
                emitted_unfinalized = true;
                bits.push(format!(
                    "ran {}",
                    format_duration(Utc::now().signed_duration_since(m.started_at)),
                ));
            }
        }
    }
    if force_unfinalized && !emitted_unfinalized {
        bits.insert(0, "unfinalized".to_string());
    }
    bits.push(format!("out={}", format_size(stdout_bytes)));
    bits.push(format!("err={}", format_size(stderr_bytes)));

    format!(" [{}]", bits.join(" "))
}

fn file_size(path: &Path) -> u64 {
    fs::metadata(path).map(|m| m.len()).unwrap_or(0)
}

/// Compact human-readable duration: `850µs`, `12ms`, `3.4s`, `2m15s`, `1h30m`.
/// Negative durations clamp to zero (callers compute `end - start` on
/// occasionally-skewed clocks).
fn format_duration(d: Duration) -> String {
    let micros = d.num_microseconds().unwrap_or(i64::MAX).max(0);
    if micros < 1_000 {
        format!("{micros}µs")
    } else if micros < 1_000_000 {
        format!("{}ms", micros / 1_000)
    } else if micros < 60_000_000 {
        // Round to one decimal: 1.0s..59.9s.
        let tenths = (micros + 50_000) / 100_000;
        format!("{}.{}s", tenths / 10, tenths % 10)
    } else {
        let total = d.num_seconds().max(0);
        let mins = total / 60;
        let secs = total % 60;
        if mins < 60 {
            format!("{mins}m{secs}s")
        } else {
            let hrs = mins / 60;
            let m = mins % 60;
            format!("{hrs}h{m}m")
        }
    }
}

/// Compact byte-size: `0B`, `512B`, `4KB`, `12MB`, `1.3GB`. Uses 1024-based
/// units (KB = 1024 B, etc.) — terse, not strictly SI.
fn format_size(bytes: u64) -> String {
    const KIB: u64 = 1024;
    const MIB: u64 = KIB * 1024;
    const GIB: u64 = MIB * 1024;
    if bytes < KIB {
        format!("{bytes}B")
    } else if bytes < MIB {
        format!("{}KB", bytes / KIB)
    } else if bytes < GIB {
        format!("{}MB", bytes / MIB)
    } else {
        format!("{:.1}GB", bytes as f64 / GIB as f64)
    }
}

fn bg_notice(input: &hook_input::PostToolUseInput) -> Option<String> {
    let bg_task_id = input
        .tool_response
        .get("backgroundTaskId")
        .and_then(|v| v.as_str())?;
    let auto = input
        .tool_response
        .get("assistantAutoBackgrounded")
        .and_then(|v| v.as_bool())
        .unwrap_or(false);
    let user = input
        .tool_response
        .get("backgroundedByUser")
        .and_then(|v| v.as_bool())
        .unwrap_or(false);
    // Explicit run_in_background: BashTool returns backgroundTaskId with both
    // assistantAutoBackgrounded and backgroundedByUser unset
    // (BashTool.tsx:989-1000). Without this check we'd misreport it as a
    // timeout. tool_input here is whatever the pre-hook handed back as
    // updatedInput; the rewrite preserves run_in_background verbatim.
    let explicit = input
        .tool_input
        .get("run_in_background")
        .and_then(|v| v.as_bool())
        .unwrap_or(false);
    let cause = if auto {
        "assistant-mode auto-background (KAIROS)".to_string()
    } else if user {
        "user manually backgrounded (Ctrl+B)".to_string()
    } else if explicit {
        "explicit run_in_background: true".to_string()
    } else {
        let limit = input
            .tool_input
            .get("timeout")
            .and_then(|v| v.as_u64())
            .unwrap_or(120_000);
        format!("timeout ({limit}ms limit hit)")
    };
    // "Backgrounded" (not "involuntarily backgrounded") — auto/user/timeout are
    // involuntary from the model's view, but explicit run_in_background is
    // voluntary; the `Cause:` line carries the distinction.
    Some(format!(
        "BACKGROUNDED: Command was backgrounded. Cause: {cause}. \
         Process is still running (task_id: {bg_task_id}). \
         To kill it: use TaskStop tool with task_id {bg_task_id}."
    ))
}

/// Scope dir = ~/.claude/agent-tools/<session_id>[/<agent_id>]. Tool_use_id
/// dirs and the ledger live directly under this scope. Subagents have their
/// own scope (their ledger is independent), so cross-agent leakage cannot
/// occur even within one session.
fn scope_dir(session_id: &str, agent_id: Option<&str>) -> Result<PathBuf> {
    let mut p = paths::state_root()?.join(session_id);
    if let Some(a) = agent_id {
        p.push(a);
    }
    Ok(p)
}

fn pid_from_dir(dir: &Path) -> Option<i64> {
    dir.file_name()?.to_str()?.parse().ok()
}

/// Acquire the per-scope ledger lock and run the seed-and-scan under it.
/// Returns the late-capture emission lines (already formatted, headerless
/// "[agent-tools] " prefix omitted — the header is recognizable by the
/// LATE_CAPTURES_HEADER_PREFIX constant which is also quoted by the prompt).
fn update_ledger_and_scan(
    input: &hook_input::PostToolUseInput,
    current_captures: &[Capture],
) -> Result<Vec<String>> {
    let scope = scope_dir(&input.session_id, input.agent_id.as_deref())?;
    if !scope.is_dir() {
        return Ok(Vec::new());
    }
    fs::create_dir_all(&scope).ok();
    let lock_path = scope.join(".hook-post-surfaced.lock");
    let ledger_path = scope.join(".hook-post-surfaced.json");

    let lock_file = fs::OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .truncate(false)
        .open(&lock_path)
        .with_context(|| format!("open lock {}", lock_path.display()))?;
    let _flock = Flock::lock(lock_file, FlockArg::LockExclusive)
        .map_err(|(_, e)| anyhow::anyhow!("flock LOCK_EX on {}: {e}", lock_path.display()))?;

    let mut ledger = read_ledger(&ledger_path);

    // Seed: record this call's PIDs as surfaced. The PostToolUse for THIS
    // tool_use_id already emitted them in the "captures from this Bash call"
    // section above, so the catch-up scan must not re-emit them when a later
    // hook fires.
    if !current_captures.is_empty() {
        let entry = ledger.entry(input.tool_use_id.clone()).or_default();
        for c in current_captures {
            if let Some(pid) = pid_from_dir(&c.dir) {
                if !entry.contains(&pid) {
                    entry.push(pid);
                }
            }
        }
    }

    let late_lines = scan_priors(&scope, &input.tool_use_id, &mut ledger);

    write_ledger_atomic(&ledger_path, &ledger)?;
    // _flock dropped here → LOCK_UN.
    Ok(late_lines)
}

fn read_ledger(path: &Path) -> Ledger {
    match fs::read_to_string(path) {
        // Fail-open on parse error: a corrupted ledger means at worst one
        // duplicate emission, never a missed one.
        Ok(s) => serde_json::from_str(&s).unwrap_or_default(),
        Err(_) => Ledger::new(),
    }
}

fn write_ledger_atomic(path: &Path, ledger: &Ledger) -> Result<()> {
    let parent = path.parent().context("ledger path has no parent")?;
    fs::create_dir_all(parent).ok();
    let tmp = path.with_extension("json.tmp");
    let body = serde_json::to_vec_pretty(ledger)?;
    fs::write(&tmp, body).with_context(|| format!("write tmp {}", tmp.display()))?;
    fs::rename(&tmp, path)
        .with_context(|| format!("rename {} -> {}", tmp.display(), path.display()))?;
    Ok(())
}

/// Walk scope_dir for prior tool_use_id dirs (those with an events.jsonl
/// directly inside, distinguishing them from agent-id subdirs in main-thread
/// scope) and emit one line per prior toolu_id that has new finalized
/// children. Mutates `ledger` to record what was emitted.
fn scan_priors(scope: &Path, current_toolu_id: &str, ledger: &mut Ledger) -> Vec<String> {
    let rd = match fs::read_dir(scope) {
        Ok(r) => r,
        Err(_) => return Vec::new(),
    };
    let mut toolu_dirs: Vec<PathBuf> = rd
        .flatten()
        .map(|e| e.path())
        .filter(|p| p.is_dir())
        // Only directories with their own events.jsonl are wrap-parent dirs.
        // This filters out subagent dirs (which contain toolu subdirs but no
        // events.jsonl of their own) when scanning main-thread scope.
        .filter(|p| p.join("events.jsonl").is_file())
        .collect();
    toolu_dirs.sort();

    let now = Utc::now();
    let mut out_lines: Vec<String> = Vec::new();

    for toolu_dir in toolu_dirs {
        let toolu_id = match toolu_dir.file_name().and_then(|s| s.to_str()) {
            Some(s) => s.to_string(),
            None => continue,
        };
        if toolu_id == current_toolu_id {
            continue;
        }

        let surfaced: HashSet<i64> = ledger
            .get(&toolu_id)
            .map(|v| v.iter().copied().collect())
            .unwrap_or_default();

        let events = match events::read_all(&toolu_dir) {
            Ok(e) => e,
            Err(_) => continue,
        };

        let mut started: HashMap<i64, (chrono::DateTime<Utc>, Option<String>)> = HashMap::new();
        let mut exited: HashSet<i64> = HashSet::new();
        for ev in &events {
            match ev.kind.as_str() {
                "child_started" => {
                    if let Some(pid) = ev.data.get("child_pid").and_then(|v| v.as_i64()) {
                        let desc = ev
                            .data
                            .get("desc")
                            .and_then(|v| v.as_str())
                            .map(|s| s.to_string());
                        started.insert(pid, (ev.ts, desc));
                    }
                }
                "child_exit" => {
                    if let Some(pid) = ev.data.get("child_pid").and_then(|v| v.as_i64()) {
                        exited.insert(pid);
                    }
                }
                _ => {}
            }
        }

        let mut emit: Vec<(i64, String, PathBuf, bool)> = Vec::new();
        for (pid, (ts, desc_opt)) in &started {
            if surfaced.contains(pid) {
                continue;
            }
            let finalized = exited.contains(pid);
            let stale = (now - *ts).num_seconds() >= UNFINALIZED_STALE_SECS;
            if !finalized && !stale {
                // In-flight and not yet stale: defer to a later hook fire.
                continue;
            }
            let child_dir = toolu_dir.join(pid.to_string());
            // Prefer meta.json's desc (richer / canonical) over the events line.
            let desc = desc_opt.clone().or_else(|| {
                fs::read_to_string(child_dir.join("meta.json"))
                    .ok()
                    .and_then(|s| serde_json::from_str::<ChildMeta>(&s).ok())
                    .and_then(|c| c.desc)
            });
            let label = desc.unwrap_or_else(|| "(no desc)".to_string());
            // If events.jsonl says unfinalized but meta.json was never updated
            // (SIGKILL before final write), force the unfinalized marker inside
            // the details bracket.
            emit.push((*pid, label, child_dir, !finalized));
        }

        if emit.is_empty() {
            continue;
        }
        emit.sort_by_key(|(pid, _, _, _)| *pid);
        let listing: Vec<String> = emit
            .iter()
            .map(|(_, label, dir, unfinalized)| {
                let details = format_details(dir, *unfinalized);
                format!("{label}{details} → {}/{{stdout,stderr}}", dir.display())
            })
            .collect();
        out_lines.push(format!(
            "{LATE_CAPTURES_HEADER_PREFIX}{toolu_id}: {}",
            listing.join("; "),
        ));
        let entry = ledger.entry(toolu_id.clone()).or_default();
        for (pid, _, _, _) in &emit {
            if !entry.contains(pid) {
                entry.push(*pid);
            }
        }
    }

    out_lines
}
