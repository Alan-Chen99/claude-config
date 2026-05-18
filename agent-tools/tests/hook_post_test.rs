use std::io::Write;
use std::process::{Command, Stdio};

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn run_post(home: &std::path::Path, body: serde_json::Value) -> (std::process::ExitStatus, String, String) {
    let mut c = Command::new(bin())
        .arg("hook-post")
        .env("HOME", home)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    c.stdin.as_mut().unwrap().write_all(body.to_string().as_bytes()).unwrap();
    let out = c.wait_with_output().unwrap();
    (out.status, String::from_utf8_lossy(&out.stdout).into_owned(), String::from_utf8_lossy(&out.stderr).into_owned())
}

fn seed_task(home: &std::path::Path, session: &str, task: &str) {
    let dir = home.join(format!(".claude/agent-tools/{session}/{task}"));
    std::fs::create_dir_all(&dir).unwrap();
    std::fs::write(dir.join("meta.json"), r#"{"kind":"task","session_id":"sid","agent_id":null,"task_id":"tuid","tool":"Bash","tool_use_id":"tuid","desc":null,"cwd":"/tmp","pid":1,"started_at":null,"ended_at":null,"exit_code":null,"silence_threshold_ms":30000}"#).unwrap();
}

#[test]
fn no_backgrounding_emits_no_additional_context() {
    let home = tempfile::tempdir().unwrap();
    seed_task(home.path(), "sid", "tuid");
    let (status, stdout, stderr) = run_post(home.path(), serde_json::json!({
        "session_id": "sid",
        "tool_name": "Bash",
        "tool_input": {"command": "echo hi"},
        "tool_use_id": "tuid",
        "tool_response": {}
    }));
    assert!(status.success(), "stderr: {stderr}");
    if !stdout.trim().is_empty() {
        let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
        assert!(v.get("hookSpecificOutput")
            .and_then(|h| h.get("additionalContext"))
            .is_none(), "should not emit additionalContext, got {stdout}");
    }
}

#[test]
fn assistant_auto_background_emits_context() {
    let home = tempfile::tempdir().unwrap();
    seed_task(home.path(), "sid", "tuid");
    let (status, stdout, _stderr) = run_post(home.path(), serde_json::json!({
        "session_id": "sid",
        "tool_name": "Bash",
        "tool_input": {"command": "long-running"},
        "tool_use_id": "tuid",
        "tool_response": {"backgroundTaskId": "bt-9", "assistantAutoBackgrounded": true}
    }));
    assert!(status.success());
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    let ctx = v["hookSpecificOutput"]["additionalContext"].as_str().unwrap();
    assert!(ctx.contains("KAIROS") || ctx.contains("auto"), "context: {ctx}");
    assert!(ctx.contains("bt-9"), "context: {ctx}");

    let evts = std::fs::read_to_string(home.path().join(".claude/agent-tools/sid/tuid/events.jsonl")).unwrap();
    assert!(evts.contains("\"backgrounded\""), "events: {evts}");
}

#[test]
fn user_backgrounding_emits_context() {
    let home = tempfile::tempdir().unwrap();
    seed_task(home.path(), "sid", "tuid");
    let (status, stdout, _stderr) = run_post(home.path(), serde_json::json!({
        "session_id": "sid",
        "tool_name": "Bash",
        "tool_input": {"command": "long-running"},
        "tool_use_id": "tuid",
        "tool_response": {"backgroundTaskId": "bt-1", "backgroundedByUser": true}
    }));
    assert!(status.success());
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    let ctx = v["hookSpecificOutput"]["additionalContext"].as_str().unwrap();
    assert!(ctx.contains("Ctrl+B") || ctx.contains("user"), "context: {ctx}");
}

#[test]
fn explicit_run_in_background_is_not_reported_as_timeout() {
    // When tool_input.run_in_background == true, BashTool returns a
    // backgroundTaskId immediately with neither assistantAutoBackgrounded nor
    // backgroundedByUser set (BashTool.tsx:989-1000). The post-hook must
    // recognize this as an intentional background, not a timeout.
    let home = tempfile::tempdir().unwrap();
    seed_task(home.path(), "sid", "tuid");
    let (status, stdout, _stderr) = run_post(home.path(), serde_json::json!({
        "session_id": "sid",
        "tool_name": "Bash",
        "tool_input": {"command": "long-running", "run_in_background": true},
        "tool_use_id": "tuid",
        "tool_response": {"backgroundTaskId": "bt-rib"}
    }));
    assert!(status.success());
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    let ctx = v["hookSpecificOutput"]["additionalContext"].as_str().unwrap();
    assert!(!ctx.contains("timeout"),
        "should NOT report timeout for explicit run_in_background: {ctx}");
    assert!(ctx.contains("bt-rib"), "context: {ctx}");

    let evts = std::fs::read_to_string(
        home.path().join(".claude/agent-tools/sid/tuid/events.jsonl")
    ).unwrap();
    assert!(!evts.contains("\"cause\":\"timeout\""),
        "should not log timeout cause for explicit background: {evts}");
}

#[test]
fn timeout_backgrounding_emits_context_with_limit() {
    let home = tempfile::tempdir().unwrap();
    seed_task(home.path(), "sid", "tuid");
    let (status, stdout, _stderr) = run_post(home.path(), serde_json::json!({
        "session_id": "sid",
        "tool_name": "Bash",
        "tool_input": {"command": "sleep 9999", "timeout": 5000},
        "tool_use_id": "tuid",
        "tool_response": {"backgroundTaskId": "bt-2"}
    }));
    assert!(status.success());
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    let ctx = v["hookSpecificOutput"]["additionalContext"].as_str().unwrap();
    assert!(ctx.contains("timeout"), "context: {ctx}");
    assert!(ctx.contains("5000"), "context: {ctx}");
}
