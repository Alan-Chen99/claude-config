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
    let dir = child_dir(parent)?;
    serde_json::from_slice(&std::fs::read(dir.join("meta.json")).ok()?).ok()
}

/// The one capture dir under `parent`, named for the wrapper pid.
fn child_dir(parent: &std::path::Path) -> Option<std::path::PathBuf> {
    std::fs::read_dir(parent)
        .ok()?
        .flatten()
        .map(|e| e.path())
        .find(|p| p.is_dir())
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

/// Bookkeeping is the wrapper's failure, not the child's. A `meta.json` that
/// cannot be written must not replace what the caller learns the child did:
/// the wrapper still exits with the child's code, and says what went wrong
/// through the event stream instead.
#[test]
fn a_failed_meta_write_never_replaces_the_child_exit_code() {
    let home = tempfile::tempdir().unwrap();
    let parent = home.path().join("parent");
    let release = home.path().join("release");

    // The child waits on a file rather than sleeping a fixed time, so the
    // window for breaking meta.json cannot close early on a loaded machine.
    let script = format!(
        "echo started; while [ ! -e {} ]; do sleep 0.02; done; exit 7",
        release.display()
    );
    let wrapper = Command::new(bin())
        .args(["run", "--desc", "unwritable", "bash", "-c", &script])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("AGENT_TOOLS_PARENT_DIR", &parent)
        .stdout(std::process::Stdio::null())
        .spawn()
        .unwrap();
    let mut cleanup = Cleanup {
        wrapper,
        daemon_pid_file: home.path().join("no-daemon.pid"),
    };

    // Wait until the child pid is on disk, so the writes broken below are the
    // reap and the drain rather than the ones that precede them.
    let deadline = std::time::Instant::now() + std::time::Duration::from_secs(10);
    loop {
        assert!(std::time::Instant::now() < deadline, "child pid never recorded");
        match read_meta(&parent) {
            Some(m) if !m["child_pid"].is_null() => break,
            _ => std::thread::sleep(std::time::Duration::from_millis(20)),
        }
    }

    // Replace meta.json with a directory: `write_meta` renames its tmp file
    // onto that path, and rename(2) onto a directory fails with EISDIR. A
    // chmod would not do it — these tests can run as root, which writes anyway.
    let meta_path = child_dir(&parent).expect("capture dir exists").join("meta.json");
    std::fs::remove_file(&meta_path).unwrap();
    std::fs::create_dir(&meta_path).unwrap();

    std::fs::write(&release, b"").unwrap();
    let status = cleanup.wrapper.wait().unwrap();

    assert_eq!(status.code(), Some(7), "the child's exit code, not the wrapper's");

    let evts = std::fs::read_to_string(parent.join("events.jsonl")).unwrap();
    let failed_facts: Vec<String> = evts
        .lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| serde_json::from_str::<serde_json::Value>(l).expect("one event per line"))
        .filter(|e| e["kind"] == "meta_write_failed")
        .map(|e| e["data"]["fact"].as_str().unwrap_or_default().to_string())
        .collect();

    // The drain write is the one that used to abort the run; the reap write
    // fails the same way for the same reason. Neither may be silent.
    assert!(failed_facts.contains(&"drained_at".to_string()), "events: {evts}");
    assert!(failed_facts.contains(&"reaped".to_string()), "events: {evts}");
}

#[test]
fn the_merge_condition_is_recorded_beside_the_capture() {
    let home = tempfile::tempdir().unwrap();
    let parent = home.path().join("parent");
    std::fs::create_dir_all(&parent).unwrap();

    let out = std::process::Command::new(bin())
        .args(["run", "--desc", "probe", "--", "bash", "-c", "echo hi"])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("AGENT_TOOLS_PARENT_DIR", &parent)
        .env("HOME", home.path())
        .output()
        .unwrap();
    assert_eq!(out.status.code(), Some(0));

    let meta = read_meta(&parent).expect("meta.json written");
    assert!(
        meta.get("merge").is_some(),
        "the merge decision is recorded per capture: {meta}"
    );
}

#[test]
fn a_close_that_stderr_could_not_carry_is_still_in_the_record() {
    let home = tempfile::tempdir().unwrap();
    let parent = home.path().join("parent");
    std::fs::create_dir_all(&parent).unwrap();

    // `2>&1` makes both of the wrapper's descriptors the same pipe, which the
    // merge rule admits, so the notice `capture::state` writes goes into the
    // pipe `head` just dropped and no reader ever sees it. Same for a split
    // run whose stderr is the stream that closed. The record is the only place
    // either can appear, which is why the spec asks for stderr *and* the status.
    let script = format!(
        "{} run --desc probe -- bash -c 'seq 1 100000' 2>&1 | head -3",
        bin()
    );
    let out = std::process::Command::new("bash")
        .args(["-c", &script])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("AGENT_TOOLS_PARENT_DIR", &parent)
        .env("HOME", home.path())
        .output()
        .unwrap();
    assert_eq!(String::from_utf8_lossy(&out.stdout), "1\n2\n3\n");

    let meta = read_meta(&parent).expect("meta.json written");
    assert_eq!(
        meta.get("forward_closed").and_then(|v| v.as_bool()),
        Some(true),
        "the record carries what stderr could not: {meta}"
    );
}

#[test]
fn a_capped_drain_is_in_the_record() {
    let home = tempfile::tempdir().unwrap();
    let parent = home.path().join("parent");
    std::fs::create_dir_all(&parent).unwrap();

    // 64 KiB rather than the 256 MiB default: the fact under test is that the
    // bound reaches the record, not what the production number is, and no test
    // can afford to drive a quarter of a gigabyte to find out.
    let script = format!(
        "{} run --desc probe --drain-cap-bytes 65536 -- bash -c 'seq 1 100000' 2>&1 | head -3",
        bin()
    );
    let out = std::process::Command::new("bash")
        .args(["-c", &script])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("AGENT_TOOLS_PARENT_DIR", &parent)
        .env("HOME", home.path())
        .output()
        .unwrap();
    assert_eq!(String::from_utf8_lossy(&out.stdout), "1\n2\n3\n");

    let meta = read_meta(&parent).expect("meta.json written");
    assert_eq!(
        meta.get("drain_capped").and_then(|v| v.as_bool()),
        Some(true),
        "the bound reached the record: {meta}"
    );
}

#[test]
fn a_capture_that_never_opened_is_in_the_record() {
    let home = tempfile::tempdir().unwrap();
    let parent = home.path().join("parent");
    std::fs::create_dir_all(&parent).unwrap();

    // `exec` hands the wrapper the shell's own pid, and the capture dir is
    // named for it, so the directories that fail the tee's open with EISDIR are
    // in place before there is anything to race. Both names, since the merge
    // rule decides which one the tee reaches for.
    let script = format!(
        "mkdir -p '{p}'/$$/stdout '{p}'/$$/output; \
         exec {bin} run --desc probe -- bash -c 'echo hi'",
        p = parent.display(),
        bin = bin()
    );
    let out = std::process::Command::new("bash")
        .args(["-c", &script])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("AGENT_TOOLS_PARENT_DIR", &parent)
        .env("HOME", home.path())
        .output()
        .unwrap();
    // The wrapper's disk is not the child's fault: the command ran, its bytes
    // reached the caller, and its exit code is the one bare would have given.
    assert_eq!(out.status.code(), Some(0));
    assert_eq!(String::from_utf8_lossy(&out.stdout), "hi\n");

    let meta = read_meta(&parent).expect("meta.json written");
    assert!(
        meta.get("capture_error")
            .and_then(|v| v.as_str())
            .is_some_and(|e| e.contains("Is a directory")),
        "the capture that never opened is in the record: {meta}"
    );
}
