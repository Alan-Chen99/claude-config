use std::path::PathBuf;
use std::process::Command;

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

fn make_task(home: &std::path::Path) -> PathBuf {
    let dir = home.join(".claude/agent-tools/sid/tuid");
    std::fs::create_dir_all(&dir).unwrap();
    dir
}

#[test]
fn errors_when_env_not_set() {
    let home = tempfile::tempdir().unwrap();
    let out = agent_tools()
        .args(["run", "--", "echo", "hi"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert!(!out.status.success());
    assert!(String::from_utf8_lossy(&out.stderr).contains("AGENT_TOOLS_PARENT_DIR"));
}

#[test]
fn captures_child_stdout_and_forwards() {
    let home = tempfile::tempdir().unwrap();
    let parent_dir = make_task(home.path());
    let out = agent_tools()
        .args([
            "run",
            "--",
            "bash",
            "-c",
            "echo hello; echo bad 1>&2; exit 0",
        ])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_PARENT_DIR", &parent_dir)
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    assert_eq!(String::from_utf8_lossy(&out.stdout), "hello\n");
    assert_eq!(String::from_utf8_lossy(&out.stderr), "bad\n");

    let children: Vec<_> = std::fs::read_dir(&parent_dir)
        .unwrap()
        .filter_map(|e| e.ok())
        .filter(|e| e.path().is_dir())
        .collect();
    assert_eq!(children.len(), 1);
    let child_dir = children[0].path();
    // Capture path is <parent>/<pid>/ — NO `children/` segment.
    assert_eq!(child_dir.parent().unwrap(), parent_dir.as_path());
    assert!(child_dir.join("meta.json").exists());
    assert_eq!(
        std::fs::read_to_string(child_dir.join("stdout")).unwrap(),
        "hello\n"
    );
    assert_eq!(
        std::fs::read_to_string(child_dir.join("stderr")).unwrap(),
        "bad\n"
    );
}

#[test]
fn lazily_creates_parent_dir_when_missing() {
    let home = tempfile::tempdir().unwrap();
    // Point AGENT_TOOLS_PARENT_DIR at a path that does NOT yet exist.
    let parent_dir = home.path().join(".claude/agent-tools/sid/tuid-fresh");
    assert!(
        !parent_dir.exists(),
        "precondition: parent dir must not exist"
    );
    let out = agent_tools()
        .args(["run", "--", "bash", "-c", "echo lazy"])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_PARENT_DIR", &parent_dir)
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    assert_eq!(String::from_utf8_lossy(&out.stdout), "lazy\n");
    assert!(
        parent_dir.exists(),
        "run should have lazily created the parent dir"
    );
    let children: Vec<_> = std::fs::read_dir(&parent_dir)
        .unwrap()
        .filter_map(|e| e.ok())
        .filter(|e| e.path().is_dir())
        .collect();
    assert_eq!(children.len(), 1);
    let child_dir = children[0].path();
    assert_eq!(child_dir.parent().unwrap(), parent_dir.as_path());
    assert_eq!(
        std::fs::read_to_string(child_dir.join("stdout")).unwrap(),
        "lazy\n"
    );
}

#[test]
fn forwards_stdin_to_child() {
    let home = tempfile::tempdir().unwrap();
    let parent_dir = make_task(home.path());
    use std::io::Write;
    use std::process::Stdio;
    let mut c = agent_tools()
        .args(["run", "--", "cat"])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_PARENT_DIR", &parent_dir)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    c.stdin.as_mut().unwrap().write_all(b"streamed\n").unwrap();
    drop(c.stdin.take());
    let out = c.wait_with_output().unwrap();
    assert!(out.status.success());
    assert_eq!(String::from_utf8_lossy(&out.stdout), "streamed\n");
}

#[test]
fn propagates_exit_code() {
    let home = tempfile::tempdir().unwrap();
    let parent_dir = make_task(home.path());
    let out = agent_tools()
        .args(["run", "--", "bash", "-c", "exit 7"])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_PARENT_DIR", &parent_dir)
        .output()
        .unwrap();
    assert_eq!(out.status.code(), Some(7));
}

#[test]
fn records_child_started_and_child_exit_in_parent_events() {
    let home = tempfile::tempdir().unwrap();
    let parent_dir = make_task(home.path());
    let out = agent_tools()
        .args([
            "run",
            "--desc",
            "compute things",
            "--",
            "bash",
            "-c",
            "echo ok",
        ])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_PARENT_DIR", &parent_dir)
        .output()
        .unwrap();
    assert!(out.status.success());
    let evts = std::fs::read_to_string(parent_dir.join("events.jsonl")).unwrap();
    assert!(evts.contains("\"child_started\""), "events: {evts}");
    assert!(evts.contains("\"child_exit\""), "events: {evts}");
    assert!(evts.contains("compute things"), "events: {evts}");
}
