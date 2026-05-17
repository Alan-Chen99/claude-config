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
