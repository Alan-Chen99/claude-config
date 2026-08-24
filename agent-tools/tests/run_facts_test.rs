use std::path::PathBuf;
use std::process::Command;

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).parent().unwrap().to_path_buf()
}

fn read_meta(parent: &std::path::Path) -> serde_json::Value {
    let dir = std::fs::read_dir(parent)
        .unwrap()
        .flatten()
        .map(|e| e.path())
        .find(|p| p.is_dir())
        .expect("one capture dir");
    let bytes = std::fs::read(dir.join("meta.json")).expect("meta.json");
    serde_json::from_slice(&bytes).unwrap()
}

#[test]
fn reap_is_recorded_before_the_pipes_drain() {
    // The child exits immediately but leaves a descendant holding the
    // inherited stdout/stderr, so the wrapper cannot drain. The reap facts
    // must be on disk anyway.
    let home = tempfile::tempdir().unwrap();
    let parent = home.path().join("parent");
    let mut child = Command::new(bin())
        .args(["run", "--desc", "leaky", "bash", "-c", "sleep 30 & echo done"])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("AGENT_TOOLS_PARENT_DIR", &parent)
        .spawn()
        .unwrap();

    // Poll for the reap facts rather than waiting on the wrapper, which is
    // blocked on the descendant.
    let deadline = std::time::Instant::now() + std::time::Duration::from_secs(10);
    let meta = loop {
        assert!(std::time::Instant::now() < deadline, "reap never recorded");
        std::thread::sleep(std::time::Duration::from_millis(100));
        if parent.is_dir() {
            let m = read_meta(&parent);
            if !m["reaped"].is_null() {
                break m;
            }
        }
    };

    assert_eq!(meta["reaped"]["status"].as_i64(), Some(0));
    assert!(meta["drained_at"].is_null(), "must not claim drained while a writer holds the pipes");
    assert!(meta["wrapper_pid"].as_u64().is_some());
    let _ = child.kill();
    let _ = child.wait();
}

#[test]
fn clean_run_records_reap_and_drain() {
    let home = tempfile::tempdir().unwrap();
    let parent = home.path().join("parent");
    let out = Command::new(bin())
        .args(["run", "--desc", "clean", "bash", "-c", "echo hi; exit 7"])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("AGENT_TOOLS_PARENT_DIR", &parent)
        .output()
        .unwrap();
    assert_eq!(out.status.code(), Some(7), "exit code must pass through");
    let meta = read_meta(&parent);
    assert_eq!(meta["reaped"]["status"].as_i64(), Some(7));
    assert!(!meta["drained_at"].is_null());
}

#[test]
fn spawn_failure_is_recorded() {
    let home = tempfile::tempdir().unwrap();
    let parent = home.path().join("parent");
    let out = Command::new(bin())
        .args(["run", "--desc", "nope", "definitely-not-a-real-binary-xyz"])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("AGENT_TOOLS_PARENT_DIR", &parent)
        .output()
        .unwrap();
    assert_ne!(out.status.code(), Some(0));
    let meta = read_meta(&parent);
    assert!(meta["spawn_error"].as_str().is_some());
    assert!(meta["child_pid"].is_null());
}
