use anyhow::{Context, Result};
use std::fs;
use std::io::Read;
use std::path::PathBuf;

use crate::hook_input;
use crate::meta::{Meta, TaskMeta};
use crate::paths;

const SILENCE_THRESHOLD_MS: u64 = 30_000;

pub fn run() -> Result<()> {
    let mut buf = String::new();
    std::io::stdin().read_to_string(&mut buf).context("read stdin")?;

    let input = match hook_input::parse_pre(&buf) {
        Ok(p) => p,
        Err(e) => {
            eprintln!("agent-tools hook-pre: parse error: {e:#}");
            print_allow_passthrough();
            return Ok(());
        }
    };

    if input.tool_name != "Bash" && input.tool_name != "Monitor" {
        print_allow_passthrough();
        return Ok(());
    }

    // tool_input.command is the only field we rewrite; everything else
    // (timeout, description, run_in_background, dangerouslyDisableSandbox,
    // future Bash/Monitor fields) must round-trip unchanged because
    // updatedInput is a full replacement, not a merge.
    let Some(command) = input.tool_input.get("command").and_then(|v| v.as_str()) else {
        eprintln!(
            "agent-tools hook-pre: tool_input.command missing or not a string; \
             allowing original command"
        );
        print_allow_passthrough();
        return Ok(());
    };
    let description = input
        .tool_input
        .get("description")
        .and_then(|v| v.as_str())
        .map(String::from);

    let task_dir = paths::task_dir_for(
        &input.session_id,
        input.agent_id.as_deref(),
        &input.tool_use_id,
    )?;

    if let Err(e) = prepare_task_dir(&task_dir, &input, command, description) {
        eprintln!("agent-tools hook-pre: setup failed ({e:#}); allowing original command");
        print_allow_passthrough();
        return Ok(());
    }

    let quoted = shell_single_quote(&task_dir.to_string_lossy());
    let new_command = format!("exec agent-tools wrap-task {quoted}");

    // Clone the original tool_input verbatim and overwrite only `command`.
    // serde_json::Value::Object preserves insertion order, so the rewritten
    // command stays in the same position the model emitted it in.
    let mut updated_input = input.tool_input.clone();
    match updated_input.as_object_mut() {
        Some(obj) => {
            obj.insert("command".to_string(), serde_json::Value::String(new_command));
        }
        None => {
            // tool_input wasn't a JSON object — can't pass-through. Build a
            // minimal updatedInput with just command (legacy behavior).
            updated_input = serde_json::json!({ "command": new_command });
        }
    }

    let out = serde_json::json!({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": updated_input
        }
    });
    println!("{}", serde_json::to_string(&out)?);
    Ok(())
}

fn prepare_task_dir(
    task_dir: &PathBuf,
    input: &hook_input::PreToolUseInput,
    command: &str,
    description: Option<String>,
) -> Result<()> {
    fs::create_dir_all(task_dir.join("children"))
        .with_context(|| format!("mkdir {}", task_dir.display()))?;
    fs::write(task_dir.join("command.sh"), command)
        .with_context(|| format!("write command.sh under {}", task_dir.display()))?;
    let meta = Meta::Task(TaskMeta {
        session_id: input.session_id.clone(),
        agent_id: input.agent_id.clone(),
        task_id: input.tool_use_id.clone(),
        tool: input.tool_name.clone(),
        tool_use_id: input.tool_use_id.clone(),
        desc: description,
        cwd: input.cwd.clone(),
        pid: None,
        started_at: None,
        ended_at: None,
        exit_code: None,
        silence_threshold_ms: SILENCE_THRESHOLD_MS,
    });
    crate::meta::write_meta(task_dir, &meta)?;
    Ok(())
}

fn print_allow_passthrough() {
    let out = serde_json::json!({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow"
        }
    });
    println!("{}", serde_json::to_string(&out).unwrap());
}

/// Single-quote a string for safe inclusion in a `bash -c` argument. Replaces
/// each existing `'` with `'\''` (close, escaped quote, reopen) and wraps in
/// single quotes.
fn shell_single_quote(s: &str) -> String {
    let mut out = String::with_capacity(s.len() + 2);
    out.push('\'');
    for ch in s.chars() {
        if ch == '\'' {
            out.push_str("'\\''");
        } else {
            out.push(ch);
        }
    }
    out.push('\'');
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn quotes_plain() {
        assert_eq!(shell_single_quote("abc"), "'abc'");
    }
    #[test]
    fn quotes_with_single_quote() {
        assert_eq!(shell_single_quote("a'b"), "'a'\\''b'");
    }
    #[test]
    fn quotes_path() {
        assert_eq!(
            shell_single_quote("/h/.claude/agent-tools/sid/tid"),
            "'/h/.claude/agent-tools/sid/tid'"
        );
    }
}
