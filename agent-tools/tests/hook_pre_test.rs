use std::process::{Command, Stdio};
use std::io::Write;

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

#[test]
fn main_thread_rewrite_creates_state_and_returns_updated_input() {
    let home = tempfile::tempdir().unwrap();
    let input = serde_json::json!({
        "session_id": "sid-test",
        "cwd": "/tmp",
        "tool_name": "Bash",
        "tool_input": {"command": "echo $((1+1))", "description": "math"},
        "tool_use_id": "tuid-test"
    }).to_string();

    let mut child = Command::new(bin())
        .arg("hook-pre")
        .env("HOME", home.path())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.as_mut().unwrap().write_all(input.as_bytes()).unwrap();
    let out = child.wait_with_output().unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));

    let parsed: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    assert_eq!(parsed["hookSpecificOutput"]["hookEventName"], "PreToolUse");
    assert_eq!(parsed["hookSpecificOutput"]["permissionDecision"], "allow");
    let new_cmd = parsed["hookSpecificOutput"]["updatedInput"]["command"]
        .as_str()
        .unwrap();
    assert!(
        new_cmd.starts_with("exec agent-tools wrap-task "),
        "got: {new_cmd}"
    );

    let task_dir = home
        .path()
        .join(".claude/agent-tools/sid-test/tuid-test");
    assert!(task_dir.join("meta.json").exists());
    assert!(task_dir.join("command.sh").exists());
    assert_eq!(
        std::fs::read_to_string(task_dir.join("command.sh")).unwrap(),
        "echo $((1+1))"
    );

    let task_dir_str = task_dir.to_string_lossy();
    assert!(new_cmd.contains(task_dir_str.as_ref()), "got: {new_cmd}");
}

#[test]
fn subagent_path_includes_agent_id() {
    let home = tempfile::tempdir().unwrap();
    let input = serde_json::json!({
        "session_id": "sid-test",
        "agent_id": "agent-x",
        "cwd": "/tmp",
        "tool_name": "Monitor",
        "tool_input": {"command": "tail -f /var/log/foo"},
        "tool_use_id": "tuid-2"
    }).to_string();

    let mut child = Command::new(bin())
        .arg("hook-pre")
        .env("HOME", home.path())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.as_mut().unwrap().write_all(input.as_bytes()).unwrap();
    let out = child.wait_with_output().unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));

    let task_dir = home
        .path()
        .join(".claude/agent-tools/sid-test/agent-x/tuid-2");
    assert!(task_dir.join("meta.json").exists());
}

#[test]
fn preserves_timeout_description_run_in_background_in_updated_input() {
    // Regression: hook_pre previously emitted updatedInput with only `command`,
    // which Claude Code uses as a full replacement (queryHelpers.ts), silently
    // dropping timeout/description/run_in_background/dangerouslyDisableSandbox.
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
    }).to_string();

    let mut child = Command::new(bin())
        .arg("hook-pre")
        .env("HOME", home.path())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.as_mut().unwrap().write_all(input.as_bytes()).unwrap();
    let out = child.wait_with_output().unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));

    let parsed: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    let ui = &parsed["hookSpecificOutput"]["updatedInput"];

    // command rewritten to the wrap-task invocation
    let new_cmd = ui["command"].as_str().expect("command missing");
    assert!(
        new_cmd.starts_with("exec agent-tools wrap-task "),
        "got: {new_cmd}"
    );

    // every other field from the original tool_input must be preserved
    assert_eq!(ui["description"].as_str(), Some("long sleep"),
        "description was dropped from updatedInput: {ui}");
    assert_eq!(ui["timeout"].as_u64(), Some(5000),
        "timeout was dropped from updatedInput: {ui}");
    assert_eq!(ui["run_in_background"].as_bool(), Some(true),
        "run_in_background was dropped from updatedInput: {ui}");
    // Unknown / future fields must also pass through — the hook should not
    // enumerate fields, it should treat tool_input as opaque except for command.
    assert_eq!(ui["dangerouslyDisableSandbox"].as_bool(), Some(true),
        "unknown field dangerouslyDisableSandbox was dropped: {ui}");
}

#[test]
fn command_with_special_chars_is_written_verbatim() {
    let home = tempfile::tempdir().unwrap();
    let weird = "echo 'a\"b\\$c\nd' | grep foo | tail -1";
    let input = serde_json::json!({
        "session_id": "sid-test",
        "cwd": "/tmp",
        "tool_name": "Bash",
        "tool_input": {"command": weird},
        "tool_use_id": "tuid-3"
    }).to_string();

    let mut child = Command::new(bin())
        .arg("hook-pre")
        .env("HOME", home.path())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.as_mut().unwrap().write_all(input.as_bytes()).unwrap();
    let out = child.wait_with_output().unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));

    let command_sh = home
        .path()
        .join(".claude/agent-tools/sid-test/tuid-3/command.sh");
    assert_eq!(std::fs::read_to_string(&command_sh).unwrap(), weird);
}
