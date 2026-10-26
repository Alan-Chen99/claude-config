use anyhow::{bail, Context, Result};
use std::fs;
use std::io::{Read, Write};

use crate::hook_input;
use crate::paths;

/// Ceiling on the report body, self-imposed rather than forced: the report
/// rides on a tool result the agent asked for, and a report that crowds it out
/// costs more than the lines it carries.
///
/// Two of Claude Code's own ceilings bear on the number, and only one of them
/// reaches a local command hook.
///
/// The 8,000-character/200-line `additionalContext` cap — truncating and
/// flagging rather than dropping (the cap table at
/// `src/chunk-6h7ejyet.js:13323-13329`, marker `additionalContext: 8000`,
/// applied by `KMo` at `:13338` through `Cr` at `:13351`) — is applied by the
/// answer sanitizer `Rhe` (`:13530`) on the paths that sanitize an answer
/// before using it: the cloud relay (`src/chunk-nc2bf1j8.js:542`, the chunk
/// that carries `Hooks the cloud session forwards here` at `:1508`), callback
/// hooks (`src/chunk-9rp40b48.js:510`) and device hook templates
/// (`src/chunk-gjq2zs1s.js:381`). Since 2.1.310 a hook from the user's own
/// settings passes through `Rhe` too (`MV`, `src/chunk-j0tbz6ra.js:142449`,
/// `personal: !0`), but `Cr` hands a personal answer's fields back untouched
/// (`if (e.options.personal === !0) return r;`), so a local command hook's
/// stdout, interpreted by `Bte` (`src/chunk-j0tbz6ra.js:140816`, marker
/// `expectedHookEvent`, called at `:144510`), still meets no cap — and
/// lowering the budget to chase it would cost lines for nothing.
///
/// The ceiling that does apply to every hook kind is persistence: an
/// `additionalContext` longer than 10,000 characters is written to a file and
/// replaced by a `<persisted-output>` stub carrying a 2,000-character preview
/// (threshold `Gii = 1e4`, `src/chunk-r1dvrqha.js:34`; stub built by `zDe`,
/// `src/chunk-z0mss2jj.js:180`, marker `Output too large (`; reached for every
/// hook's `additionalContext` at `src/chunk-j0tbz6ra.js:144889`). 9,000 clears
/// it with the backgrounding notice on top, which this budget deliberately
/// leaves uncharged and which is 250 characters at its widest. A measurement
/// recorded here against 2.1.269 — a PostToolUse command hook returning 18,611
/// characters over 401 lines arriving whole — cannot be reconciled with that
/// threshold, which 2.1.269 carried at the same value under the names `Qhe`
/// and `HEr`; the measurement is kept because the budget is safe either way
/// and the discrepancy is worth re-measuring rather than deleting.
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

    // Independent of the report below, and like it never allowed to fail the
    // tool call this hook answers.
    if let Err(e) = update_inboxes(&input) {
        eprintln!("agent-tools hook-post: inbox update failed: {e:#}");
    }

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
    let flag = |key: &str| {
        input
            .tool_response
            .get(key)
            .and_then(|v| v.as_bool())
            .unwrap_or(false)
    };
    // The Bash tool's output schema names one field per cause
    // (`src/chunk-j0tbz6ra.js:197871-197876`, marker
    // `backgroundedToDeliverMessage`), and the set is the same one 2.1.269
    // declared. The background time limit added since then does not extend it:
    // a task stopped at its deadline is announced through its own notice
    // (`stopped after reaching its background time limit`,
    // `src/chunk-j0tbz6ra.js:5638`) rather than through a field on the call
    // that started it. `timedOutAfterMs` carries the
    // timeout that actually applied, which is not the one the model asked for
    // whenever the runtime shortened it — so the response answers this where
    // `tool_input.timeout` could only guess.
    let timed_out = input
        .tool_response
        .get("timedOutAfterMs")
        .and_then(|v| v.as_u64());
    // Explicit run_in_background is the one cause with no field of its own:
    // the response carries the task id and none of the flags. tool_input here
    // is whatever the pre-hook handed back as updatedInput; the rewrite
    // preserves run_in_background verbatim.
    let explicit = input
        .tool_input
        .get("run_in_background")
        .and_then(|v| v.as_bool())
        .unwrap_or(false);
    let cause = if flag("backgroundedByUser") {
        "user manually backgrounded (Ctrl+B)".to_string()
    } else if flag("backgroundedByTurnAbort") {
        "turn aborted with the command still running".to_string()
    } else if flag("backgroundedToDeliverMessage") {
        "a queued message needed to reach the model".to_string()
    } else if let Some(ms) = timed_out {
        format!("timeout ({ms}ms limit hit)")
    } else if explicit {
        "explicit run_in_background: true".to_string()
    } else {
        // Every cause above is a field the tool response sets. Naming a cause
        // here would be a guess, and a wrong Cause: reads as fact.
        "not stated by the tool response".to_string()
    };
    // An agent nothing re-invokes when the job ends waits inside its turn. A
    // subagent's turn end loses the job under `claude -p` (still so on 2.1.310,
    // measured 2026-10-25: killed when the main thread exits) and wakes its
    // caller interactively; a message, and the job's end, reach a subagent only
    // between tool calls (`notes/cc-2.1.289-subagent-waits.md`). Subagents run
    // without this repo's system prompt and, measured 2026-10-24, do not load
    // the skill on its description, so the notice carries the call itself.
    // A main thread is told only when cc says its job ends with the final
    // response: `backgroundEndsWithFinalResponse`, set for a `-p` main thread
    // unless `"tengu_tidy_sloth"` (default on) holds the process for the shell
    // and starts a turn when it ends (`function ppt()`, 2.1.310; measured
    // 2026-10-25), which is what an interactive main thread gets.
    // A subagent is told whatever the flag says: cc sets it only for a
    // synchronous one ("a synchronous subagent's command"), yet under `-p` an
    // async subagent's shell is killed too when the main thread finishes, as
    // `-p` holds only main-thread shells (`e.agentId === void 0`; measured
    // 2026-10-25, 81848736).
    let who = if input.agent_id.is_some() {
        Some("as a subagent")
    } else if flag("backgroundEndsWithFinalResponse") {
        Some("under `claude -p`")
    } else {
        None
    };
    // cc's Bash text tells an agent it will be notified not to poll the
    // output file; one blocking call is the wait cc itself recommends where
    // nothing notifies ("one foreground shell command that blocks until the
    // output file shows what you need"), so the sentence names the difference
    // rather than read as the polling cc forbids. The wait sizes its own bound
    // to a subagent's prompt cache and to the call's `timeout`, so the hour
    // asked for here is a ceiling, not how long it blocks.
    let in_turn = who.map_or(String::new(), |who| {
        format!(
            " To wait for it {who}, stay in your turn: call `agent-tools wait <its output \
             file>` with Bash `timeout: 3600000` until it reports the job ended. Each call is \
             one blocking wait, not the polling of the file the Bash tool warns against: it \
             returns when the job ends, when a message to you is queued (answer it before \
             the next call), or in time to keep your prompt cache warm. Make each wait the \
             only call in its message: calls in one message run back to back."
        )
    });
    // "Backgrounded" (not "involuntarily backgrounded") — every cause but the
    // last is involuntary from the model's view, while explicit
    // run_in_background is voluntary; the `Cause:` line carries the distinction.
    // PROMPT-COUPLED
    Some(format!(
        "BACKGROUNDED: Command was backgrounded. Cause: {cause}. \
         Process is still running (task_id: {bg_task_id}). \
         To wait for it without polling: load the long-bash skill. \
         To kill it: use TaskStop tool with task_id {bg_task_id}.{in_turn}"
    ))
}

/// Keeps `paths::inbox_path` true for `agent-tools wait`. Claude Code delivers
/// what is queued for an agent when its tool round ends, which is when this
/// hook runs for it, so its own inbox empties here. A SendMessage that left a
/// message waiting for the recipient's next tool round adds a line to the
/// recipient's: SendMessage never cuts a running call short, and the wait is
/// how a subagent in one hears of it (`notes/cc-2.1.310-subagent-wait-costs.md`).
fn update_inboxes(input: &hook_input::PostToolUseInput) -> Result<()> {
    let own = paths::inbox_path(&input.session_id, input.agent_id.as_deref())?;
    match fs::remove_file(&own) {
        Ok(()) => {}
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => {}
        Err(e) => return Err(e).with_context(|| format!("remove {}", own.display())),
    }
    if input.tool_name != "SendMessage" {
        return Ok(());
    }
    let r = &input.tool_response;
    // `Resuming agent <id>` starts the recipient's turn with the message in
    // it, and `to: "main"` names no agent: neither leaves a message waiting.
    let queued = r["message"]
        .as_str()
        .is_some_and(|m| m.starts_with("Message queued for delivery to "));
    let (true, Some(to)) = (queued, r["pin"]["id"].as_str()) else {
        return Ok(());
    };
    if to.is_empty() || !to.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_') {
        bail!("SendMessage's pin.id {to:?} is not an agent id, so no inbox was written");
    }
    let path = paths::inbox_path(&input.session_id, Some(to))?;
    let dir = path.parent().expect("an inbox path has its scope as parent");
    fs::create_dir_all(dir).with_context(|| format!("create {}", dir.display()))?;
    let mut f = fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&path)
        .with_context(|| format!("open {}", path.display()))?;
    let from = input.agent_id.as_deref().unwrap_or("main");
    writeln!(f, "{}\t{from}", chrono::Utc::now().to_rfc3339())
        .with_context(|| format!("append to {}", path.display()))?;
    Ok(())
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
    // Each subagent has its own scope and ledger, so no agent is told of
    // another's runs even within one session.
    let scope = paths::scope_dir(session_id, agent_id)?;
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
    // What the report spends before it carries a single child: the header both
    // delivery points prepend, and the notes prepended after packing. Budgeting
    // from zero measured only the middle of the report and let the ends push the
    // total past the ceiling — a 9,000-char budget emitting 9,003 characters,
    // eating the margin that keeps the report, with the backgrounding notice on
    // top, under the 10,000 characters at which the runtime replaces the whole
    // block with its stub. The notice is deliberately not charged: it rides on
    // top because it is the one message this hook must never drop for size.
    let reserved: usize = report_header(now).len()
        + 1
        + notes.iter().map(|n| n.len() + 1).sum::<usize>();
    let mut lines = bound(
        &mut ledger,
        terminal
            .into_iter()
            .map(|(id, key, line, _, _)| (id, key, line))
            .collect(),
        reserved,
    );
    // `collapse_running` gets only what `bound` left of the budget, not the
    // module ceiling again: checking its one line against the whole of
    // `REPORT_BUDGET` a second time would let the two sums together reach
    // twice it, well past the 10,000 characters at which the runtime replaces
    // the whole report with its stub — which reads to the agent as nothing
    // else changed.
    let used: usize = reserved + lines.iter().map(|l| l.len() + 1).sum::<usize>();
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
    reserved: usize,
) -> Vec<String> {
    // Which lines fit under `ceiling`, and what they spend. `continue`, not
    // `break`: a short line after a long one still fits.
    let select = |ceiling: usize| -> (Vec<usize>, usize) {
        let mut used = reserved;
        let mut fit = Vec::new();
        for (i, (_, _, line)) in pending.iter().enumerate() {
            if used + line.len() + 1 > ceiling {
                continue;
            }
            used += line.len() + 1;
            fit.push(i);
        }
        (fit, used)
    };

    // Two passes, because the note announcing a drop has to have its room
    // reserved before any line is recorded. Checked for after packing, the note
    // is the thing that does not fit — and a truncation nobody announced is
    // indistinguishable from a report of no change, the one failure this
    // function exists to prevent. The first pass only asks whether anything
    // drops and records nothing; the reserve it then takes is the note at its
    // widest possible count, so the second pass dropping more lines can never
    // outgrow it.
    let (fit, used) = select(REPORT_BUDGET);
    let (fit, used) = if fit.len() == pending.len() {
        (fit, used)
    } else {
        select(REPORT_BUDGET.saturating_sub(omitted_note(pending.len()).len() + 1))
    };

    let mut kept: Vec<String> = Vec::with_capacity(fit.len() + 1);
    for i in &fit {
        let (id, key, line) = &pending[*i];
        ledger.record(id, key);
        kept.push(line.clone());
    }
    let dropped = pending.len() - fit.len();
    if dropped > 0 {
        let note = omitted_note(dropped);
        // The second pass reserved this note's room, so it fits unless the
        // caller's own `reserved` had already spent the ceiling. In that corner
        // saying nothing is the only honest option left; every dropped line
        // stayed unrecorded, so it is retried at the next delivery point.
        if used + note.len() < REPORT_BUDGET {
            kept.push(note);
        }
    }
    kept
}

/// The one wording for "some lines did not fit", so the room `bound` reserves
/// for it and the text it finally pushes cannot disagree about its length.
fn omitted_note(dropped: usize) -> String {
    format!(
        "  ... {dropped} more changed, omitted for size; they are reported at the \
         next delivery point, or run `agent-tools ps` now"
    )
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
        // Read back through the date and offset the stamp itself carries, so
        // the assertion holds in whatever zone the test runs in and supplies
        // nothing the reader of a compacted report would not have. A header
        // stamping a different instant fails here.
        let parsed = chrono::DateTime::parse_from_str(stamp, "%Y-%m-%d %H:%M:%S %z")
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
        let kept = super::bound(&mut ledger, pending, 0);
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
        let lines = super::bound(&mut ledger, pending, 0);
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
        // past REPORT_BUDGET and on past the 10,000 characters at which the
        // runtime replaces the whole report with its stub, which reads to the
        // agent as nothing changed.
        let tmp = tempfile::TempDir::new().unwrap();
        let mut ledger = crate::ledger::Ledger::open(tmp.path()).unwrap();

        // One terminal line sized so only a sliver of the budget remains.
        let terminal = vec![(
            "a/1".to_string(),
            "final(0)".to_string(),
            "x".repeat(super::REPORT_BUDGET - 40),
        )];
        let lines = super::bound(&mut ledger, terminal, 0);
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
