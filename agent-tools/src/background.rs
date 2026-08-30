//! Fork before any tokio runtime exists, so a wrapper can outlive the caller
//! that started it and still tell that caller whether it started.
//!
//! A tokio runtime does not survive `fork`: its worker threads do not cross,
//! and the child would hold a runtime whose executor is gone. So the fork
//! happens at the top of the process, before a runtime is built, and everything
//! asynchronous happens after `detach` has already answered.
//!
//! Three rules bind the child's side of that fork, and every one of them is
//! easy to break by accident:
//!
//! - **Terminate with `libc::_exit`, never `std::process::exit`, in a child
//!   that bails out before it has taken over.** The stdio buffers it holds are
//!   *copies* of the parent's, and `exit` flushes them — writing a second time
//!   whatever the parent had buffered and not yet written — and runs `atexit`
//!   handlers registered before the fork against state only the parent still
//!   owns. Once a child has taken over it is an ordinary process and ends like
//!   one. `probe`'s `dirty-stdout` mode is what holds this rule up.
//! - **Run ordinary code only because `detach` refuses to fork a process with
//!   more than one thread.** See the SAFETY note there.
//! - **Take the child off the caller's descriptors before doing any work.** It
//!   inherits fd 1 and 2 as the very open file description the parent is
//!   using — measured: parent and detached child both showing fd 1 on one
//!   pipe — so a caller that reads to EOF, which is Claude Code's Bash tool,
//!   `Command::output` and `$(...)` alike, waits on the child rather than on
//!   the parent that already answered it. Skip the redirect and a backgrounded
//!   run returns no sooner than a foreground one, while every test here still
//!   passes.

use anyhow::{anyhow, Result};
use std::io::Read;
use std::os::fd::OwnedFd;

/// Which side of the fork the caller is on.
pub enum Detached {
    /// The original process. Carries what the child reported about starting:
    /// the line to print, or the reason nothing started.
    ///
    /// Nothing here reaps the child, and nothing needs to: on the success path
    /// the child is still running and outlives this process, so it is orphaned
    /// and the init process reaps it. On the failure path the child has already
    /// exited and is a zombie for as long as this process takes to print one
    /// line and exit — after which it is orphaned and reaped like any other. A
    /// caller that keeps running instead of exiting owes the child a `wait`.
    Parent(Result<String>),
    /// The detached process, in a session of its own. It owns the one channel
    /// back to the caller and must use it exactly once.
    Child(Reporter),
}

/// The detached child's single message to the caller that is still blocking on
/// it. Consuming `self` is the type saying what the protocol says: one report,
/// then the pipe closes and the caller stops waiting.
pub struct Reporter {
    fd: OwnedFd,
}

impl Reporter {
    /// The child started. `line` is what the caller prints.
    pub fn started(self, line: &str) {
        self.write(&format!("ok\n{line}"));
        // Dropping closes the write end, which is what ends the parent's read.
        // The child keeps running past this point — that is the whole design —
        // so the close, not this process's exit, is what unblocks the caller.
    }

    /// Nothing started, and this is why. Does not return: a process that failed
    /// to start a child has nothing left to do, and continuing would leave a
    /// detached wrapper supervising a child that does not exist.
    pub fn failed(self, e: &anyhow::Error) -> ! {
        self.write(&format!("err\n{e:#}"));
        // Explicit, so the order reads as the protocol it is: the report is
        // whole and the pipe is closed before this process stops existing.
        drop(self);
        // SAFETY: `_exit` is always safe to call; it is `unsafe` only as a raw
        // FFI declaration. `std::process::exit` is what would be wrong here —
        // see the module doc's rule on the child's side of the fork.
        unsafe { libc::_exit(1) }
    }

    /// Best effort. The caller may already be gone — killed, or interrupted —
    /// and there is nothing useful to do about that from here: the capture on
    /// disk is the durable record, and the status channel carries it.
    ///
    /// The loop is for signals, not for size: a blocking write to a pipe
    /// transfers the whole buffer however large, waiting for the reader — a
    /// 200 KB report goes in one pass past a 64 KiB pipe, measured. What splits
    /// it is a signal arriving mid-write, which surfaces as `EINTR` if nothing
    /// had been transferred yet and as a short count if something had. Neither
    /// is a failure, and treating either as one would truncate the report into
    /// something the parent reads as a start that never happened.
    ///
    /// No test covers the second pass, and none can cheaply: on Linux a
    /// blocking pipe write transfers the lot, so the loop only ever runs once
    /// unless a signal lands mid-write. Read it as reasoned, not as pinned.
    fn write(&self, msg: &str) {
        let mut buf = msg.as_bytes();
        while !buf.is_empty() {
            match nix::unistd::write(&self.fd, buf) {
                // Cannot happen for a non-empty buffer on a pipe, but looping
                // on it would spin forever if it ever did.
                Ok(0) => break,
                Ok(n) => buf = &buf[n..],
                Err(nix::errno::Errno::EINTR) => continue,
                Err(_) => break,
            }
        }
    }
}

/// What the parent makes of the bytes the child sent.
///
/// Separate from `detach` because every answer below is a decision rather than
/// a formality, and a decision that can only be exercised by forking is one
/// nobody checks.
fn interpret(report: &str) -> Result<String> {
    match report.split_once('\n') {
        // An `ok` carrying nothing is a defect in whatever built the line, but
        // it is still an `ok`: a child that reported started, and calling that
        // a failed start would tell the caller nothing is running while a
        // detached wrapper runs — the worse of the two wrong answers, because
        // it is the one that stops the caller looking.
        Some(("ok", rest)) => Ok(rest.trim_end().to_string()),
        Some(("err", rest)) => Err(anyhow!("{}", rest.trim_end())),
        // A tag this version does not know. The child spoke, so it may well be
        // running: saying it "exited" would send the reader hunting a crash
        // that did not happen.
        Some((tag, _)) => Err(anyhow!(
            "the backgrounded wrapper reported {tag:?}, which this version does \
             not understand"
        )),
        // No newline anywhere: an empty read, or a write cut short mid-tag.
        // Nothing was reported, and a start nobody reported did not happen as
        // far as the caller can tell.
        None => Err(anyhow!(
            "the backgrounded wrapper exited before saying whether it started"
        )),
    }
}

/// Threads in this process.
///
/// `fork` gives the child only the calling thread, so any lock another thread
/// held at that instant stays held forever in the child. Ordinary locks are
/// the hazard, and they are everywhere: std's stdout lock is one, and a
/// `println!` is enough to wedge on it — measured, 193 of 300 children.
///
/// The allocator is deliberately *not* the example, however well it reads.
/// glibc brackets `fork` with `__malloc_fork_lock_parent` /
/// `__malloc_fork_unlock_child`, and 3000 forks from a process with three
/// threads hammering `malloc` allocated in the child every time without
/// wedging once. Naming it would put a claim under this guard that anyone can
/// falsify in five minutes, and a maintainer who did would conclude the guard
/// is superstition and delete it. What POSIX actually promises after a threaded
/// fork is the async-signal-safe subset and nothing more; glibc's malloc
/// bracketing is an implementation detail to lean on never.
///
/// So the count is the fork's precondition, not a diagnostic.
fn thread_count() -> std::io::Result<usize> {
    Ok(std::fs::read_dir("/proc/self/task")?.count())
}

/// Fork, put the child in its own session, and block the parent until the child
/// reports.
///
/// The parent blocks on the pipe until the child calls `Reporter::started` or
/// `Reporter::failed`, or dies holding it. That is the whole point: a caller
/// that walked away before learning a start failed is the failure mode `&` has
/// and this does not.
///
/// `setsid` is what makes the child survive the caller's process group being
/// killed. Measured: a `setsid` child outlives a Claude Code Bash call killed
/// at its timeout, where `nohup` and a bare `&` do not.
pub fn detach() -> Detached {
    // The child of the fork below goes on to run ordinary code — open files,
    // take locks, build a tokio runtime — rather than heading straight for
    // `exec`, so it needs an address space no departed thread left locked. Checking beats asserting:
    // this is what makes the SAFETY note below true at every call site the
    // code permits, instead of true only of the call sites that exist today.
    match thread_count() {
        Ok(1) => {}
        Ok(n) => {
            return Detached::Parent(Err(anyhow!(
                "refusing to fork a process with {n} threads: the child would \
                 inherit locks held by threads that do not cross the fork"
            )))
        }
        Err(e) => return Detached::Parent(Err(anyhow!("count threads: {e}"))),
    }

    // O_CLOEXEC so no descendant of the wrapped command inherits the write end
    // and holds the parent's read open after this process is done with it.
    let (read_fd, write_fd) = match nix::unistd::pipe2(nix::fcntl::OFlag::O_CLOEXEC) {
        Ok(p) => p,
        Err(e) => return Detached::Parent(Err(anyhow!("pipe: {e}"))),
    };

    // SAFETY: `thread_count` answered 1 immediately above, and that answer
    // cannot go stale before the fork: the one thread it counted is this one,
    // executing these statements, so no other thread exists to create a second.
    // The child therefore inherits an address space in which no lock is held by
    // a thread that did not cross, which is what lets it do ordinary work
    // instead of only the async-signal-safe subset.
    //
    // The check is here rather than a comment claiming the caller is
    // single-threaded because `libtest` is not — measured at two threads even
    // under `--test-threads=1` — so a claim would be false at exactly the call
    // sites a test adds. What such a call site gets is not a clean failure: the
    // child wedges on the first ordinary lock a departed thread was holding,
    // std's stdout lock being enough on its own, while the caller blocks on a
    // pipe that has no timeout. Allocation is not the thing that breaks — see
    // `thread_count` for why naming it would be worse than saying nothing.
    match unsafe { nix::unistd::fork() } {
        Err(e) => Detached::Parent(Err(anyhow!("fork: {e}"))),
        Ok(nix::unistd::ForkResult::Parent { .. }) => {
            // The parent must not hold a write end, or its own read never ends.
            drop(write_fd);
            let mut buf = String::new();
            let mut f = std::fs::File::from(read_fd);
            // Reads to EOF, so a report longer than the pipe buffer arrives
            // whole: this drains while the child writes. Non-UTF-8 fails here
            // rather than being read lossily — this pipe carries only text this
            // binary wrote, so bytes that are not text mean the protocol broke,
            // not that some foreign name came through.
            if let Err(e) = f.read_to_string(&mut buf) {
                return Detached::Parent(Err(anyhow!("read start status: {e}")));
            }
            Detached::Parent(interpret(&buf))
        }
        Ok(nix::unistd::ForkResult::Child) => {
            drop(read_fd);
            let reporter = Reporter { fd: write_fd };
            // A child that could not detach must not pass for one that did.
            if let Err(e) = nix::unistd::setsid() {
                reporter.failed(&anyhow!("setsid: {e}"));
            }
            Detached::Child(reporter)
        }
    }
}

/// The `background-probe` subcommand: run `detach` once and print what the
/// parent learned.
///
/// It is here, in the binary, because every property `detach` has is a property
/// of processes, and the only way to drive one is to be one. Nothing is set up
/// before this: `main` reaches it with `Cli::parse` and `repo_root` behind it
/// and nothing else, so a probe that gets past the thread check has also
/// measured this binary's startup as single-threaded — the precondition every
/// other caller of `detach` inherits.
pub fn probe(mode: &str) -> ! {
    // Leaves a partial line in std's `LineWriter` — no newline, so it stays
    // buffered across the fork. It is the only way to observe the `_exit` rule:
    // the child inherits a copy of this buffer, and `std::process::exit` there
    // would write the marker a second time.
    if mode == "dirty-stdout" {
        print!("MARKER");
    }
    match detach() {
        Detached::Parent(Ok(line)) => {
            // The caller's session, for the child's to be compared against:
            // leading a session means nothing unless it is not this one.
            let sid = nix::unistd::getsid(None).map(|p| p.as_raw()).unwrap_or(-1);
            println!("ok {line}");
            println!("parent-sid {sid}");
            std::process::exit(0)
        }
        Detached::Parent(Err(e)) => {
            println!("err {e:#}");
            std::process::exit(3)
        }
        Detached::Child(reporter) => probe_child(mode, reporter),
    }
}

/// The detached half of the probe. One mode per property under test.
fn probe_child(mode: &str, reporter: Reporter) -> ! {
    let pid = nix::unistd::getpid().as_raw();
    let sid = nix::unistd::getsid(None).map(|p| p.as_raw()).unwrap_or(-1);
    match mode {
        // Reports late on purpose. The numbers show the parent read the report;
        // the delay shows it waited for it rather than returning first.
        "report-ok" => {
            std::thread::sleep(std::time::Duration::from_millis(500));
            reporter.started(&format!("pid={pid} sid={sid}"));
        }
        "report-err" => reporter.failed(&anyhow!("mkdir /nope: Permission denied")),
        // Bails out holding the parent's buffered marker. Whether that marker
        // reaches the caller once or twice is the whole of the `_exit` rule.
        "dirty-stdout" => reporter.failed(&anyhow!("bailing out with a dirty stdout")),
        // Drops the reporter unwritten: the write end closes with nothing on it.
        "silent" => drop(reporter),
        // Past the pipe's 64 KiB buffer, which only arrives whole because the
        // parent drains while this writes.
        "report-big" => reporter.started(&"x".repeat(200_000)),
        // A grandchild outliving this process, holding nothing but whatever it
        // inherited. Were the write end not O_CLOEXEC it would keep the
        // parent's read from ever reaching EOF until the grandchild died.
        "leak-check" => {
            let grandchild = std::process::Command::new("sleep")
                .arg("10")
                .stdin(std::process::Stdio::null())
                .stdout(std::process::Stdio::null())
                .stderr(std::process::Stdio::null())
                .spawn()
                .map(|c| c.id() as i32)
                .unwrap_or(-1);
            reporter.started(&format!("pid={pid} sid={sid} grandchild={grandchild}"));
        }
        other => reporter.failed(&anyhow!("unknown probe mode: {other}")),
    }
    // SAFETY: `_exit` is always safe to call. Reaching here means the report is
    // already sent, so nothing is waiting on this process — and see the module
    // doc for why it is not `std::process::exit`.
    unsafe { libc::_exit(0) }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// `libtest` runs tests in a multi-threaded process, which is exactly the
    /// shape `fork` must not be called from — so the refusal can be checked
    /// here, and only here, without forking anything.
    #[test]
    fn detach_refuses_to_fork_a_process_that_has_more_than_one_thread() {
        assert!(
            thread_count().unwrap() > 1,
            "this test is only meaningful in a multi-threaded harness"
        );
        match detach() {
            Detached::Parent(Err(e)) => {
                let msg = e.to_string();
                assert!(msg.contains("threads"), "{msg}");
                assert!(msg.contains("do not cross the fork"), "{msg}");
            }
            Detached::Parent(Ok(line)) => panic!("a fork was permitted here: {line}"),
            Detached::Child(_) => panic!("a fork happened in a multi-threaded process"),
        }
    }

    #[test]
    fn a_reported_line_reaches_the_caller_whole() {
        let line = interpret("ok\n/tmp/x/1  wrapper pid 7  child pid 8").unwrap();
        assert_eq!(line, "/tmp/x/1  wrapper pid 7  child pid 8");
    }

    /// An `ok` with nothing after it is a defect in whatever built the line,
    /// but the child did start, and a caller told otherwise stops looking for
    /// a wrapper that is running.
    #[test]
    fn an_ok_carrying_no_line_still_means_the_child_started() {
        assert_eq!(interpret("ok\n").unwrap(), "");
    }

    #[test]
    fn a_reported_reason_reaches_the_caller_whole() {
        let e = interpret("err\nspawn \"nope\": No such file or directory").unwrap_err();
        assert_eq!(e.to_string(), "spawn \"nope\": No such file or directory");
    }

    /// The empty read is the case that matters: a child that died holding the
    /// pipe said nothing, and nothing is not a successful start.
    #[test]
    fn a_report_that_never_arrived_is_a_failed_start() {
        let e = interpret("").unwrap_err();
        assert!(e.to_string().contains("before saying whether it started"));
    }

    /// A write cut short mid-tag leaves no newline. Treating the fragment as a
    /// tag would turn a truncated `ok` into a start that was never reported.
    #[test]
    fn a_report_with_no_newline_is_not_a_report() {
        for fragment in ["ok", "e", "err", "garbage"] {
            let e = interpret(fragment).unwrap_err();
            assert!(
                e.to_string().contains("before saying whether it started"),
                "{fragment}"
            );
        }
    }

    /// The child spoke, so it may still be running. Reporting it as an exit
    /// would send whoever reads the line hunting a crash that did not happen.
    #[test]
    fn a_tag_this_protocol_does_not_know_is_not_reported_as_a_crash() {
        let e = interpret("maybe\nsomething").unwrap_err();
        let msg = e.to_string();
        assert!(msg.contains("\"maybe\""), "{msg}");
        assert!(msg.contains("does not understand"), "{msg}");
        assert!(
            !msg.contains("exited"),
            "an unknown tag is not an exit: {msg}"
        );
    }
}
