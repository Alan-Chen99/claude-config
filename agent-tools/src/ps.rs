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
use crate::statusline;

/// `--format`'s value set, as a `clap::ValueEnum` rather than a bare
/// `String`: the set was spelled three times over — the help text, the
/// dispatch match, and a hand-written rejection message — and only two of
/// those three could ever be checked against each other. `ValueEnum` makes
/// an unrecognized value clap's rejection to issue, the dispatch match
/// exhaustive under the compiler, and the third format the next spelling
/// arrives at needs one variant added, not a fallback arm's text edited to
/// still be true.
#[derive(Debug, Clone, Copy, PartialEq, Eq, clap::ValueEnum)]
pub enum PsFormat {
    Json,
    Text,
    Statusline,
}

pub fn run(
    task_filter: Option<String>,
    session_override: Option<String>,
    format: PsFormat,
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
    // still acting on. This is the grouped ranking the text layout needs —
    // `render_json`'s flat arrays rank themselves again below, since a
    // group's newest member is routinely not the member either array holds.
    sort_newest_group_first(&mut captures, |c| c);

    let now = Utc::now();
    match format {
        PsFormat::Json => render_json(&session_id, &captures, all, now),
        PsFormat::Text => render_text(&session_id, &captures, all, events, now),
        PsFormat::Statusline => render_statusline(&captures, now),
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

/// Newest first, by group: an (agent, tool-use) group ranks by its own
/// newest member's start, and its captures follow in the same direction —
/// otherwise a group's newest capture could sit under a group buried below
/// older ones. Takes a projection instead of committing to `&mut [Capture]`
/// so `run` can rank everything it collected and `render_text` can rank
/// again over only what its `--all` filter kept — the latter over
/// `(&Capture, Status)` pairs, without either caller reshaping its data to
/// match the other's element type.
fn sort_newest_group_first<T>(items: &mut [T], capture_of: impl Fn(&T) -> &Capture) {
    let started = |c: &Capture| c.meta.as_ref().map(|m| m.started_at);
    let mut group_newest: HashMap<(Option<String>, String), Option<DateTime<Utc>>> = HashMap::new();
    for item in items.iter() {
        let c = capture_of(item);
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
    items.sort_by(|x, y| {
        let a = capture_of(x);
        let b = capture_of(y);
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
    // `captures` arrives ranked by group, the key the grouped text layout
    // needs and the wrong one here: `live` and `settled` are flat, and a
    // group's rank can be set by a sibling neither array carries — under
    // `--background`, routinely a settled one sitting next to a live one in
    // the same tool-use. Rank each record by its own start instead; stable,
    // so a tie keeps the group order above, and a capture with no readable
    // meta (`started_at: None`) sorts last rather than first.
    let newest_first = |a: &Record, b: &Record| b.started_at.cmp(&a.started_at);
    live.sort_by(newest_first);
    settled.sort_by(newest_first);
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

/// `ps --format statusline`. One line for the Claude Code status bar, or
/// nothing at all when no capture is live — see `statusline::render`. `--all`
/// and `--events` do not apply: the bar exists to show what is running, and a
/// settled child or an event log answers a different question than that one.
fn render_statusline(captures: &[Capture], now: DateTime<Utc>) -> Result<()> {
    // Zero bytes when nothing is live, not a bare newline: a caller checking
    // for empty output must see none. A real line does get its newline —
    // `print!` alone leaves the terminal's next prompt mid-line, and a
    // pipeline reading line-by-line (`| while read`) drops an unterminated
    // last line entirely.
    let line = statusline::render(captures, now);
    if !line.is_empty() {
        println!("{line}");
    }
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

    // One `Status` derivation per capture, at the one `now` this render
    // shares, kept for both the filter decision below and the printed line
    // further down: a second derivation at a later instant reads whatever
    // the filesystem holds at that later moment, which for a capture near
    // the live/terminal boundary need not be what the filter just saw — an
    // `exited(0)` kept as live could print as `final(0)` moments later, on
    // the same line the filter approved as non-terminal.
    let mut withheld = Withheld::default();
    let mut visible: Vec<(&Capture, crate::status::Status)> = Vec::new();
    for c in captures {
        let st = crate::status::derive(&c.capture_dir, now);
        if all || !st.is_terminal() {
            visible.push((c, st));
        } else {
            withheld.add(&st.key.to_string());
        }
    }

    // `captures` arrived ranked over everything collected; a group's rank
    // there can be set by a capture the filter above just withheld. Ranking
    // again, over only what will be shown, is what keeps a hidden sibling
    // from setting a visible group's place in the listing.
    sort_newest_group_first(&mut visible, |(c, _)| *c);

    // Group captures by (agent_id, tool_use_id) for display.
    let mut current_agent: Option<Option<String>> = None;
    let mut current_tuid: Option<String> = None;

    // Precompute group sizes keyed by (agent_id, tool_use_id), over the
    // captures that survived the filter above — sizing a header off the full
    // set would announce a group of four and then show one of them.
    let mut group_sizes: Vec<((Option<String>, String), usize)> = Vec::new();
    for (c, _) in &visible {
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

    for (c, st) in &visible {
        if current_agent.as_ref() != Some(&c.agent_id) {
            current_agent = Some(c.agent_id.clone());
            current_tuid = None;
            let agent_label = c.agent_id.clone().unwrap_or_else(|| "_main".into());
            writeln!(buf, "agent: {agent_label}")?;
        }
        if current_tuid.as_ref() != Some(&c.tool_use_id) {
            current_tuid = Some(c.tool_use_id.clone());
            // `group_sizes` holds exactly one entry per group boundary this
            // same walk of `visible` crosses, in the order it crosses them —
            // a `None` here means the two walks disagree about what
            // `visible` holds, which a fallback would paper over with a
            // plausible wrong count rather than surface.
            let n = group_iter.next().map(|(_, n)| *n).expect(
                "group_sizes has one entry per group boundary crossed in this walk of `visible`",
            );
            let plural = if n == 1 { "capture" } else { "captures" };
            writeln!(buf, "  tool-use {} ({} {})", c.tool_use_id, n, plural)?;
        }
        write_capture(&mut buf, c, st, now)?;
    }

    // By key, on the same terms JSON withholds a capture: a bare total would
    // hide a `spawn-failed` sitting among a hundred clean exits exactly as a
    // bare count would in the JSON envelope, and reusing `Withheld` is what
    // keeps the two surfaces from bucketing it differently.
    if !withheld.by_key.is_empty() {
        let total: usize = withheld.by_key.values().sum();
        let by_key = withheld
            .by_key
            .iter()
            .map(|(k, n)| format!("{}: {n}", meta::escape_control(k)))
            .collect::<Vec<_>>()
            .join(", ");
        writeln!(
            buf,
            "{total} settled capture{} withheld -> agent-tools ps --all ({by_key})",
            if total == 1 { "" } else { "s" }
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
/// Takes an already-derived `Status` rather than deriving its own: the caller
/// has just used that same derivation to decide whether this capture is shown
/// at all, and a fresh derivation here, at a later instant, could disagree
/// with the one the caller already acted on.
fn write_capture(
    buf: &mut String,
    c: &Capture,
    st: &crate::status::Status,
    now: DateTime<Utc>,
) -> Result<()> {
    writeln!(
        buf,
        "    {}",
        crate::status::render(&c.capture_dir, st, now)
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
