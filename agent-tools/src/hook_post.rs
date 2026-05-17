use anyhow::{Context, Result};
use std::io::Read;

use crate::events;
use crate::hook_input;
use crate::paths;

pub fn run() -> Result<()> {
    let mut buf = String::new();
    std::io::stdin().read_to_string(&mut buf).context("read stdin")?;

    let input = match hook_input::parse_post(&buf) {
        Ok(p) => p,
        Err(e) => {
            eprintln!("agent-tools hook-post: parse error: {e:#}");
            return Ok(());
        }
    };

    if input.tool_name != "Bash" && input.tool_name != "Monitor" {
        return Ok(());
    }

    let bg_task_id = input.tool_response.get("backgroundTaskId").and_then(|v| v.as_str());
    let Some(bg_task_id) = bg_task_id else {
        return Ok(());
    };

    let auto = input.tool_response.get("assistantAutoBackgrounded").and_then(|v| v.as_bool()).unwrap_or(false);
    let user = input.tool_response.get("backgroundedByUser").and_then(|v| v.as_bool()).unwrap_or(false);

    let (cause_label, cause_for_context) = if auto {
        ("assistant_auto", "assistant-mode auto-background (KAIROS)".to_string())
    } else if user {
        ("user", "user manually backgrounded (Ctrl+B)".to_string())
    } else {
        let limit = input.tool_input.timeout.unwrap_or(120_000);
        ("timeout", format!("timeout ({limit}ms limit hit)"))
    };

    let task_dir = paths::task_dir_for(
        &input.session_id,
        input.agent_id.as_deref(),
        &input.tool_use_id,
    )?;
    let _ = events::append(
        &task_dir,
        "backgrounded",
        serde_json::json!({
            "cause": cause_label,
            "background_task_id": bg_task_id,
            "timeout_ms": input.tool_input.timeout
        }),
    );

    let additional_context = format!(
        "BACKGROUNDED: Command was involuntarily backgrounded. Cause: {cause}. \
         Process is still running (task_id: {tid}). \
         To kill it: use TaskStop tool with task_id {tid}. \
         Captured output paths in: {task_dir}",
        cause = cause_for_context,
        tid = bg_task_id,
        task_dir = task_dir.display(),
    );

    let out = serde_json::json!({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": additional_context
        }
    });
    println!("{}", serde_json::to_string(&out)?);
    Ok(())
}
