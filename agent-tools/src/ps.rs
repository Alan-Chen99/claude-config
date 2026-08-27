use anyhow::{Context, Result};
use chrono::Utc;
use std::fmt::Write as _;
use std::fs;
use std::path::{Path, PathBuf};

use crate::events::{self, Event};
use crate::meta::{self, ChildMeta};
use crate::paths;

/// One captured `agent-tools run` invocation on disk.
struct Capture {
    agent_id: Option<String>,
    tool_use_id: String,
    /// Directory holding this capture: `stdout` and `stderr` when the streams were
    /// split, `output` when they were merged, plus `meta.json` either way.
    /// Layout: `<tool_use_id_dir>/<pid>/`.
    capture_dir: PathBuf,
    /// `None` when `meta.json` is absent or will not parse. The capture still
    /// exists and `status::derive` still has an answer for it — `abandoned` —
    /// so dropping it here would leave `ps` disagreeing with the report about
    /// whether the child exists at all.
    meta: Option<ChildMeta>,
}

pub fn run(task_filter: Option<String>, session_override: Option<String>) -> Result<()> {
    let session_id = match session_override {
        Some(s) => s,
        None => {
            let parent_dir = paths::parent_dir_from_env().context(
                "AGENT_TOOLS_PARENT_DIR is not set; pass --session-id when invoking ps \
                 outside a Claude Code Bash tool",
            )?;
            let (sid, _, _) = paths::parse_parent_dir(&parent_dir)?;
            sid
        }
    };

    let session_dir = paths::state_root()?.join(&session_id);
    if !session_dir.is_dir() {
        println!("session: {session_id}");
        println!("(no state on disk)");
        return Ok(());
    }

    let mut captures: Vec<Capture> = Vec::new();
    collect_captures(&session_dir, &mut captures)?;

    if let Some(ref t) = task_filter {
        captures.retain(|c| &c.tool_use_id == t);
    }

    // Stable ordering: agent (None first), then tool_use_id, then start time, then pid.
    captures.sort_by(|a, b| {
        a.agent_id
            .cmp(&b.agent_id)
            .then_with(|| a.tool_use_id.cmp(&b.tool_use_id))
            .then_with(|| {
                a.meta
                    .as_ref()
                    .map(|m| m.started_at)
                    .cmp(&b.meta.as_ref().map(|m| m.started_at))
            })
            // A capture with no meta has no start time to sort by; its
            // directory is the wrapper pid, which is stable and unique.
            .then_with(|| a.capture_dir.cmp(&b.capture_dir))
    });

    let mut buf = String::new();
    writeln!(buf, "session: {session_id}")?;

    if captures.is_empty() {
        writeln!(buf, "(no state on disk)")?;
        print!("{buf}");
        return Ok(());
    }

    // Group captures by (agent_id, tool_use_id) for display.
    let mut current_agent: Option<Option<String>> = None;
    let mut current_tuid: Option<String> = None;

    // Precompute group sizes keyed by (agent_id, tool_use_id).
    let mut group_sizes: Vec<((Option<String>, String), usize)> = Vec::new();
    for c in &captures {
        let key = (c.agent_id.clone(), c.tool_use_id.clone());
        if let Some(last) = group_sizes.last_mut() {
            if last.0 == key {
                last.1 += 1;
                continue;
            }
        }
        group_sizes.push((key, 1));
    }
    let mut group_iter = group_sizes.iter();

    for c in &captures {
        if current_agent.as_ref() != Some(&c.agent_id) {
            current_agent = Some(c.agent_id.clone());
            current_tuid = None;
            let agent_label = c.agent_id.clone().unwrap_or_else(|| "_main".into());
            writeln!(buf, "agent: {agent_label}")?;
        }
        if current_tuid.as_ref() != Some(&c.tool_use_id) {
            current_tuid = Some(c.tool_use_id.clone());
            let n = group_iter.next().map(|(_, n)| *n).unwrap_or(1);
            let plural = if n == 1 { "capture" } else { "captures" };
            writeln!(buf, "  tool-use {} ({} {})", c.tool_use_id, n, plural)?;
        }
        write_capture(&mut buf, c)?;
    }

    // Chronological merge of events.jsonl across all surviving captures'
    // tool_use_id dirs. Each tool_use_id dir owns a single events.jsonl.
    let mut seen_tuid_dirs: Vec<PathBuf> = Vec::new();
    let mut all_events: Vec<(String, Event)> = Vec::new();
    let mut unreadable_lines = 0usize;
    let mut event_errors: Vec<String> = Vec::new();
    for c in &captures {
        let tuid_dir = c
            .capture_dir
            .parent()
            .map(|p| p.to_path_buf())
            .unwrap_or_else(|| c.capture_dir.clone());
        if seen_tuid_dirs.contains(&tuid_dir) {
            continue;
        }
        seen_tuid_dirs.push(tuid_dir.clone());
        // A line that will not parse costs that line, and the count is stated
        // below: silence about a dropped record reads as "nothing was written".
        match events::read_all(&tuid_dir) {
            Ok(log) => {
                unreadable_lines += log.unreadable;
                for e in log.events {
                    all_events.push((c.tool_use_id.clone(), e));
                }
            }
            Err(e) => event_errors.push(format!("{}: {e}", c.tool_use_id)),
        }
    }
    all_events.sort_by_key(|(_, e)| e.ts);
    if !all_events.is_empty() || unreadable_lines > 0 || !event_errors.is_empty() {
        writeln!(buf, "\nevents (chronological, all captures):")?;
        for (tid, e) in &all_events {
            writeln!(
                buf,
                "  {}  {:<14} {:<20} {}",
                e.ts.format("%H:%M:%S%.3f"),
                e.kind,
                tid,
                e.data
            )?;
        }
        if unreadable_lines > 0 {
            writeln!(
                buf,
                "  note: {unreadable_lines} unreadable event line{} skipped",
                if unreadable_lines == 1 { "" } else { "s" }
            )?;
        }
        for err in &event_errors {
            writeln!(buf, "  note: events unreadable for {err}")?;
        }
    }

    print!("{buf}");
    Ok(())
}

/// Walk `<session>/[<subagent>/]<tool_use_id>/<pid>/` and accumulate captures.
///
/// Discrimination between subagent vs tool_use_id at the second level:
/// a tool_use_id dir contains pid-named subdirs (numeric, parseable as `u32`);
/// a subagent dir contains tool_use_id-named subdirs (non-numeric). See
/// `dir_holds_pid_children`.
fn collect_captures(session_dir: &Path, out: &mut Vec<Capture>) -> Result<()> {
    let rd = match fs::read_dir(session_dir) {
        Ok(r) => r,
        Err(_) => return Ok(()),
    };
    for entry in rd.flatten() {
        let path = entry.path();
        if !path.is_dir() {
            continue;
        }
        let name = match path.file_name().and_then(|n| n.to_str()) {
            Some(n) => n.to_string(),
            None => continue,
        };
        if dir_holds_pid_children(&path) {
            // <session>/<tool_use_id>/<pid>/ — main-thread captures.
            collect_pid_captures(&path, None, &name, out);
        } else {
            // <session>/<subagent>/<tool_use_id>/<pid>/ — subagent captures.
            let agent_id = name;
            let inner = match fs::read_dir(&path) {
                Ok(r) => r,
                Err(_) => continue,
            };
            for ie in inner.flatten() {
                let tuid_path = ie.path();
                if !tuid_path.is_dir() {
                    continue;
                }
                let tuid_name = match tuid_path.file_name().and_then(|n| n.to_str()) {
                    Some(n) => n.to_string(),
                    None => continue,
                };
                if !dir_holds_pid_children(&tuid_path) {
                    continue;
                }
                collect_pid_captures(&tuid_path, Some(agent_id.clone()), &tuid_name, out);
            }
        }
    }
    Ok(())
}

/// Discriminator: returns true iff `dir` has at least one subdirectory whose
/// name parses as `u32` (pid). Empty dirs return false (treated as a subagent
/// placeholder — they contribute nothing either way).
fn dir_holds_pid_children(dir: &Path) -> bool {
    let rd = match fs::read_dir(dir) {
        Ok(r) => r,
        Err(_) => return false,
    };
    for entry in rd.flatten() {
        let p = entry.path();
        if !p.is_dir() {
            continue;
        }
        if let Some(n) = p.file_name().and_then(|n| n.to_str()) {
            if n.parse::<u32>().is_ok() {
                return true;
            }
        }
    }
    false
}

fn collect_pid_captures(
    tuid_dir: &Path,
    agent_id: Option<String>,
    tool_use_id: &str,
    out: &mut Vec<Capture>,
) {
    let rd = match fs::read_dir(tuid_dir) {
        Ok(r) => r,
        Err(_) => return,
    };
    for entry in rd.flatten() {
        let p = entry.path();
        if !p.is_dir() {
            continue;
        }
        let is_pid = p
            .file_name()
            .and_then(|n| n.to_str())
            .map(|n| n.parse::<u32>().is_ok())
            .unwrap_or(false);
        if !is_pid {
            continue;
        }
        out.push(Capture {
            agent_id: agent_id.clone(),
            tool_use_id: tool_use_id.to_string(),
            meta: meta::read_meta(&p).ok(),
            capture_dir: p,
        });
    }
}

/// Longest command `ps` renders on one line. A wrapped heredoc script reaches
/// six figures, and `ps` is read through a tool result that truncates, so one
/// child's source would displace every other child's status. The cap is far
/// above any command an agent types, and the full text stays in `meta.json`
/// beside the capture, whose path is on the same line.
const CMD_MAX: usize = 2000;

/// One capture block: the derived status line, then the facts a pushed report
/// leaves out — the command, the wrapper pid, and the start time. `ps` has no
/// budget over the set of children, so it carries fields a report cannot; the
/// command is still capped per line, for the reason `CMD_MAX` gives.
///
/// Status is derived here rather than read from `c.meta`: the meta on disk is
/// facts only, and liveness is the wrapper's, never the child pid's — a live
/// wrapper that has not recorded a reap means the child is alive by definition.
fn write_capture(buf: &mut String, c: &Capture) -> Result<()> {
    let now = Utc::now();
    let st = crate::status::derive(&c.capture_dir, now);
    writeln!(
        buf,
        "    {}",
        crate::status::render(&c.capture_dir, &st, now)
    )?;
    if let Some(m) = &st.meta {
        writeln!(
            buf,
            "      cmd:     {}",
            crate::status::cap_to(&crate::meta::escape_control(&m.command.join(" ")), CMD_MAX)
        )?;
        writeln!(buf, "      wrapper: pid {}", m.wrapper_pid)?;
        writeln!(
            buf,
            "      started: {}",
            m.started_at.format("%H:%M:%S%.3f")
        )?;
    }
    Ok(())
}
