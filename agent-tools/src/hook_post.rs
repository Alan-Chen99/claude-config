use anyhow::{Context, Result};
use std::fs;
use std::io::{Read, Write};
use std::path::PathBuf;

use crate::hook_input;
use crate::paths;

/// Ceiling on the report body. `additionalContext` is capped at 10,000
/// characters and the runtime silently replaces anything longer with a
/// ~2,000-character stub — which the agent would read as "nothing else
/// changed". The margin below the cap leaves room for the reset note and the
/// BACKGROUNDED notice sharing the same field.
const REPORT_BUDGET: usize = 9_000;

/// The one place a report header is built. Both delivery points use it, so the
/// prompt's quoted form matches what either emits rather than one of them.
///
/// `at` is the instant the report's lines were measured against, not the
/// instant the header is built: the stamp is what a re-read report resolves
/// `last byte 4s ago` against, and a second clock read here would put the
/// anchor however long the scan took after the figures it anchors.
pub(crate) fn report_header(at: chrono::DateTime<chrono::Utc>) -> String {
    format!(
        // PROMPT-COUPLED
        "[agent-tools] run status @ {}:",
        crate::status::fmt_local_stamp(at)
    )
}

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

    let mut parts: Vec<String> = Vec::new();

    // Only Bash and Monitor can be backgrounded. Every other tool reaches this
    // hook purely as a delivery point for status changes.
    if input.tool_name == "Bash" || input.tool_name == "Monitor" {
        if let Some(b) = bg_notice(&input) {
            parts.push(b);
        }
    }

    // The backgrounding notice is independent of status reporting and is the one
    // message this hook must not lose. A `?` here would discard an
    // already-computed notice because something unrelated failed.
    let mut delivered: Option<Report> = None;
    match report_changes(&input.session_id, input.agent_id.as_deref()) {
        Ok(report) if !report.lines.is_empty() => {
            parts.push(format!(
                "{}\n{}",
                report_header(report.at),
                report.lines.join("\n")
            ));
            delivered = Some(report);
        }
        Ok(_) => {}
        Err(e) => {
            eprintln!("agent-tools hook-post: status report failed: {e:#}");
            parts.push(format!(
                // PROMPT-COUPLED
                "[agent-tools] run status: unavailable this time ({e}); \
                 run `agent-tools ps` for the current state"
            ));
        }
    }

    if parts.is_empty() {
        return Ok(());
    }

    // PostToolUse does not fire when a tool result is an error — the failure
    // path dispatches PostToolUseFailure — so the same binary answers both and
    // the response must name the event it is answering.
    let event = input.hook_event_name.as_deref().unwrap_or("PostToolUse");
    let out = serde_json::json!({
        "hookSpecificOutput": {
            "hookEventName": event,
            // Newline, not space: the prompt teaches the agent to recognize a
            // line beginning `[agent-tools]` or `BACKGROUNDED:`, and a joined
            // pair leaves the second header mid-line where that rule cannot
            // reach it.
            "additionalContext": parts.join("\n")
        }
    });
    // Write, flush, and only then record what was delivered: a key recorded
    // before the write reaches the agent retires a change nobody saw.
    // `println!` is unusable here because it panics on a write error rather
    // than returning one.
    let mut stdout = std::io::stdout().lock();
    writeln!(stdout, "{}", serde_json::to_string(&out)?).context("write hook output")?;
    stdout.flush().context("flush hook output")?;
    if let Some(report) = delivered {
        report.commit()?;
    }
    Ok(())
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
    // PROMPT-COUPLED
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

/// The lines to deliver, and the ledger that has recorded them as delivered.
///
/// The ledger is uncommitted: a key must be written down only
/// after the report reaches the agent. Committing first means a failed write
/// retires a change nobody was shown, and its key matches at every later
/// delivery point, so it is never reported again. Committing after costs at
/// worst a duplicate report, which the design already accepts.
pub(crate) struct Report {
    pub(crate) lines: Vec<String>,
    /// The instant every relative figure in `lines` was derived against. The
    /// header stamps this, so `last byte 4s ago` and the stamp above it name
    /// one moment.
    pub(crate) at: chrono::DateTime<chrono::Utc>,
    ledger: Option<crate::ledger::Ledger>,
}

impl Report {
    /// Persist the delivered keys. Call only after the write succeeded.
    pub(crate) fn commit(self) -> Result<()> {
        match self.ledger {
            Some(mut l) => l.commit(),
            None => Ok(()),
        }
    }
}

/// Scan every capture dir in this agent's scope, derive each status, and
/// return one line per child whose key changed since it was last reported,
/// together with the ledger holding those keys for the caller to commit.
pub(crate) fn report_changes(session_id: &str, agent_id: Option<&str>) -> Result<Report> {
    let scope = scope_dir(session_id, agent_id)?;
    let now = chrono::Utc::now();
    if !scope.is_dir() {
        return Ok(Report {
            lines: Vec::new(),
            at: now,
            ledger: None,
        });
    }
    let mut ledger = crate::ledger::Ledger::open(&scope)?;
    // (id, key, rendered line, name, still running) — name and the running
    // flag both travel with the other fields rather than being recovered
    // later from the string `key` or the rendered `line`: see
    // `collapse_running` and `StatusKey::is_still_running`.
    let mut pending: Vec<(String, String, String, String, bool)> = Vec::new();
    let mut notes: Vec<String> = Vec::new();

    for tuid_entry in fs::read_dir(&scope)?.flatten() {
        let tuid_dir = tuid_entry.path();
        if !tuid_dir.is_dir() {
            continue;
        }
        let Some(tuid) = tuid_dir.file_name().and_then(|n| n.to_str()) else {
            continue;
        };
        let Ok(cap_entries) = fs::read_dir(&tuid_dir) else {
            // The surrounding scan skips what it cannot use; aborting the whole
            // report over one directory would hide every other child's change.
            notes.push(format!(
                "  note: {} could not be listed; its captures are missing from this report",
                tuid_dir.display()
            ));
            continue;
        };
        for cap_entry in cap_entries.flatten() {
            let cap_dir = cap_entry.path();
            let Some(name) = cap_dir.file_name().and_then(|n| n.to_str()) else {
                continue;
            };
            // A capture dir is named for the wrapper pid. Anything else under a
            // tool_use_id dir — and every dir under a subagent's dir, which is
            // named for a tool_use_id — is not this scope's to report.
            if !cap_dir.is_dir() || name.parse::<u32>().is_err() {
                continue;
            }
            let st = crate::status::derive(&cap_dir, now);
            let id = format!("{tuid}/{name}");
            let key = st.key.to_string();
            if ledger.changed(&id, &key) {
                pending.push((
                    id,
                    key,
                    format!("  {}", crate::status::render(&cap_dir, &st, now)),
                    crate::status::name(&cap_dir, &st),
                    st.key.is_still_running(),
                ));
            }
        }
    }
    // Identity order, so the report is reproducible rather than in whatever
    // order `read_dir` happened to yield — which would also make the dropped
    // set arbitrary. Terminal-first is no longer this sort's job; see the
    // partition below.
    pending.sort_by(|a, b| a.0.cmp(&b.0));
    // A hard split, not a sort: a still-running child can never edge out a
    // settled one for budget by sorting earlier. "This finished" matters more
    // to an agent than "this is still running", so settled children —
    // including `exited`, whose fate is not yet terminal but whose exit code
    // is worth a full line — always get first claim on the budget.
    let (running, terminal): (Vec<_>, Vec<_>) = pending
        .into_iter()
        .partition(|(_, _, _, _, still_running)| *still_running);
    let mut lines = bound(
        &mut ledger,
        terminal
            .into_iter()
            .map(|(id, key, line, _, _)| (id, key, line))
            .collect(),
    );
    // `collapse_running` gets only what `bound` left of the budget, not the
    // module ceiling again: checking its one line against the whole of
    // `REPORT_BUDGET` a second time would let the two sums together exceed
    // it, and a report over `REPORT_BUDGET` is replaced whole by the
    // runtime's stub — which reads to the agent as nothing else changed.
    let used: usize = lines.iter().map(|l| l.len() + 1).sum();
    let running: Vec<(String, String, String, String)> = running
        .into_iter()
        .map(|(id, key, line, name, _)| (id, key, line, name))
        .collect();
    match collapse_running(&mut ledger, running, REPORT_BUDGET.saturating_sub(used)) {
        Collapsed::None => {}
        Collapsed::Line(line) => lines.push(line),
        // Distinct from `Collapsed::None`, for the reason `bound`'s own
        // "omitted for size" note exists: a silently dropped change is
        // indistinguishable from no change at all, which is the exact failure
        // `REPORT_BUDGET` exists to prevent. The note itself spends budget
        // too, and is checked against what `bound` left rather than pushed
        // unconditionally — a `Dropped` this close to a full budget is rare,
        // but the announcement replacing the very silence it exists to avoid
        // would not be. In that corner nothing is recorded either way, so
        // these children are simply retried at the next delivery point.
        Collapsed::Dropped(n) => {
            let note = format!(
                "  ... {n} still-running children changed, omitted for size; they are \
                 reported at the next delivery point, or run `agent-tools ps` now"
            );
            if used + note.len() < REPORT_BUDGET {
                lines.push(note);
            }
        }
    }
    // A reset ledger makes every child look new. Say why, or the agent sees a
    // burst of repeats with no explanation.
    if let Some(reason) = ledger.reset_reason.clone() {
        notes.insert(
            0,
            format!(
                "  note: report history lost — {reason}; each child below is reported again once"
            ),
        );
    }
    for note in notes.into_iter().rev() {
        lines.insert(0, note);
    }
    Ok(Report {
        lines,
        at: now,
        ledger: Some(ledger),
    })
}

/// Keep the report lines that fit under the additionalContext cap, and record in
/// the ledger only the ones actually kept.
///
/// Recording a line the agent never saw would retire that child's change
/// permanently: its key would match next time and never be reported again. A
/// dropped line stays pending instead, and lands at the next delivery point.
/// The count of dropped lines is stated, because a silently truncated report is
/// indistinguishable from a report of no change.
fn bound(
    ledger: &mut crate::ledger::Ledger,
    pending: Vec<(String, String, String)>,
) -> Vec<String> {
    let mut used = 0;
    let mut kept: Vec<String> = Vec::new();
    let mut dropped = 0;
    for (id, key, line) in pending {
        // `continue`, not `break`: a short line after a long one still fits.
        if used + line.len() + 1 > REPORT_BUDGET {
            dropped += 1;
            continue;
        }
        used += line.len() + 1;
        ledger.record(&id, &key);
        kept.push(line);
    }
    if dropped > 0 {
        let note = format!(
            "  ... {dropped} more changed, omitted for size; they are reported at the \
             next delivery point, or run `agent-tools ps` now"
        );
        // The note itself spends budget too. Pushing it unconditionally could
        // let `kept`'s own total exceed REPORT_BUDGET by the note's length —
        // the same gap `collapse_running`'s `Dropped` case had, in reverse:
        // there the fix was discovered by a test that packed this function
        // this tightly. In the corner where even the note does not fit,
        // saying nothing is the only honest option left; every dropped line
        // already stayed unrecorded, so it is retried at the next delivery
        // point regardless.
        if used + note.len() < REPORT_BUDGET {
            kept.push(note);
        }
    }
    kept
}

/// What became of the still-running children: nothing to say, something said
/// in full, or something that had to be left out.
///
/// `None` and `Dropped` are kept apart for the reason `bound`'s own "omitted
/// for size" note exists: collapsing "nothing was running" and "something was
/// running but did not fit" into one `None` would make a dropped change
/// indistinguishable from no change at all — the exact failure `REPORT_BUDGET`
/// exists to prevent, arriving through the code meant to prevent it.
#[derive(Debug)]
enum Collapsed {
    None,
    /// This many children changed but could not be named without exceeding
    /// the budget; none of them were recorded, so all stay pending.
    Dropped(usize),
    Line(String),
}

/// One line for every child that is merely still running, grouping them by key
/// and naming each one under its own.
///
/// Naming is not decoration. Counts alone — "17 producing, 2 quiet" — would
/// tell the agent that two children are quiet without telling it which, and
/// the ledger could then not honestly retire them: a key would be recorded as
/// reported when the child holding it was never named. So a child is recorded
/// only once its name is in the line, and if the line will not fit, nothing is
/// recorded and every one of them stays pending for the next delivery point.
///
/// The name is the caller's fourth tuple field, not something recovered here
/// by re-splitting the rendered line: a `--desc` is free text and
/// `escape_control` does not touch `[`, so a name like `build [stage 2]`
/// would split at its own bracket and report the child as `build`.
///
/// `budget` is what `bound` did not already spend on terminal lines, not
/// `REPORT_BUDGET` again — the caller charges both against one ceiling so the
/// two together can never exceed it. The caller also decides, once, which
/// children are "running": this function trusts that partition rather than
/// re-deriving it, so there is exactly one place a key is classified.
fn collapse_running(
    ledger: &mut crate::ledger::Ledger,
    running: Vec<(String, String, String, String)>,
    budget: usize,
) -> Collapsed {
    if running.is_empty() {
        return Collapsed::None;
    }
    let count = running.len();
    let mut groups: std::collections::BTreeMap<String, Vec<(String, String)>> =
        std::collections::BTreeMap::new();
    for (id, key, _line, name) in running {
        groups.entry(key).or_default().push((id, name));
    }
    let body = groups
        .iter()
        .map(|(key, members)| {
            let names: Vec<&str> = members.iter().map(|(_, n)| n.as_str()).collect();
            format!("[{}] {}", key, names.join(", "))
        })
        .collect::<Vec<_>>()
        .join("; ");
    // PROMPT-COUPLED
    let line = format!("  still running: {body}  -> agent-tools ps");
    if line.len() + 1 > budget {
        return Collapsed::Dropped(count);
    }
    for (key, members) in &groups {
        for (id, _) in members {
            ledger.record(id, key);
        }
    }
    Collapsed::Line(line)
}

#[cfg(test)]
mod tests {
    use super::{report_header, Collapsed};

    #[test]
    fn a_header_stamps_the_instant_it_is_handed() {
        // The stamp is the anchor a compacted report is re-read against, so it
        // must name the instant the lines were measured at. A header reading
        // its own clock still looks right in isolation and is wrong by however
        // long the scan took, which is why the instant is asserted rather than
        // the shape.
        let at = chrono::DateTime::from_timestamp(chrono::Utc::now().timestamp() - 11_237, 0)
            .expect("a timestamp in range");
        let header = report_header(at);
        let stamp = header
            .strip_prefix("[agent-tools] run status @ ")
            .and_then(|s| s.strip_suffix(':'))
            .unwrap_or_else(|| panic!("header shape: {header:?}"));
        // Read back through the offset the stamp itself carries, so the
        // assertion holds in whatever zone the test runs in. The date comes
        // from `at` because the stamp does not carry one; a header stamping a
        // different instant lands on a different time of day and fails here.
        let local_date = at.with_timezone(&chrono::Local).format("%Y-%m-%d");
        let parsed = chrono::DateTime::parse_from_str(
            &format!("{local_date} {stamp}"),
            "%Y-%m-%d %H:%M:%S %z",
        )
        .unwrap_or_else(|e| panic!("stamp {stamp:?} did not parse: {e}"));
        assert_eq!(
            parsed.with_timezone(&chrono::Utc),
            at,
            "the header stamped {stamp:?}, which is not the instant it was handed"
        );
    }

    #[test]
    fn bounds_own_dropped_count_note_never_pushes_the_kept_total_past_the_budget() {
        // Uniform lines that pack tightly enough that some are dropped and the
        // remainder left over is smaller than the note announcing the drop —
        // the same shape of gap `collapse_running`'s `Dropped` case had,
        // discovered in this sibling function by a test that packed it
        // exactly this tightly. Announcing the drop is `bound`'s preference
        // (see the test below, which has room for the note and gets one), but
        // never at the cost of the one invariant that actually matters here:
        // `kept`'s own total staying inside the budget it exists to enforce.
        let tmp = tempfile::TempDir::new().unwrap();
        let mut ledger = crate::ledger::Ledger::open(tmp.path()).unwrap();
        let line_len = 100;
        let count = super::REPORT_BUDGET / (line_len + 1) + 6;
        let pending: Vec<(String, String, String)> = (0..count)
            .map(|i| {
                (
                    format!("a/{i}"),
                    "final(0)".to_string(),
                    "x".repeat(line_len),
                )
            })
            .collect();
        let kept = super::bound(&mut ledger, pending);
        let total: usize = kept.iter().map(|l| l.len() + 1).sum();
        assert!(
            total <= super::REPORT_BUDGET,
            "the dropped-count note must not itself push the kept total past \
             the budget: {total} bytes, kept: {kept:?}"
        );
    }

    #[test]
    fn a_short_line_after_one_that_does_not_fit_still_lands() {
        // Scan order is the filesystem's. A child whose line does not fit must
        // not end the report: the ones after it in that order still have room.
        let tmp = tempfile::TempDir::new().unwrap();
        let mut ledger = crate::ledger::Ledger::open(tmp.path()).unwrap();
        let oversized = "b".repeat(super::REPORT_BUDGET - 100);
        let pending = vec![
            ("a/1".to_string(), "final(0)".to_string(), "a".repeat(200)),
            ("b/2".to_string(), "final(0)".to_string(), oversized),
            ("c/3".to_string(), "final(0)".to_string(), "c".repeat(50)),
        ];
        let lines = super::bound(&mut ledger, pending);
        assert!(lines.iter().any(|l| l.starts_with("aaa")), "lines: {lines:?}");
        assert!(
            lines.iter().any(|l| l.starts_with("ccc")),
            "the short line after the one that did not fit must still land"
        );
        assert!(lines.iter().any(|l| l.contains("1 more changed")), "the drop is counted");
        assert!(ledger.changed("b/2", "final(0)"), "a dropped line must stay pending");
        assert!(!ledger.changed("a/1", "final(0)"), "a kept line must be recorded");
        assert!(!ledger.changed("c/3", "final(0)"), "a kept line must be recorded");
    }

    #[test]
    fn a_collapsed_line_is_dropped_rather_than_pushing_the_total_past_the_budget() {
        // `bound` and the collapsed line share one ceiling. Checking the
        // collapsed line against the whole of it — the same ceiling `bound`
        // already spent part of on terminal lines — would let the two sum
        // past REPORT_BUDGET, and a report over that size is replaced whole by
        // the runtime's stub, which reads to the agent as nothing changed.
        let tmp = tempfile::TempDir::new().unwrap();
        let mut ledger = crate::ledger::Ledger::open(tmp.path()).unwrap();

        // One terminal line sized so only a sliver of the budget remains.
        let terminal = vec![(
            "a/1".to_string(),
            "final(0)".to_string(),
            "x".repeat(super::REPORT_BUDGET - 40),
        )];
        let lines = super::bound(&mut ledger, terminal);
        let used: usize = lines.iter().map(|l| l.len() + 1).sum();

        // Comfortably under REPORT_BUDGET on its own, but not under the
        // sliver `bound` left behind.
        let running = vec![(
            "b/2".to_string(),
            "producing".to_string(),
            "irrelevant".to_string(),
            "y".repeat(80),
        )];
        let collapsed = super::collapse_running(&mut ledger, running, super::REPORT_BUDGET - used);
        assert!(
            matches!(collapsed, Collapsed::Dropped(1)),
            "a collapsed line that does not fit what bound left behind must be \
             dropped whole and counted, not silently appended on top of an \
             already-full budget, and not folded into Collapsed::None either: \
             got {collapsed:?}"
        );
    }
}
