use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("agent-tools/ should have a parent")
        .to_path_buf()
}

fn agent_tools() -> Command {
    let mut command = Command::new(bin());
    command.env("CLAUDE_CONFIG_ROOT", worktree_root());
    command
}

fn run_hook_pre(home: &std::path::Path, input: &str) -> std::process::Output {
    run_hook_pre_env(home, input, &[])
}

/// The Bash timeout variables the hook reads are cleared first, so the
/// session running the tests cannot leak its own into them.
fn run_hook_pre_env(home: &std::path::Path, input: &str, env: &[(&str, &str)]) -> std::process::Output {
    let mut c = agent_tools();
    c.arg("hook-pre")
        .env("HOME", home)
        .env_remove("BASH_DEFAULT_TIMEOUT_MS")
        .env_remove("BASH_MAX_TIMEOUT_MS");
    for (k, v) in env {
        c.env(k, v);
    }
    let mut child = c
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child
        .stdin
        .as_mut()
        .unwrap()
        .write_all(input.as_bytes())
        .unwrap();
    let out = child.wait_with_output().unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    out
}

/// Check that `cmd` matches the regex
/// `^unset HTTPS_PROXY NODE_EXTRA_CA_CERTS NODE_OPTIONS; export AGENT_TOOLS_PARENT_DIR='[^']+'( AGENT_TOOLS_CALL_TIMEOUT_MS=<ms>)?; <orig>$`
/// without pulling in a regex dependency; `timeout_ms` is the part in parentheses.
fn assert_matches_envprefix(cmd: &str, orig: &str, timeout_ms: Option<u64>) {
    let prefix =
        "unset HTTPS_PROXY NODE_EXTRA_CA_CERTS NODE_OPTIONS; export AGENT_TOOLS_PARENT_DIR='";
    assert!(cmd.starts_with(prefix), "missing prefix; got: {cmd}");
    let timeout = timeout_ms.map_or(String::new(), |ms| format!(" AGENT_TOOLS_CALL_TIMEOUT_MS={ms}"));
    let suffix = format!("'{timeout}; {orig}");
    assert!(
        cmd.ends_with(&suffix),
        "missing suffix `{suffix}`; got: {cmd}"
    );
    let inner = &cmd[prefix.len()..cmd.len() - suffix.len()];
    assert!(!inner.is_empty(), "empty path between quotes; got: {cmd}");
    assert!(
        !inner.contains('\''),
        "path between quotes must not contain `'`; got: {cmd}"
    );
}

#[test]
fn bash_simple_command_is_wrapped_with_env_prefix() {
    let home = tempfile::tempdir().unwrap();
    let input = serde_json::json!({
        "session_id": "sid-test",
        "cwd": "/tmp",
        "tool_name": "Bash",
        "tool_input": {"command": "echo hi", "description": "greet"},
        "tool_use_id": "tuid-test"
    })
    .to_string();

    let out = run_hook_pre(home.path(), &input);
    let parsed: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    assert_eq!(parsed["hookSpecificOutput"]["hookEventName"], "PreToolUse");
    assert_eq!(parsed["hookSpecificOutput"]["permissionDecision"], "allow");
    let new_cmd = parsed["hookSpecificOutput"]["updatedInput"]["command"]
        .as_str()
        .unwrap();
    assert_matches_envprefix(new_cmd, "echo hi", Some(120_000));
}

#[test]
fn main_thread_exports_session_slash_tool_use_id() {
    let home = tempfile::tempdir().unwrap();
    let input = serde_json::json!({
        "session_id": "sid-test",
        "cwd": "/tmp",
        "tool_name": "Bash",
        "tool_input": {"command": "echo hi"},
        "tool_use_id": "tuid-test"
    })
    .to_string();

    let out = run_hook_pre(home.path(), &input);
    let parsed: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    let new_cmd = parsed["hookSpecificOutput"]["updatedInput"]["command"]
        .as_str()
        .unwrap();

    // Extract the path between the single quotes after AGENT_TOOLS_PARENT_DIR=.
    let marker = "AGENT_TOOLS_PARENT_DIR='";
    let start = new_cmd.find(marker).expect("marker present") + marker.len();
    let rest = &new_cmd[start..];
    let end = rest.find('\'').expect("closing quote");
    let path = &rest[..end];
    assert!(
        path.ends_with("sid-test/tuid-test"),
        "expected path to end with sid-test/tuid-test; got: {path}"
    );
}

#[test]
fn subagent_exports_session_slash_agent_slash_tool_use_id() {
    let home = tempfile::tempdir().unwrap();
    let input = serde_json::json!({
        "session_id": "sid-test",
        "agent_id": "agent-x",
        "cwd": "/tmp",
        "tool_name": "Monitor",
        "tool_input": {"command": "tail -f /var/log/foo"},
        "tool_use_id": "tuid-2"
    })
    .to_string();

    let out = run_hook_pre(home.path(), &input);
    let parsed: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    let new_cmd = parsed["hookSpecificOutput"]["updatedInput"]["command"]
        .as_str()
        .unwrap();

    let marker = "AGENT_TOOLS_PARENT_DIR='";
    let start = new_cmd.find(marker).expect("marker present") + marker.len();
    let rest = &new_cmd[start..];
    let end = rest.find('\'').expect("closing quote");
    let path = &rest[..end];
    assert!(
        path.ends_with("sid-test/agent-x/tuid-2"),
        "expected path to end with sid-test/agent-x/tuid-2; got: {path}"
    );
}

#[test]
fn non_bash_non_monitor_passthrough() {
    let home = tempfile::tempdir().unwrap();
    let input = serde_json::json!({
        "session_id": "sid-test",
        "cwd": "/tmp",
        "tool_name": "Read",
        "tool_input": {"file_path": "/tmp/x"},
        "tool_use_id": "tuid-read"
    })
    .to_string();

    let out = run_hook_pre(home.path(), &input);
    let parsed: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    assert_eq!(parsed["hookSpecificOutput"]["hookEventName"], "PreToolUse");
    assert_eq!(parsed["hookSpecificOutput"]["permissionDecision"], "allow");
    assert!(
        parsed["hookSpecificOutput"].get("updatedInput").is_none(),
        "passthrough must not include updatedInput; got: {parsed}"
    );
}

#[test]
fn hook_does_not_create_parent_dir_on_disk() {
    let home = tempfile::tempdir().unwrap();
    let input = serde_json::json!({
        "session_id": "sid-test",
        "cwd": "/tmp",
        "tool_name": "Bash",
        "tool_input": {"command": "echo hi"},
        "tool_use_id": "tuid-lazy"
    })
    .to_string();

    let _ = run_hook_pre(home.path(), &input);

    let parent_dir = home.path().join(".claude/agent-tools/sid-test/tuid-lazy");
    assert!(
        !parent_dir.exists(),
        "parent dir must not be created by hook-pre (lazy creation); exists at {}",
        parent_dir.display()
    );
}

#[test]
fn single_quote_in_original_command_is_preserved_byte_for_byte() {
    let home = tempfile::tempdir().unwrap();
    let orig = "echo 'a\"b\\$c' | grep foo | tail -1";
    let input = serde_json::json!({
        "session_id": "sid-test",
        "cwd": "/tmp",
        "tool_name": "Bash",
        "tool_input": {"command": orig},
        "tool_use_id": "tuid-quote"
    })
    .to_string();

    let out = run_hook_pre(home.path(), &input);
    let parsed: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    let new_cmd = parsed["hookSpecificOutput"]["updatedInput"]["command"]
        .as_str()
        .unwrap();

    let separator = "; ";
    // The original command must appear verbatim after the final `; ` between the
    // export statement and the user's command.
    let suffix = format!("{separator}{orig}");
    assert!(
        new_cmd.ends_with(&suffix),
        "original command not preserved verbatim after `; `; got: {new_cmd}"
    );
}

#[test]
fn preserves_timeout_description_run_in_background_in_updated_input() {
    // Regression (main b279c25): hook_pre previously emitted updatedInput with
    // only `command`, which Claude Code uses as a full replacement
    // (queryHelpers.ts:262-272), silently dropping timeout/description/
    // run_in_background/dangerouslyDisableSandbox. The fix clones tool_input
    // verbatim and overwrites only `command`.
    let home = tempfile::tempdir().unwrap();
    let input = serde_json::json!({
        "session_id": "sid-test",
        "cwd": "/tmp",
        "tool_name": "Bash",
        "tool_input": {
            "command": "sleep 9999",
            "description": "long sleep",
            "timeout": 5000,
            "run_in_background": true,
            "dangerouslyDisableSandbox": true
        },
        "tool_use_id": "tuid-preserve"
    })
    .to_string();

    let out = run_hook_pre(home.path(), &input);
    let parsed: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    let ui = &parsed["hookSpecificOutput"]["updatedInput"];

    // command rewritten with env prefix, original tail preserved
    let new_cmd = ui["command"].as_str().expect("command missing");
    assert_matches_envprefix(new_cmd, "sleep 9999", None);

    // every other field from the original tool_input must round-trip
    assert_eq!(
        ui["description"].as_str(),
        Some("long sleep"),
        "description was dropped from updatedInput: {ui}"
    );
    assert_eq!(
        ui["timeout"].as_u64(),
        Some(5000),
        "timeout was dropped from updatedInput: {ui}"
    );
    assert_eq!(
        ui["run_in_background"].as_bool(),
        Some(true),
        "run_in_background was dropped from updatedInput: {ui}"
    );
    // Unknown / future fields must also pass through — the hook should not
    // enumerate fields, it should treat tool_input as opaque except for command.
    assert_eq!(
        ui["dangerouslyDisableSandbox"].as_bool(),
        Some(true),
        "unknown field dangerouslyDisableSandbox was dropped: {ui}"
    );
}

/// `agent-tools wait` reads the exported value to return before the call is
/// moved to the background, so it must be the timeout Claude Code applies.
#[test]
fn a_foreground_bash_call_exports_the_timeout_claude_code_applies() {
    let exported = |tool: &str, tool_input: serde_json::Value, env: &[(&str, &str)]| {
        let home = tempfile::tempdir().unwrap();
        let input = serde_json::json!({
            "session_id": "sid-test",
            "agent_id": "a1",
            "tool_name": tool,
            "tool_input": tool_input,
            "tool_use_id": "tuid-t"
        })
        .to_string();
        let out = run_hook_pre_env(home.path(), &input, env);
        let parsed: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
        let cmd = parsed["hookSpecificOutput"]["updatedInput"]["command"].as_str().unwrap().to_string();
        let marker = "AGENT_TOOLS_CALL_TIMEOUT_MS=";
        cmd.find(marker).map(|i| cmd[i + marker.len()..].split(';').next().unwrap().parse::<u64>().unwrap())
    };
    let wait = |timeout: Option<u64>| match timeout {
        Some(t) => serde_json::json!({"command": "agent-tools wait", "timeout": t}),
        None => serde_json::json!({"command": "agent-tools wait"}),
    };
    assert_eq!(exported("Bash", wait(None), &[]), Some(120_000));
    assert_eq!(exported("Bash", wait(Some(300_000)), &[]), Some(300_000));
    // Clamped to the 10-minute ceiling, raised by BASH_MAX_TIMEOUT_MS.
    assert_eq!(exported("Bash", wait(Some(3_600_000)), &[]), Some(600_000));
    assert_eq!(
        exported("Bash", wait(Some(3_600_000)), &[("BASH_MAX_TIMEOUT_MS", "2147483647")]),
        Some(3_600_000)
    );
    // A default above the ceiling raises the ceiling to it.
    assert_eq!(exported("Bash", wait(None), &[("BASH_DEFAULT_TIMEOUT_MS", "900000")]), Some(900_000));
    assert_eq!(
        exported("Bash", serde_json::json!({"command": "x", "run_in_background": true, "timeout": 5000}), &[]),
        None
    );
    assert_eq!(exported("Monitor", serde_json::json!({"command": "x", "timeout_ms": 5000}), &[]), None);
}
