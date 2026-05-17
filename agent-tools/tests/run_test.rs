use std::process::Command;
use std::path::PathBuf;

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn make_task(home: &std::path::Path) -> PathBuf {
    let dir = home.join(".claude/agent-tools/sid/tuid");
    std::fs::create_dir_all(dir.join("children")).unwrap();
    let meta = serde_json::json!({
        "kind":"task","session_id":"sid","agent_id":null,"task_id":"tuid",
        "tool":"Bash","tool_use_id":"tuid","desc":null,"cwd":"/tmp",
        "pid":1,"started_at":null,"ended_at":null,"exit_code":null,
        "silence_threshold_ms":30000
    });
    std::fs::write(dir.join("meta.json"), serde_json::to_string_pretty(&meta).unwrap()).unwrap();
    std::fs::write(dir.join("command.sh"), "true").unwrap();
    dir
}

#[test]
fn errors_when_env_not_set() {
    let home = tempfile::tempdir().unwrap();
    let out = Command::new(bin())
        .args(["run", "--", "echo", "hi"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_TASK_ID")
        .output()
        .unwrap();
    assert!(!out.status.success());
    assert!(String::from_utf8_lossy(&out.stderr).contains("AGENT_TOOLS_TASK_ID"));
}

#[test]
fn captures_child_stdout_and_forwards() {
    let home = tempfile::tempdir().unwrap();
    let task_dir = make_task(home.path());
    let out = Command::new(bin())
        .args(["run", "--", "bash", "-c", "echo hello; echo bad 1>&2; exit 0"])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_TASK_ID", &task_dir)
        .output()
        .unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));
    assert_eq!(String::from_utf8_lossy(&out.stdout), "hello\n");
    assert_eq!(String::from_utf8_lossy(&out.stderr), "bad\n");

    let children: Vec<_> = std::fs::read_dir(task_dir.join("children")).unwrap().collect();
    assert_eq!(children.len(), 1);
    let child_dir = children[0].as_ref().unwrap().path();
    assert_eq!(std::fs::read_to_string(child_dir.join("stdout")).unwrap(), "hello\n");
    assert_eq!(std::fs::read_to_string(child_dir.join("stderr")).unwrap(), "bad\n");
}

#[test]
fn forwards_stdin_to_child() {
    let home = tempfile::tempdir().unwrap();
    let task_dir = make_task(home.path());
    use std::io::Write;
    use std::process::{Stdio};
    let mut c = Command::new(bin())
        .args(["run", "--", "cat"])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_TASK_ID", &task_dir)
        .stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::piped())
        .spawn().unwrap();
    c.stdin.as_mut().unwrap().write_all(b"streamed\n").unwrap();
    drop(c.stdin.take());
    let out = c.wait_with_output().unwrap();
    assert!(out.status.success());
    assert_eq!(String::from_utf8_lossy(&out.stdout), "streamed\n");
}

#[test]
fn propagates_exit_code() {
    let home = tempfile::tempdir().unwrap();
    let task_dir = make_task(home.path());
    let out = Command::new(bin())
        .args(["run", "--", "bash", "-c", "exit 7"])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_TASK_ID", &task_dir)
        .output()
        .unwrap();
    assert_eq!(out.status.code(), Some(7));
}

#[test]
fn records_child_started_and_child_exit_in_parent_events() {
    let home = tempfile::tempdir().unwrap();
    let task_dir = make_task(home.path());
    let out = Command::new(bin())
        .args(["run", "--desc", "compute things", "--", "bash", "-c", "echo ok"])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_TASK_ID", &task_dir)
        .output()
        .unwrap();
    assert!(out.status.success());
    let evts = std::fs::read_to_string(task_dir.join("events.jsonl")).unwrap();
    assert!(evts.contains("\"child_started\""), "events: {evts}");
    assert!(evts.contains("\"child_exit\""), "events: {evts}");
    assert!(evts.contains("compute things"), "events: {evts}");
}
