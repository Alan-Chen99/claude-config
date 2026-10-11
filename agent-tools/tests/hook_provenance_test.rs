//! The launch record, driven through the real binary. A resume keeps the
//! session id and continues the transcript from a new process its launcher
//! configured afresh, so the record is kept once per process, not once per
//! session.

use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::time::{Duration, SystemTime};

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("agent-tools/ should have a parent")
        .to_path_buf()
}

/// A live process standing in for a Claude Code pid, killed on drop.
struct StandIn(Child);

impl StandIn {
    fn spawn() -> Self {
        StandIn(Command::new("sleep").arg("60").spawn().unwrap())
    }

    fn pid(&self) -> u32 {
        self.0.id()
    }
}

impl Drop for StandIn {
    fn drop(&mut self) {
        let _ = self.0.kill();
        let _ = self.0.wait();
    }
}

/// One hook invocation, from a cleared environment: this suite runs inside
/// sessions whose own `CLAUDE_PID` and `CLAUDE_SH_*` would otherwise decide
/// what the record says.
fn record(home: &Path, claude_pid: Option<u32>, launchers: &str, session: &str) -> String {
    let mut cmd = Command::new(bin());
    cmd.arg("hook-provenance")
        .env_clear()
        .env("PATH", std::env::var("PATH").unwrap())
        .env("HOME", home)
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("CLAUDE_SH_LAUNCHERS", launchers)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    if let Some(pid) = claude_pid {
        cmd.env("CLAUDE_PID", pid.to_string());
    }
    let mut child = cmd.spawn().unwrap();
    let payload = format!(
        r#"{{"session_id":"{session}","hook_event_name":"Stop","cwd":"{}"}}"#,
        home.display()
    );
    child
        .stdin
        .as_mut()
        .unwrap()
        .write_all(payload.as_bytes())
        .unwrap();
    let out = child.wait_with_output().unwrap();
    assert!(
        out.status.success(),
        "hook exited {:?}: {}",
        out.status,
        String::from_utf8_lossy(&out.stderr)
    );
    String::from_utf8(out.stdout).unwrap()
}

fn process_line(pid: u32) -> String {
    format!("\nprocess:  pid {pid}, started ")
}

#[test]
fn a_resumed_process_records_its_own_launch_and_neither_process_repeats() {
    let home = tempfile::tempdir().unwrap();
    let launcher = home.path().join("claude.sh");
    fs::write(&launcher, "#!/bin/sh\n").unwrap();
    let launcher = launcher.to_str().unwrap();
    let (first, resumed) = (StandIn::spawn(), StandIn::spawn());

    let block = record(home.path(), Some(first.pid()), launcher, "sid-resume");
    assert!(block.starts_with("<launch-provenance v2>\n"), "{block}");
    assert!(block.contains(&process_line(first.pid())), "{block}");
    assert_eq!(
        record(home.path(), Some(first.pid()), launcher, "sid-resume"),
        "",
        "a later event of the same process must not repeat the record"
    );

    let again = record(home.path(), Some(resumed.pid()), launcher, "sid-resume");
    assert!(again.contains(&process_line(resumed.pid())), "{again}");
    assert_eq!(
        record(home.path(), Some(resumed.pid()), launcher, "sid-resume"),
        ""
    );
}

#[test]
fn a_launcher_modified_after_its_process_started_is_flagged_and_an_older_one_is_not() {
    let home = tempfile::tempdir().unwrap();
    let process = StandIn::spawn();
    let untouched = home.path().join("kimi.sh");
    let edited = home.path().join("claude.sh");
    // Explicit mtimes an hour either side, not sleeps: the start time comes
    // from boot time in whole seconds.
    let hour = Duration::from_secs(3600);
    for (path, mtime) in [
        (&untouched, SystemTime::now() - hour),
        (&edited, SystemTime::now() + hour),
    ] {
        fs::write(path, "#!/bin/sh\n").unwrap();
        fs::File::options()
            .write(true)
            .open(path)
            .unwrap()
            .set_modified(mtime)
            .unwrap();
    }

    let chain = format!("{}:{}", untouched.display(), edited.display());
    let block = record(home.path(), Some(process.pid()), &chain, "sid-mtime");
    let entry = |n: usize| {
        block
            .lines()
            .find(|l| l.starts_with(&format!("  {n}. ")))
            .unwrap_or_else(|| panic!("no launcher {n} in {block}"))
            .to_string()
    };
    assert!(!entry(1).contains("modified after"), "{block}");
    assert!(
        entry(2).ends_with("(modified after this process started: its text below may not be what ran)"),
        "{block}"
    );
}

#[test]
fn without_a_claude_pid_the_record_says_so_and_is_kept_once_per_session() {
    let home = tempfile::tempdir().unwrap();
    let block = record(home.path(), None, "", "sid-nopid");
    assert!(block.contains("\nprocess:  unknown (see errors)\n"), "{block}");
    assert!(
        block.contains("  - process: CLAUDE_PID: "),
        "the errors section names what was missing: {block}"
    );
    assert_eq!(record(home.path(), None, "", "sid-nopid"), "");
}
