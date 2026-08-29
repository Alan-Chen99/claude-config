use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use std::collections::HashMap;
use std::fmt::Write as _;
use std::fs;
use std::path::{Path, PathBuf};

use crate::events::{self, Event};
use crate::meta;
use crate::paths;
use crate::psrecord::{Capture, Envelope, Record, Withheld};

pub fn run(
    task_filter: Option<String>,
    session_override: Option<String>,
    format: &str,
    all: bool,
    events: bool,
) -> Result<()> {
    let session_id = resolve_session(session_override)?;
    let session_dir = paths::state_root()?.join(&session_id);

    let mut captures: Vec<Capture> = Vec::new();
    collect_captures(&session_dir, &mut captures)?;

    if let Some(ref t) = task_filter {
        captures.retain(|c| &c.tool_use_id == t);
    }

    // Newest first, because `ps` is read after a compaction through a tool
    // result that truncates: what started most recently is what the agent is
    // still acting on. Display groups by tool-use, so a group sorts by its own
    // newest capture and its captures follow in the same direction — otherwise
    // the newest capture could sit under a group buried below older ones.
    let started = |c: &Capture| c.meta.as_ref().map(|m| m.started_at);
    let mut group_newest: HashMap<(Option<String>, String), Option<DateTime<Utc>>> = HashMap::new();
    for c in &captures {
        let key = (c.agent_id.clone(), c.tool_use_id.clone());
        let newest = group_newest.entry(key).or_default();
        if started(c) > *newest {
            *newest = started(c);
        }
    }
    let newest_of = |c: &Capture| {
        group_newest
            .get(&(c.agent_id.clone(), c.tool_use_id.clone()))
            .copied()
            .flatten()
    };
    captures.sort_by(|a, b| {
        a.agent_id
            .cmp(&b.agent_id)
            .then_with(|| newest_of(b).cmp(&newest_of(a)))
            // Two groups can share a newest time only if seeded that way; the
            // identifier keeps their captures contiguous.
            .then_with(|| a.tool_use_id.cmp(&b.tool_use_id))
            .then_with(|| started(b).cmp(&started(a)))
            // A capture with no meta has no start time to sort by; its
            // directory is the wrapper pid, which is stable and unique.
            .then_with(|| a.capture_dir.cmp(&b.capture_dir))
    });

    let now = Utc::now();
    match format {
        "json" => render_json(&session_id, &captures, all, now),
        "text" => render_text(&session_id, &captures, all, events, now),
        other => anyhow::bail!("unknown --format {other}; expected json or text"),
    }
}

/// The session `ps` reports on, in priority order: an explicit
/// `--session-id`; otherwise the scope a hook already set for this Bash call
/// (`AGENT_TOOLS_PARENT_DIR`); otherwise the id every Claude Code shell
/// carries in its own environment, which is what lets `! agent-tools ps`
/// answer even where no hook ran to set a scope.
fn resolve_session(session_override: Option<String>) -> Result<String> {
    if let Some(s) = session_override {
        return Ok(s);
    }
    if let Ok(parent_dir) = paths::parent_dir_from_env() {
        let (sid, _, _) = paths::parse_parent_dir(&parent_dir)?;
        return Ok(sid);
    }
    std::env::var("CLAUDE_CODE_SESSION_ID").context(
        "no session: pass --session-id, or run where AGENT_TOOLS_PARENT_DIR or \
         CLAUDE_CODE_SESSION_ID is set",
    )
}

/// `ps --format json` (the default): one `psrecord::Record` per capture,
/// sorted into `live` or (under `--all`) `settled` — never both, since a
/// consumer selects a settled child by which array carries it, not by a field
/// on the record.
fn render_json(
    session_id: &str,
    captures: &[Capture],
    all: bool,
    now: DateTime<Utc>,
) -> Result<()> {
    let mut live = Vec::new();
    let mut settled = Vec::new();
    let mut withheld = Withheld::default();
    for c in captures {
        let r = Record::build(&c.capture_dir, c.agent_id.clone(), &c.tool_use_id, now);
        match (r.terminal, all) {
            (false, _) => live.push(r),
            // Asked for, so shown in full — its own array, because `live`
            // means live.
            (true, true) => settled.push(r),
            // Not asked for, so counted rather than dropped: a spawn failure
            // among a hundred clean exits must stay visible even withheld.
            (true, false) => withheld.add(&r.key),
        }
    }
    let envelope = Envelope {
        now: now.with_timezone(&chrono::Local),
        session: session_id.to_string(),
        live,
        settled: all.then_some(settled),
        withheld,
    };
    println!("{}", serde_json::to_string_pretty(&envelope)?);
    Ok(())
}

/// `ps --format text`. A settled capture is skipped unless `--all`, and the
/// event log is skipped unless `--events`: what is running is the question a
/// reader brings to this command, and an unfiltered dump answers a
/// different one.
fn render_text(
    session_id: &str,
    captures: &[Capture],
    all: bool,
    events: bool,
    now: DateTime<Utc>,
) -> Result<()> {
    let mut buf = String::new();
    writeln!(buf, "session: {session_id}")?;

    if captures.is_empty() {
        writeln!(buf, "(no state on disk)")?;
        print!("{buf}");
        return Ok(());
    }

    // A settled capture is skipped here on the same terms JSON withholds it —
    // a silent skip reads as "there were none", so the count survives the
    // filter and is stated once the groups below are drawn.
    let mut withheld = 0usize;
    let visible: Vec<&Capture> = captures
        .iter()
        .filter(|c| {
            let keep = all || !crate::status::derive(&c.capture_dir, now).is_terminal();
            if !keep {
                withheld += 1;
            }
            keep
        })
        .collect();

    // Group captures by (agent_id, tool_use_id) for display.
    let mut current_agent: Option<Option<String>> = None;
    let mut current_tuid: Option<String> = None;

    // Precompute group sizes keyed by (agent_id, tool_use_id), over the
    // captures that survived the filter above — sizing a header off the full
    // set would announce a group of four and then show one of them.
    let mut group_sizes: Vec<((Option<String>, String), usize)> = Vec::new();
    for c in &visible {
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

    for c in &visible {
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

    if withheld > 0 {
        writeln!(
            buf,
            "{withheld} settled capture{} withheld -> agent-tools ps --all",
            if withheld == 1 { "" } else { "s" }
        )?;
    }

    // Chronological merge of events.jsonl across every collected capture's
    // tool_use_id dir — regardless of `--all`, since the log answers a
    // different question than which capture's status is shown above. Each
    // tool_use_id dir owns a single events.jsonl.
    if events {
        let mut seen_tuid_dirs: Vec<PathBuf> = Vec::new();
        let mut all_events: Vec<(String, Event)> = Vec::new();
        let mut unreadable_lines = 0usize;
        let mut event_errors: Vec<String> = Vec::new();
        for c in captures {
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
            crate::status::fmt_local_hms(m.started_at)
        )?;
    }
    Ok(())
}
