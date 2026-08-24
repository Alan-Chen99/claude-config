use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("agent-tools/ should have a parent")
        .to_path_buf()
}

/// Kills the wrapper and the daemon holding its pipes however the test exits,
/// including on a failed assertion. `std::process::Child`'s own Drop does not
/// kill, and the daemon is not the wrapper's child at all, so without this a
/// single failing assertion would leave two processes behind — one of them
/// sleeping for five minutes.
struct Cleanup {
    wrapper: std::process::Child,
    daemon_pid_file: PathBuf,
}

impl Drop for Cleanup {
    fn drop(&mut self) {
        let _ = self.wrapper.kill();
        let _ = self.wrapper.wait();
        if let Ok(s) = std::fs::read_to_string(&self.daemon_pid_file) {
            if let Ok(pid) = s.trim().parse::<u32>() {
                let _ = Command::new("kill").arg(pid.to_string()).status();
            }
        }
    }
}

/// The one capture dir under `parent`, named for the wrapper pid.
fn capture_dir(parent: &Path) -> Option<PathBuf> {
    std::fs::read_dir(parent)
        .ok()?
        .flatten()
        .map(|e| e.path())
        .find(|p| p.is_dir())
}

/// A daemon outlives the wrapped child and writes a marker. The tool call that
/// first observes the marker must carry a report whose key is at least
/// `exited` — the agent must never see the consequence before the status.
#[test]
fn a_consequence_never_arrives_before_the_status_that_caused_it() {
    let home = tempfile::tempdir().unwrap();
    let parent = home.path().join(".claude/agent-tools/sid/toolu_run");
    let marker = home.path().join("marker.txt");
    let pid_file = home.path().join("daemon.pid");

    // Two detached jobs, both holding the inherited stdout and stderr:
    //
    // - `sleep 300` is the pipe holder. It is what makes this test
    //   discriminating. While it lives the wrapper cannot reach EOF, so an
    //   implementation that records the exit status only once the pipes drain
    //   has nothing to report for the whole life of the test. Its pid is `$!`
    //   of a simple command, so killing that pid really does release the pipe;
    //   a subshell pid could leave the fd held by a grandchild.
    // - the marker writer waits a second, so the marker — the consequence —
    //   cannot appear until well after the wrapped `bash` has exited and been
    //   reaped. It then exits on its own.
    let script = format!(
        "sleep 300 & echo $! > {pid}; (sleep 1; echo done > {marker}) & echo started",
        pid = pid_file.display(),
        marker = marker.display(),
    );
    let wrapper = Command::new(bin())
        .args(["run", "--desc", "detaching job", "bash", "-c", &script])
        .env("HOME", home.path())
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("AGENT_TOOLS_PARENT_DIR", &parent)
        .stdout(Stdio::null())
        .spawn()
        .unwrap();
    let _cleanup = Cleanup {
        wrapper,
        daemon_pid_file: pid_file,
    };

    // Wait for the consequence to become observable.
    let deadline = std::time::Instant::now() + std::time::Duration::from_secs(15);
    while !marker.exists() {
        assert!(
            std::time::Instant::now() < deadline,
            "marker never appeared"
        );
        std::thread::sleep(std::time::Duration::from_millis(50));
    }

    // The tool call that observes it must carry the status.
    let mut c = Command::new(bin())
        .arg("hook-post")
        .env("HOME", home.path())
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    c.stdin
        .as_mut()
        .unwrap()
        .write_all(
            serde_json::json!({
                "session_id": "sid",
                "tool_name": "Read",
                "tool_input": {"file_path": marker.to_string_lossy()},
                "tool_use_id": "toolu_read",
                "tool_response": {},
            })
            .to_string()
            .as_bytes(),
        )
        .unwrap();
    let out = c.wait_with_output().unwrap();
    let stdout = String::from_utf8_lossy(&out.stdout).into_owned();
    let stderr = String::from_utf8_lossy(&out.stderr).into_owned();
    assert!(out.status.success(), "hook-post failed; stderr: {stderr}");

    assert!(
        stdout.contains("detaching job"),
        "no report at all: {stdout}{stderr}"
    );
    // Name and key together in one fragment: a report about this child, whose
    // key names an exit status. `exited` while the wrapper is still draining,
    // `final` once it is gone — either says what the agent needed to know.
    assert!(
        stdout.contains("detaching job [exited(0)]") || stdout.contains("detaching job [final(0)]"),
        "consequence observed before the status: {stdout}"
    );

    // `drained_at` only ever goes from null to set, so finding it null now
    // proves it was null while the report above was produced: the status was
    // known before the pipes drained, which is the whole hazard. A test that
    // observed a drained wrapper would be passing on the easy case.
    let dir = capture_dir(&parent).expect("capture dir exists");
    let meta: serde_json::Value =
        serde_json::from_slice(&std::fs::read(dir.join("meta.json")).unwrap()).unwrap();
    assert!(
        meta["drained_at"].is_null(),
        "the daemon should still hold the pipes; meta: {meta}"
    );
}
