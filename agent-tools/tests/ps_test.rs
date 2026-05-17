use std::process::Command;

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn seed(home: &std::path::Path, session: &str, agent: Option<&str>, task: &str, pid: u32, exit: Option<i32>) -> std::path::PathBuf {
    let mut dir = home.join(".claude/agent-tools").join(session);
    if let Some(a) = agent { dir.push(a); }
    dir.push(task);
    std::fs::create_dir_all(dir.join("children")).unwrap();
    let meta = serde_json::json!({
        "kind":"task","session_id":session,
        "agent_id": agent,
        "task_id":task,"tool":"Bash","tool_use_id":task,
        "desc":format!("task {task}"),"cwd":"/tmp",
        "pid":pid,"started_at":"2026-05-17T10:00:00Z",
        "ended_at": exit.map(|_| "2026-05-17T10:00:05Z"),
        "exit_code": exit,
        "silence_threshold_ms":30000
    });
    std::fs::write(dir.join("meta.json"), serde_json::to_string_pretty(&meta).unwrap()).unwrap();
    std::fs::write(dir.join("command.sh"), format!("echo {task}")).unwrap();
    std::fs::write(dir.join("stdout"), format!("hello from {task}\n")).unwrap();
    std::fs::write(dir.join("stderr"), "").unwrap();
    std::fs::write(dir.join("events.jsonl"), format!(
        r#"{{"ts":"2026-05-17T10:00:00Z","kind":"task_started","data":{{"pid":{pid}}}}}
"#)).unwrap();
    dir
}

#[test]
fn default_lists_session_tasks_resolved_from_env() {
    let home = tempfile::tempdir().unwrap();
    let dir = seed(home.path(), "sid", None, "tuid1", 99999, None);
    let _ = seed(home.path(), "sid", None, "tuid2", 99999, Some(0));

    let out = Command::new(bin())
        .arg("ps")
        .env("HOME", home.path())
        .env("AGENT_TOOLS_TASK_ID", &dir)
        .output()
        .unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("tuid1"), "{s}");
    assert!(s.contains("tuid2"), "{s}");
    assert!(s.contains("session: sid"), "{s}");
}

#[test]
fn task_filter_only_shows_one_task() {
    let home = tempfile::tempdir().unwrap();
    let dir = seed(home.path(), "sid", None, "tuid1", 99999, None);
    let _ = seed(home.path(), "sid", None, "tuid2", 99999, Some(0));

    let out = Command::new(bin())
        .args(["ps", "--task", "tuid2"])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_TASK_ID", &dir)
        .output()
        .unwrap();
    assert!(out.status.success());
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("tuid2"));
    assert!(!s.contains("tuid1"));
}

#[test]
fn cross_session_with_session_id_flag() {
    let home = tempfile::tempdir().unwrap();
    let dir = seed(home.path(), "sid-a", None, "tuid", 99999, None);
    let _ = seed(home.path(), "sid-b", None, "tuid-b", 99999, None);
    let out = Command::new(bin())
        .args(["ps", "--session-id", "sid-b"])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_TASK_ID", &dir)
        .output()
        .unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("tuid-b"));
    assert!(!s.contains("session: sid-a"), "leak: {s}");
    assert!(!s.contains("task tuid "), "leak: {s}");
}

#[test]
fn live_marker_uses_pid_kill_zero() {
    let home = tempfile::tempdir().unwrap();
    let my_pid = std::process::id();
    let dir = seed(home.path(), "sid", None, "live-task", my_pid, None);
    let out = Command::new(bin())
        .arg("ps")
        .env("HOME", home.path())
        .env("AGENT_TOOLS_TASK_ID", &dir)
        .output()
        .unwrap();
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("[running]") || s.contains("running"), "{s}");
}

#[test]
fn ended_meta_shows_exit_code() {
    let home = tempfile::tempdir().unwrap();
    let dir = seed(home.path(), "sid", None, "done", 1, Some(42));
    let out = Command::new(bin())
        .arg("ps")
        .env("HOME", home.path())
        .env("AGENT_TOOLS_TASK_ID", &dir)
        .output()
        .unwrap();
    assert!(out.status.success());
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("42"), "{s}");
}
