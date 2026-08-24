use anyhow::Result;
use std::io::Read;

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
    let ctx = match crate::hook_post::report_changes(session_id, None) {
        Ok(changes) if changes.is_empty() => return Ok(()),
        Ok(changes) => format!("[agent-tools] run status:\n{}", changes.join("\n")),
        Err(e) => {
            eprintln!("agent-tools hook-prompt: status report failed: {e:#}");
            format!(
                "[agent-tools] run status: unavailable this time ({e}); \
                 run `agent-tools ps` for the current state"
            )
        }
    };
    println!(
        "{}",
        serde_json::json!({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": ctx
            }
        })
    );
    Ok(())
}
