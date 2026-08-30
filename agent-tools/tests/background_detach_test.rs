//! `background::detach` through a real process, via the hidden
//! `background-probe` subcommand.
//!
//! Every property here is a property of processes — the parent blocking until
//! the child reports, the child leading a session of its own, a child that dies
//! silently, a descendant that must not hold the report pipe open, a bailing
//! child that must not reprint the parent's buffer. None of them is reachable
//! from a `#[cfg(test)]` module: `libtest` runs tests in a multi-threaded
//! process, which `detach` refuses to fork, and a test that forked anyway would
//! put a forked `libtest` child on the harness's own stdout. `run-core` exists
//! in this binary for the same reason.
//!
//! The refusal itself is the one part that needs no process, so it is a unit
//! test in `src/background.rs` — it is what `libtest` being multi-threaded is
//! good for.

use std::io::Read;
use std::path::PathBuf;
use std::process::{Command, ExitStatus, Stdio};
use std::time::{Duration, Instant};

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("agent-tools/ should have a parent")
        .to_path_buf()
}

/// Above `leak-check`'s own ten-second grandchild, so a leaked write end
/// reports as the leak it is rather than as a timeout, and far above every
/// other mode, which finish inside a second.
const DEADLINE: Duration = Duration::from_secs(15);

/// One probe run, bounded.
struct Probe {
    stdout: String,
    stderr: String,
    /// `None` when the deadline killed it — see `finished`.
    status: Option<ExitStatus>,
    elapsed: Duration,
}

impl Probe {
    /// The exit status, or a named failure.
    ///
    /// The mutations these tests exist to catch mostly present as a process
    /// that never exits — a parent still holding a write end waits on itself, a
    /// child that never reports leaves it there — and a blocking wait would
    /// turn each of those into a hung suite that names nothing. Nothing else
    /// bounds them either: CI runs `pytest tests/` and no `cargo test` job at
    /// all.
    fn finished(&self) -> ExitStatus {
        self.status.unwrap_or_else(|| {
            panic!(
                "the probe never exited within {DEADLINE:?}: nothing closed the report pipe, \
                 most likely because the parent kept a write end and is waiting on itself\n\
                 stdout so far: {}\nstderr so far: {}",
                self.stdout, self.stderr
            )
        })
    }

    fn field(&self, key: &str) -> String {
        self.stdout
            .split_whitespace()
            .find_map(|t| t.strip_prefix(&format!("{key}=")).map(str::to_string))
            .unwrap_or_else(|| panic!("no {key}= in probe output: {}", self.stdout))
    }
}

/// Run one probe mode under a deadline.
fn probe(mode: &str) -> Probe {
    let started = Instant::now();
    let mut child = Command::new(bin())
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .args(["background-probe", mode])
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("the probe subcommand should run");

    // Drained on threads rather than after the wait. `report-big`'s parent
    // writes 200 KB, well past the 64 KiB pipe buffer, so polling for an exit
    // without reading would block the very process being waited on.
    let mut out_pipe = child.stdout.take().expect("piped");
    let mut err_pipe = child.stderr.take().expect("piped");
    let out_reader = std::thread::spawn(move || {
        let mut v = Vec::new();
        let _ = out_pipe.read_to_end(&mut v);
        v
    });
    let err_reader = std::thread::spawn(move || {
        let mut v = Vec::new();
        let _ = err_pipe.read_to_end(&mut v);
        v
    });

    let deadline = Instant::now() + DEADLINE;
    let status = loop {
        match child.try_wait().expect("try_wait on the probe") {
            Some(s) => break Some(s),
            None if Instant::now() >= deadline => {
                // Killing the parent releases both pipes, so the readers below
                // finish instead of joining forever on a process that is gone.
                let _ = child.kill();
                let _ = child.wait();
                break None;
            }
            None => std::thread::sleep(Duration::from_millis(10)),
        }
    };
    let elapsed = started.elapsed();

    Probe {
        stdout: String::from_utf8_lossy(&out_reader.join().expect("stdout reader")).into_owned(),
        stderr: String::from_utf8_lossy(&err_reader.join().expect("stderr reader")).into_owned(),
        status,
        elapsed,
    }
}

/// The child reports half a second late, and the parent's line carries numbers
/// only the child knows. Both halves are needed: the numbers show the parent
/// read the report rather than inventing an answer, and the delay shows it
/// waited for it rather than returning first and printing nothing.
#[test]
fn the_parent_blocks_until_the_child_reports() {
    let p = probe("report-ok");
    assert!(p.finished().success(), "stdout: {}", p.stdout);
    assert!(
        p.stdout.starts_with("ok "),
        "the parent must learn a start succeeded: {}",
        p.stdout
    );
    assert!(
        p.field("pid").parse::<i32>().unwrap() > 0,
        "the line must carry what only the child could report: {}",
        p.stdout
    );
    assert!(
        p.elapsed >= Duration::from_millis(400),
        "the parent returned before the child reported: {:?}",
        p.elapsed
    );
}

/// Its own session is what survives the caller's process group being killed, so
/// the child must both lead a session and have left the caller's.
#[test]
fn the_detached_child_leads_a_session_of_its_own() {
    let p = probe("report-ok");
    assert!(p.finished().success(), "stdout: {}", p.stdout);

    let pid = p.field("pid");
    let sid = p.field("sid");
    assert_eq!(sid, pid, "the detached child must lead its own session");

    let parent_sid = p
        .stdout
        .lines()
        .find_map(|l| l.strip_prefix("parent-sid "))
        .expect("the parent reports its own session for comparison");
    assert_ne!(
        sid, parent_sid,
        "a child still in the caller's session dies with the caller's group"
    );
}

/// The reason travels the same channel the success line does, so a caller that
/// is still blocking hears it while it can still act on it.
#[test]
fn the_parent_learns_the_reason_a_start_failed() {
    let p = probe("report-err");
    assert!(!p.finished().success(), "a failed start must not exit 0");
    assert!(
        p.stdout.contains("Permission denied"),
        "the reason must reach the parent verbatim: {}",
        p.stdout
    );
}

/// An empty read is not consent. This also pins that the parent dropped its own
/// copy of the write end: holding one, it would wait here until the deadline
/// rather than reach EOF when the child exits.
#[test]
fn a_child_that_dies_without_reporting_is_a_failed_start() {
    let p = probe("silent");
    assert!(!p.finished().success(), "a silent death must not exit 0");
    assert!(
        p.stdout.contains("before saying whether it started"),
        "stdout: {}",
        p.stdout
    );
}

/// The write end is `O_CLOEXEC`, so an `exec`ed descendant of the child cannot
/// hold the parent's read open. The probe leaves a ten-second grandchild alive
/// across the child's exit: without the flag the parent reaches EOF only when
/// that grandchild dies, and this returns ten seconds late instead of at once.
#[test]
fn no_descendant_of_the_child_holds_the_report_pipe_open() {
    let p = probe("leak-check");
    let status = p.finished();
    let grandchild = p.field("grandchild");
    // Before asserting, so a failure still leaves nothing sleeping behind.
    let _ = Command::new("kill").arg(&grandchild).status();

    assert!(status.success(), "stdout: {}", p.stdout);
    assert_ne!(grandchild, "-1", "the probe must have a grandchild to test");
    assert!(
        p.elapsed < Duration::from_secs(5),
        "a descendant held the report pipe open: {:?}",
        p.elapsed
    );
}

/// A report past the pipe's 64 KiB buffer arrives whole, because the parent
/// drains as the child writes. A parent that read once into a fixed buffer
/// would report a truncated identity line as a successful start.
#[test]
fn a_report_larger_than_the_pipe_buffer_arrives_whole() {
    let p = probe("report-big");
    assert!(p.finished().success(), "stderr: {}", p.stderr);

    let line = p
        .stdout
        .lines()
        .next()
        .expect("the parent prints the reported line");
    assert_eq!(
        line.len(),
        "ok ".len() + 200_000,
        "the report was truncated at the pipe buffer"
    );
}

/// The child's stdio buffers are copies of the parent's, so a child that bails
/// out with `std::process::exit` flushes bytes the parent has not written yet
/// and the caller sees them twice. The probe leaves a partial line buffered
/// across the fork and then takes the failing path; `libc::_exit` is what keeps
/// the count at one.
#[test]
fn a_child_that_bails_out_does_not_reprint_what_the_parent_had_buffered() {
    let p = probe("dirty-stdout");
    assert!(!p.finished().success(), "the bail-out path must not exit 0");
    assert_eq!(
        p.stdout.matches("MARKER").count(),
        1,
        "the parent's buffered bytes were written twice: {}",
        p.stdout
    );
}
