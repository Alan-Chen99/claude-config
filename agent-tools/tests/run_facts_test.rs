use std::path::PathBuf;
use std::process::Command;

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).parent().unwrap().to_path_buf()
}

/// Read the single capture dir's meta.json, if the wrapper has written it yet.
/// `run` creates the parent dir before the capture dir, so a poll can land in
/// the window where the parent exists and nothing is inside it; that is a
/// "not yet", not a failure.
fn read_meta(parent: &std::path::Path) -> Option<serde_json::Value> {
    let dir = std::fs::read_dir(parent)
        .ok()?
        .flatten()
        .map(|e| e.path())
        .find(|p| p.is_dir())?;
    serde_json::from_slice(&std::fs::read(dir.join("meta.json")).ok()?).ok()
}

/// Kills the wrapper and the detached daemon however the test exits, including
/// on panic. `std::process::Child`'s own Drop does not kill the process, so an
/// assertion failure would otherwise leave both running.
struct Cleanup {
    wrapper: std::process::Child,
    daemon_pid_file: std::path::PathBuf,
}

impl Drop for Cleanup {
    fn drop(&mut self) {
        let _ = self.wrapper.kill();
        let _ = self.wrapper.wait();
        if let Ok(s) = std::fs::read_to_string(&self.daemon_pid_file) {
            if let Ok(pid) = s.trim().parse::<u32>() {
                let _ = std::process::Command::new("kill").arg(pid.to_string()).status();
            }
        }
    }
}

#[test]
fn reap_is_recorded_before_the_pipes_drain() {
    // The child exits immediately but leaves a descendant holding the
    // inherited stdout/stderr, so the wrapper cannot drain. The reap facts
    // must be on disk anyway.
    let home = tempfile::tempdir().unwrap();
    let parent = home.path().join("parent");
    let pid_file = home.path().join("daemon.pid");
    let wrapper = Command::new(bin())
        .args([
            "run", "--desc", "leaky", "bash", "-c",
            &format!("sleep 30 & echo $! > {}; echo done", pid_file.display()),
        ])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("AGENT_TOOLS_PARENT_DIR", &parent)
        .spawn()
        .unwrap();
    let _cleanup = Cleanup { wrapper, daemon_pid_file: pid_file };

    // Poll for the reap facts rather than waiting on the wrapper, which is
    // blocked on the descendant.
    let deadline = std::time::Instant::now() + std::time::Duration::from_secs(10);
    let meta = loop {
        assert!(std::time::Instant::now() < deadline, "reap never recorded");
        std::thread::sleep(std::time::Duration::from_millis(50));
        if let Some(m) = read_meta(&parent) {
            if !m["reaped"].is_null() {
                break m;
            }
        }
    };

    assert_eq!(meta["reaped"]["status"].as_i64(), Some(0));
    assert!(meta["drained_at"].is_null(), "must not claim drained while a writer holds the pipes");
    assert!(meta["wrapper_pid"].as_u64().is_some());
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
    let meta = read_meta(&parent).expect("meta.json written");
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
    let meta = read_meta(&parent).expect("meta.json written");
    assert!(meta["spawn_error"].as_str().is_some());
    assert!(meta["child_pid"].is_null());
}
