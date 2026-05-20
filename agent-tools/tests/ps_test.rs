use std::path::{Path, PathBuf};
use std::process::Command;

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

/// Seed a capture at `<home>/.claude/agent-tools/<session>/[<agent>/]<tuid>/<pid>/`.
/// Writes meta.json, stdout, stderr. Returns the capture (pid) directory.
fn seed_capture(
    home: &Path,
    session: &str,
    agent: Option<&str>,
    tuid: &str,
    pid: u32,
    desc: Option<&str>,
    exit: Option<i32>,
    stdout: &str,
) -> PathBuf {
    let mut dir = home.join(".claude/agent-tools").join(session);
    if let Some(a) = agent {
        dir.push(a);
    }
    dir.push(tuid);
    dir.push(pid.to_string());
    std::fs::create_dir_all(&dir).unwrap();
    let meta = serde_json::json!({
        "child_id": pid,
        "desc": desc,
        "command": ["echo", desc.unwrap_or("anon")],
        "started_at": "2026-05-17T10:00:00Z",
        "ended_at": exit.map(|_| "2026-05-17T10:00:05Z"),
        "exit_code": exit,
    });
    std::fs::write(
        dir.join("meta.json"),
        serde_json::to_string_pretty(&meta).unwrap(),
    )
    .unwrap();
    std::fs::write(dir.join("stdout"), stdout).unwrap();
    std::fs::write(dir.join("stderr"), "").unwrap();
    dir
}

/// Write an events.jsonl line at `<home>/.claude/agent-tools/<session>/[<agent>/]<tuid>/events.jsonl`.
fn append_event(home: &Path, session: &str, agent: Option<&str>, tuid: &str, line: &str) {
    let mut dir = home.join(".claude/agent-tools").join(session);
    if let Some(a) = agent {
        dir.push(a);
    }
    dir.push(tuid);
    std::fs::create_dir_all(&dir).unwrap();
    let path = dir.join("events.jsonl");
    let prior = std::fs::read_to_string(&path).unwrap_or_default();
    std::fs::write(&path, format!("{prior}{line}\n")).unwrap();
}

#[test]
fn no_state_on_disk_prints_session_and_marker() {
    let home = tempfile::tempdir().unwrap();
    let out = Command::new(bin())
        .args(["ps", "--session-id", "sid-fresh"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("session: sid-fresh"), "{s}");
    assert!(s.contains("(no state on disk)"), "{s}");
}

#[test]
fn main_thread_two_captures_under_one_tool_use_id() {
    let home = tempfile::tempdir().unwrap();
    seed_capture(
        home.path(),
        "sid",
        None,
        "tuid1",
        11111,
        Some("probe-a"),
        Some(0),
        "out-a\n",
    );
    seed_capture(
        home.path(),
        "sid",
        None,
        "tuid1",
        22222,
        Some("probe-b"),
        Some(1),
        "out-b\n",
    );

    let out = Command::new(bin())
        .args(["ps", "--session-id", "sid"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("session: sid"), "{s}");
    assert!(s.contains("agent: _main"), "{s}");
    assert!(s.contains("tool-use tuid1 (2 captures)"), "{s}");
    assert!(s.contains("pid 11111"), "{s}");
    assert!(s.contains("pid 22222"), "{s}");
    assert!(s.contains("desc:    probe-a"), "{s}");
    assert!(s.contains("desc:    probe-b"), "{s}");
}

#[test]
fn subagent_capture_listed_under_subagent_header() {
    let home = tempfile::tempdir().unwrap();
    seed_capture(
        home.path(),
        "sid",
        Some("agent-x"),
        "tuid-sub",
        33333,
        Some("sub-probe"),
        Some(0),
        "sub-out\n",
    );

    let out = Command::new(bin())
        .args(["ps", "--session-id", "sid"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("agent: agent-x"), "{s}");
    assert!(s.contains("tool-use tuid-sub (1 capture)"), "{s}");
    assert!(s.contains("pid 33333"), "{s}");
    assert!(!s.contains("agent: _main"), "leak: {s}");
}

#[test]
fn task_filter_limits_to_one_tool_use_id() {
    let home = tempfile::tempdir().unwrap();
    seed_capture(
        home.path(),
        "sid",
        None,
        "tuid-keep",
        44444,
        Some("keep"),
        Some(0),
        "k\n",
    );
    seed_capture(
        home.path(),
        "sid",
        None,
        "tuid-drop",
        55555,
        Some("drop"),
        Some(0),
        "d\n",
    );

    let out = Command::new(bin())
        .args(["ps", "--session-id", "sid", "--task", "tuid-keep"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("tuid-keep"), "{s}");
    assert!(!s.contains("tuid-drop"), "{s}");
    assert!(!s.contains("pid 55555"), "{s}");
}

#[test]
fn events_appear_in_chronological_order() {
    let home = tempfile::tempdir().unwrap();
    seed_capture(
        home.path(),
        "sid",
        None,
        "tuid-evt",
        66666,
        Some("evt"),
        Some(0),
        "e\n",
    );

    // Out-of-order writes: middle, then earliest, then latest.
    append_event(
        home.path(),
        "sid",
        None,
        "tuid-evt",
        r#"{"ts":"2026-05-17T10:00:02Z","kind":"middle","data":{"n":2}}"#,
    );
    append_event(
        home.path(),
        "sid",
        None,
        "tuid-evt",
        r#"{"ts":"2026-05-17T10:00:01Z","kind":"first","data":{"n":1}}"#,
    );
    append_event(
        home.path(),
        "sid",
        None,
        "tuid-evt",
        r#"{"ts":"2026-05-17T10:00:03Z","kind":"last","data":{"n":3}}"#,
    );

    let out = Command::new(bin())
        .args(["ps", "--session-id", "sid"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("events (chronological, all captures):"), "{s}");
    let pos_first = s.find("first").expect("first event missing");
    let pos_middle = s.find("middle").expect("middle event missing");
    let pos_last = s.find("last").expect("last event missing");
    assert!(pos_first < pos_middle, "ordering wrong: {s}");
    assert!(pos_middle < pos_last, "ordering wrong: {s}");
}
