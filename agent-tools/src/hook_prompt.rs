use anyhow::{Context, Result};
use std::io::{Read, Write};

/// UserPromptSubmit hook. A user turn is a delivery point, so it carries the
/// same status-change report as a tool result. Main-thread scope only: a user
/// turn is never addressed to a subagent.
pub fn run() -> Result<()> {
    let mut buf = String::new();
    std::io::stdin().read_to_string(&mut buf)?;
    let v: serde_json::Value = match serde_json::from_str(&buf) {
        Ok(v) => v,
        Err(e) => {
            eprintln!("agent-tools hook-prompt: parse error: {e:#}");
            return Ok(());
        }
    };
    let Some(session_id) = v.get("session_id").and_then(|s| s.as_str()) else {
        return Ok(());
    };
    // A reporting failure must not surface as a hook error on the user's own
    // turn. Say so in the context instead, and keep the turn moving.
    //
    // `None` for the agent id is the whole point of the scope argument here: a
    // user turn reaches the main thread, so consuming a subagent's pending
    // reports would retire changes that subagent has not been told about.
    let mut delivered = None;
    let ctx = match crate::hook_post::report_changes(session_id, None) {
        Ok(report) if report.lines.is_empty() => return Ok(()),
        Ok(report) => {
            let ctx = format!(
                "{}\n{}",
                crate::hook_post::report_header(report.at),
                report.lines.join("\n")
            );
            delivered = Some(report);
            ctx
        }
        Err(e) => {
            eprintln!("agent-tools hook-prompt: status report failed: {e:#}");
            format!(
                "[agent-tools] run status: unavailable this time ({e}); \
                 run `agent-tools ps` for the current state"
            )
        }
    };
    // Write, flush, then record: a change recorded before it reached the agent
    // matches at every later delivery point and is never reported again.
    let mut stdout = std::io::stdout().lock();
    writeln!(
        stdout,
        "{}",
        serde_json::json!({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": ctx
            }
        })
    )
    .context("write hook output")?;
    stdout.flush().context("flush hook output")?;
    if let Some(report) = delivered {
        report.commit()?;
    }
    Ok(())
}
