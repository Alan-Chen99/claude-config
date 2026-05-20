use anyhow::{Context, Result};
use std::io::Read;

use crate::hook_input;
use crate::paths;

pub fn run() -> Result<()> {
    let mut buf = String::new();
    std::io::stdin()
        .read_to_string(&mut buf)
        .context("read stdin")?;

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

    // tool_input is a raw Value: extract command safely, round-trip every
    // other field. updatedInput is a full replacement (queryHelpers.ts:262-272),
    // not a merge — anything we don't echo back (timeout, description,
    // run_in_background, dangerouslyDisableSandbox, future fields) is silently
    // dropped from the executed tool call.
    let Some(command) = input.tool_input.get("command").and_then(|v| v.as_str()) else {
        eprintln!(
            "agent-tools hook-pre: tool_input.command missing or not a string; \
             allowing original command"
        );
        print_allow_passthrough();
        return Ok(());
    };

    let parent_dir = paths::parent_dir_for(
        &input.session_id,
        input.agent_id.as_deref(),
        &input.tool_use_id,
    )?;
    let quoted_dir = shell_single_quote(&parent_dir.to_string_lossy());
    let new_command = format!(
        "unset HTTPS_PROXY NODE_EXTRA_CA_CERTS NODE_OPTIONS; \
         export AGENT_TOOLS_PARENT_DIR={quoted_dir}; \
         {command}",
    );

    // Clone tool_input verbatim and overwrite only `command`.
    // serde_json::Value::Object preserves insertion order, so the rewritten
    // command stays in the same position the model emitted it in.
    let mut updated_input = input.tool_input.clone();
    match updated_input.as_object_mut() {
        Some(obj) => {
            obj.insert(
                "command".to_string(),
                serde_json::Value::String(new_command),
            );
        }
        None => {
            // tool_input wasn't a JSON object — fall back to minimal updatedInput.
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
