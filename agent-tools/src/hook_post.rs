use anyhow::{Context, Result};
use std::fs;
use std::io::Read;
use std::path::PathBuf;

use crate::hook_input;
use crate::paths;

/// Ceiling on the report body. `additionalContext` is capped at 10,000
/// characters and the runtime silently replaces anything longer with a
/// ~2,000-character stub — which the agent would read as "nothing else
/// changed". The margin below the cap leaves room for the reset note and the
/// BACKGROUNDED notice sharing the same field.
const REPORT_BUDGET: usize = 9_000;

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

    let changes = report_changes(&input.session_id, input.agent_id.as_deref())?;
    if !changes.is_empty() {
        parts.push(format!("[agent-tools] run status:\n{}", changes.join("\n")));
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
            "additionalContext": parts.join(" ")
        }
    });
    println!("{}", serde_json::to_string(&out)?);
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

/// Scan every capture dir in this agent's scope, derive each status, and
/// return one line per child whose key changed since it was last reported.
fn report_changes(session_id: &str, agent_id: Option<&str>) -> Result<Vec<String>> {
    let scope = scope_dir(session_id, agent_id)?;
    if !scope.is_dir() {
        return Ok(Vec::new());
    }
    let now = chrono::Utc::now();
    let mut ledger = crate::ledger::Ledger::open(&scope)?;
    let mut pending: Vec<(String, String, String)> = Vec::new();

    for tuid_entry in fs::read_dir(&scope)?.flatten() {
        let tuid_dir = tuid_entry.path();
        if !tuid_dir.is_dir() {
            continue;
        }
        let Some(tuid) = tuid_dir.file_name().and_then(|n| n.to_str()) else {
            continue;
        };
        for cap_entry in fs::read_dir(&tuid_dir)?.flatten() {
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
                ));
            }
        }
    }
    let mut lines = bound(&mut ledger, pending);
    // A reset ledger makes every child look new. Say why, or the agent sees a
    // burst of repeats with no explanation.
    if let Some(reason) = ledger.reset_reason.clone() {
        lines.insert(
            0,
            format!(
                "  note: report history lost — {reason}; each child below is reported again once"
            ),
        );
    }
    ledger.commit()?;
    Ok(lines)
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
        kept.push(format!(
            "  ... {dropped} more changed, omitted for size; they are reported at the \
             next delivery point, or run `agent-tools ps` now"
        ));
    }
    kept
}
