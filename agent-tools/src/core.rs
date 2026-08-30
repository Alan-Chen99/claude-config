use anyhow::Result;
use std::path::{Path, PathBuf};
use std::process::Stdio;
use std::sync::atomic::AtomicI64;
use std::sync::Arc;
use tokio::process::Command;

use crate::capture;

/// How much the tee captures once capturing is the only thing still happening.
/// Which byte the count runs from is `capture::Bound`'s to say, and it follows
/// from the destination: after a downstream refuses a write for a forwarded
/// run, from the first byte for one with nowhere to forward to. A forwarded run
/// in normal operation never approaches this, because forwarding does not fail;
/// a backgrounded one is past the starting line from its first byte.
pub const DEFAULT_DRAIN_CAP_BYTES: u64 = 256 * 1024 * 1024;

// The two properties that make that number a cap at all, checked where it is
// written rather than by a test. Every test that exercises the bound names its
// own, so the resolved default has no runtime coverage at its top end, where an
// unbounded value lets a wrapped `yes` drain tens of gigabytes into the capture
// directory while the whole suite stays green. A `const` assertion fails the build instead, which is both
// stronger than a failing test and the reason clippy does not call it constant.
const _: () = assert!(
    DEFAULT_DRAIN_CAP_BYTES < u64::MAX,
    "an unbounded default is the disk-filling path the bound exists to close"
);
const _: () = assert!(
    DEFAULT_DRAIN_CAP_BYTES <= 4 * 1024 * 1024 * 1024,
    "a cap protects nothing it cannot reach before the disk does: at the \
     measured 400 MB/s, 4 GiB is ten seconds of drain"
);

/// Why the child's two streams did or did not share one destination.
///
/// `status::Capture` is the same fact read back off disk: merged runs open one
/// capture file, split runs two. A change to what either arm opens has to move
/// both, or a report line describes files that are not there.
#[derive(Debug, Clone, PartialEq)]
pub enum Merge {
    /// One destination. The reason names the condition that made it sound.
    Merged(&'static str),
    /// Two destinations. The reason names what disqualified merging.
    Split(&'static str),
}

impl Merge {
    /// The condition that decided it, for the record. Which way it was decided
    /// is not carried with it: `status::Capture` already reads that off disk
    /// from how many capture files exist, and two records of one fact drift.
    pub fn condition(&self) -> &'static str {
        match *self {
            Merge::Merged(why) | Merge::Split(why) => why,
        }
    }
}

/// The condition recorded when the wrapper, not the caller, owns where the
/// child's bytes go. Sound for the reason the merge rule already states, not
/// as an exception to it — but the reason is the pipe, not appendingness: the
/// capture file is opened `create` + `append` in every arm, split included
/// (twice, there), so that cannot be what tells merged apart from split. What
/// does is that this pipe is one the wrapper creates itself and hands the
/// child *both* write ends of — fd 1 and fd 2 both `dup2`'d from the same end
/// — so no descriptor obtained from outside this process participates, and
/// there is nothing left for two independent ends to disagree about.
pub const BACKGROUNDED: &str = "backgrounded: wrapper owns the destination";

/// Where the child's streams are forwarded, beyond the capture.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Destination {
    /// This process's own stdout and stderr, which the merge rule inspects.
    Caller,
    /// The caller has gone; the capture is the whole record. Nothing here can
    /// refuse a write, so a bound counting from a refusal would never arm — and
    /// the case that needs one is precisely a wrapper outliving its session,
    /// where nobody is left to read `ps`'s byte count and stop a wrapped `yes`
    /// by hand. The bound counts from the first byte instead:
    /// `capture::Bound::Captured`.
    Nowhere,
}

/// The caller's descriptors provably reached two destinations, so bare kept the
/// streams apart too. Named because `status::render` must not report it: it is
/// the one split that explains nothing, and it is the shape of every harness
/// that spawns with two pipes.
pub const DESTINATIONS_ALREADY_DIFFERED: &str = "different destinations";

/// Decide whether the child's two streams may share one destination.
///
/// Whether two descriptors share an open file description is not decidable from
/// userspace, so this does not try. It admits only destinations that have no
/// offset to disagree about — a pipe, or a file both descriptors append to —
/// which makes the question irrelevant. Everything else splits. Declining costs
/// interleaving; guessing wrong misroutes the caller's data.
///
/// `Split` therefore answers two different questions the same conservative way:
/// *cannot tell*, when a descriptor would not be inspected at all, and *can
/// tell, and merging would be unsound*. The reason string names which.
pub fn decide_merge(fd_out: i32, fd_err: i32) -> Merge {
    use nix::fcntl::{fcntl, FcntlArg, OFlag};
    use nix::sys::stat::{fstat, FileStat, SFlag};

    let (s_out, s_err) = match (fstat(fd_out), fstat(fd_err)) {
        (Ok(a), Ok(b)) => (a, b),
        _ => return Merge::Split("descriptor could not be inspected"),
    };
    if s_out.st_dev != s_err.st_dev || s_out.st_ino != s_err.st_ino {
        return Merge::Split(DESTINATIONS_ALREADY_DIFFERED);
    }

    let (f_out, f_err) = match (
        fcntl(fd_out, FcntlArg::F_GETFL),
        fcntl(fd_err, FcntlArg::F_GETFL),
    ) {
        (Ok(a), Ok(b)) => (OFlag::from_bits_truncate(a), OFlag::from_bits_truncate(b)),
        // No test drives this arm: both descriptors have just survived `fstat`,
        // and F_GETFL on a valid fd fails only with EBADF, which that already
        // screened. Reaching it needs a TOCTOU race no call site can produce.
        // Unreachable in practice is not dead — keep the arm.
        _ => return Merge::Split("descriptor flags could not be read"),
    };
    let writable = |f: OFlag| {
        let m = f & OFlag::O_ACCMODE;
        m == OFlag::O_WRONLY || m == OFlag::O_RDWR
    };
    if !writable(f_out) || !writable(f_err) {
        return Merge::Split("not both writable");
    }

    let is_fifo = |s: &FileStat| SFlag::from_bits_truncate(s.st_mode).contains(SFlag::S_IFIFO);
    if is_fifo(&s_out) && is_fifo(&s_err) {
        return Merge::Merged("both pipes, same destination");
    }
    if f_out.contains(OFlag::O_APPEND) && f_err.contains(OFlag::O_APPEND) {
        return Merge::Merged("both appending, same file");
    }
    Merge::Split("same file, but not both appending")
}

/// What the wrapper reads back from the child, which the merge decision fixes:
/// the one pipe it made and owns, or the two the child was spawned with.
///
/// Matched in exactly one place, so a stream's tee and its silence watcher are
/// spawned from the same arm and cannot drift apart, and so a new `Merge`
/// variant is a compile error at the single site that builds this rather than a
/// silent fall into the split path at three.
enum Streams {
    /// One pipe carrying both of the child's streams.
    Merged(tokio::net::unix::pipe::Receiver),
    /// The child's own two pipes, which live on the `Child` until taken.
    Split,
}

/// What the core observed by the end of the run. Everything here explains a
/// difference from bare, and none of it is knowable before the tees finish. The
/// merge condition explains a difference too and is not here: it is decided
/// before the spawn and handed to `on_spawn`, so a caller that records it need
/// not wait for the drain — and one fact with one delivery path cannot disagree
/// with itself. `TeeOutcome::bytes_since_close_detected` is not here either, for
/// the opposite reason: it explains nothing to a reader, being the anchor the
/// drain bound compares against and nothing a caller acts on.
#[derive(Debug, Clone)]
pub struct Outcome {
    pub exit_code: i32,
    /// A downstream stopped accepting writes, on either stream, and forwarding
    /// to it stopped. The child ran on and the capture kept growing.
    pub forward_closed: bool,
    /// A drain reached its bound, on either stream, and the read end was
    /// dropped. The child met the `SIGPIPE` bare would have given it, and the
    /// capture stops short of whatever it wrote after that.
    pub drain_capped: bool,
    /// A capture reached its bound with nothing downstream, on either stream,
    /// and the read end was dropped. `drain_capped`'s sibling and never its
    /// synonym: the two name different bounds, and a backgrounded child
    /// reported under the other one would send its reader looking for the
    /// downstream that closed, of which there was none.
    pub capture_capped: bool,
    /// A capture could not be written, on either stream, and stopped there;
    /// what the OS said about the first such failure. The child ran to its own
    /// end and the caller's streams carry everything it wrote, so nothing else
    /// distinguishes this run from a complete one — except under
    /// `Destination::Nowhere`, where there are no caller streams to carry
    /// anything and this failure is total loss, not a difference from bare.
    pub capture_error: Option<String>,
}

/// Spawn failed, or something else did. Kept distinct so `run` can record the
/// spawn error string exactly as the OS reported it.
#[derive(Debug)]
pub enum CoreError {
    Spawn(std::io::Error),
    Other(anyhow::Error),
}

impl std::fmt::Display for CoreError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CoreError::Spawn(e) => write!(f, "{e}"),
            CoreError::Other(e) => write!(f, "{e:#}"),
        }
    }
}

impl From<anyhow::Error> for CoreError {
    fn from(e: anyhow::Error) -> Self {
        CoreError::Other(e)
    }
}

/// Run `cmd`, capturing both streams under `capture_dir` and, per `destination`,
/// forwarding them to this process's own stdout/stderr or to nowhere at all.
///
/// `on_spawn` receives the child pid the moment it exists, and with it the merge
/// condition, which was decided before the spawn: it is the one fact explaining a
/// capture's shape that is knowable this early, so a reader never finds a capture
/// whose shape nothing accounts for. `on_reap` receives the exit code the moment
/// the child is reaped, before any draining. `run` uses those to persist facts in
/// the order the invariant requires; `run-core` ignores them.
///
/// `drain_cap_bytes` bounds what the tee keeps capturing after a downstream has
/// stopped accepting writes; `None` is `DEFAULT_DRAIN_CAP_BYTES`. Resolving it
/// here rather than at each entry point is what keeps `run` and `run-core` from
/// disagreeing about it, which they once did.
pub async fn run_core<S, R>(
    cmd: &[String],
    capture_dir: &Path,
    drain_cap_bytes: Option<u64>,
    destination: Destination,
    on_spawn: S,
    on_reap: R,
) -> Result<Outcome, CoreError>
where
    S: FnOnce(u32, &'static str),
    R: FnOnce(i32),
{
    // The only place the production default is applied. Both entry points pass
    // whatever their flag held, so there is no second copy to drift from.
    let drain_cap_bytes = drain_cap_bytes.unwrap_or(DEFAULT_DRAIN_CAP_BYTES);

    // Which byte the bound counts from follows from where the bytes go, so it
    // is decided here beside the destination rather than inside the tee: a
    // forwarded run has a downstream whose refusal is the only thing that makes
    // capturing the whole of what the tee is doing, while a run with nowhere to
    // forward to is in that state from its first byte. One bound serves both
    // streams and each counts its own, which is the arithmetic the drain bound
    // already did on a split run.
    let bound = match destination {
        Destination::Caller => capture::Bound::AfterForwardCloses(drain_cap_bytes),
        Destination::Nowhere => capture::Bound::Captured(drain_cap_bytes),
    };

    // `cmd[0]` below would panic on an empty slice. Both callers check first,
    // but this is the contract the passthrough tests drive directly, so it
    // answers instead of aborting.
    if cmd.is_empty() {
        return Err(CoreError::Other(anyhow::anyhow!(
            "run_core: no command supplied"
        )));
    }

    std::fs::create_dir_all(capture_dir)
        .map_err(|e| CoreError::Other(anyhow::anyhow!("mkdir {}: {e}", capture_dir.display())))?;

    let merge = match destination {
        Destination::Caller => decide_merge(libc::STDOUT_FILENO, libc::STDERR_FILENO),
        // Asking would get the wrong answer, not merely a redundant one. Under
        // `--background`, `detach_std_fds` has already pointed this process's
        // own stdout and stderr at one `/dev/null`, opened `O_RDWR` with no
        // `O_APPEND` — and `decide_merge` on that shape returns
        // `Split("same file, but not both appending")`, correct for a real
        // caller on a character device but wrong here: it would make every
        // backgrounded run a two-file capture and print `streams split:
        // backgrounded: wrapper owns the destination` on every one of them.
        // "Split because nobody was watching" explains nothing a reader
        // needed explained, and would appear on every such run rather than
        // the rare one worth flagging.
        Destination::Nowhere => Merge::Merged(BACKGROUNDED),
    };

    // `command` owns every write end it is handed, and a pipe reports EOF only
    // once the last one closes. This block is that ownership: it ends at the
    // brace, the moment the child holds its own copies. A `Command` still in
    // scope is a write end still open, and a merged tee reading a pipe that
    // nobody will write to or close again.
    let (mut child, streams) = {
        let mut command = Command::new(&cmd[0]);
        command.args(&cmd[1..]).stdin(Stdio::inherit());

        let streams = match merge {
            Merge::Merged(_) => {
                // O_CLOEXEC, as `Stdio::piped()` does for the split arm: the
                // child gets fd 1 and fd 2 by `dup2`, which clears the flag,
                // and the copies these came from close on exec. Left
                // inheritable, a descendant of a child that closed its own
                // stdout and stderr would still hold a write end, and the tee
                // would wait on a pipe bare would already have closed.
                let (r, w) = nix::unistd::pipe2(nix::fcntl::OFlag::O_CLOEXEC)
                    .map_err(|e| CoreError::Other(anyhow::anyhow!("pipe: {e}")))?;
                let w2 = w
                    .try_clone()
                    .map_err(|e| CoreError::Other(anyhow::anyhow!("dup: {e}")))?;
                // Registered with the reactor before there is a child to
                // strand. `EMFILE` or `ENOMEM` here returns while the only
                // thing that exists is a pipe; after the spawn it would leave a
                // running child wired to a pipe nobody drains, blocked forever
                // on the write that fills it.
                let rx = tokio::net::unix::pipe::Receiver::from_owned_fd(r)
                    .map_err(|e| CoreError::Other(anyhow::anyhow!("async pipe: {e}")))?;
                command.stdout(Stdio::from(w)).stderr(Stdio::from(w2));
                Streams::Merged(rx)
            }
            Merge::Split(_) => {
                command.stdout(Stdio::piped()).stderr(Stdio::piped());
                Streams::Split
            }
        };

        (command.spawn().map_err(CoreError::Spawn)?, streams)
    };

    let pid = child
        .id()
        .ok_or_else(|| CoreError::Other(anyhow::anyhow!("child pid unavailable")))?;
    // Before `on_spawn`, not after. `run`'s `on_spawn` is what answers a
    // `--background` caller, and a caller holding the pid may signal at once.
    // In the other order the wrapper is briefly signallable and unprotected —
    // for as long as it takes to register four handlers — and a SIGTERM landing
    // there takes its default disposition, killing the wrapper and leaving the
    // child alive at PPID 1, the exact opposite of the one-signal-ends-both
    // property the wrapper exists to provide. Narrow, and not a race anyone has
    // seen bite: with the installation after the report, `SigCgt` already
    // carried SIGTERM at the caller's first possible read in 20 runs of 20,
    // because the caller's own path — parent print, exit, reap, wake, `/proc`
    // open — is the slower of the two. This ordering closes it by construction
    // instead, which is the only way it can be closed: no test can observe a
    // window the observer is too slow to enter.
    //
    // Its own failure is discarded rather than raised, and that is what keeps
    // it out of the gap's other constraint: nothing between the spawn and
    // `on_spawn` may return `Err`, or a failed start is reported for a child
    // that is running. The `CoreError::Other` arm in `run` argues that in full.
    let (cancel_tx, cancel_rx) = tokio::sync::watch::channel(false);
    crate::signals::install_forwarding(pid as i32, cancel_rx.clone()).ok();

    on_spawn(pid, merge.condition());

    let last_stdout = Arc::new(AtomicI64::new(chrono::Utc::now().timestamp_millis()));
    let last_stderr = Arc::new(AtomicI64::new(chrono::Utc::now().timestamp_millis()));

    let dir: PathBuf = capture_dir.to_path_buf();

    // One writer per stream, chosen once from `destination` rather than
    // re-decided per `Streams` arm below. Before this, `Streams::Split`
    // hardcoded the caller's own stdout/stderr regardless of `destination`,
    // correct only because `Nowhere` never (today) produces `Merge::Split` —
    // an invariant enforced by the match above and nothing in this arm.
    // Boxing erases the writer type behind one trait so both arms draw from
    // the same two bindings and neither can fall back to the caller's
    // descriptors on its own.
    trait Fwd: tokio::io::AsyncWrite + Unpin + Send {}
    impl<T: tokio::io::AsyncWrite + Unpin + Send> Fwd for T {}
    let (fwd_out, fwd_err): (Box<dyn Fwd>, Box<dyn Fwd>) = match destination {
        Destination::Caller => (Box::new(tokio::io::stdout()), Box::new(tokio::io::stderr())),
        Destination::Nowhere => (Box::new(tokio::io::sink()), Box::new(tokio::io::sink())),
    };

    // A stream, the tee that carries it, and the watcher that times its silence
    // are one arm each. A merged run has one of all three: it advances only
    // `last_stdout`, so a second watcher would sit on a clock nobody winds and
    // announce silence on a stream that is busy, under a name the run does not
    // have.
    let (tee_a, tee_b, watch_a, watch_b) = match streams {
        Streams::Merged(rx) => {
            let tee = tokio::spawn(capture::tee(
                "output",
                rx,
                dir.join("output"),
                fwd_out,
                bound,
                last_stdout.clone(),
                dir.clone(),
            ));
            let watch = tokio::spawn(capture::watch_silence(
                "output",
                last_stdout,
                30_000,
                dir.clone(),
                cancel_rx.clone(),
            ));
            (tee, None, watch, None)
        }
        Streams::Split => {
            let stdout_pipe = child
                .stdout
                .take()
                .ok_or_else(|| CoreError::Other(anyhow::anyhow!("no stdout pipe")))?;
            let stderr_pipe = child
                .stderr
                .take()
                .ok_or_else(|| CoreError::Other(anyhow::anyhow!("no stderr pipe")))?;
            let tee_out = tokio::spawn(capture::tee(
                "stdout",
                stdout_pipe,
                dir.join("stdout"),
                fwd_out,
                bound,
                last_stdout.clone(),
                dir.clone(),
            ));
            let tee_err = tokio::spawn(capture::tee(
                "stderr",
                stderr_pipe,
                dir.join("stderr"),
                fwd_err,
                bound,
                last_stderr.clone(),
                dir.clone(),
            ));
            let watch_out = tokio::spawn(capture::watch_silence(
                "stdout",
                last_stdout,
                30_000,
                dir.clone(),
                cancel_rx.clone(),
            ));
            let watch_err = tokio::spawn(capture::watch_silence(
                "stderr",
                last_stderr,
                30_000,
                dir.clone(),
                cancel_rx,
            ));
            (tee_out, Some(tee_err), watch_out, Some(watch_err))
        }
    };

    let status = child
        .wait()
        .await
        .map_err(|e| CoreError::Other(anyhow::anyhow!("wait: {e}")))?;
    let exit_code = status.code().unwrap_or_else(|| {
        #[cfg(unix)]
        {
            use std::os::unix::process::ExitStatusExt;
            if let Some(sig) = status.signal() {
                return 128 + sig;
            }
        }
        1
    });
    on_reap(exit_code);

    let _ = cancel_tx.send(true);
    // Whatever a tee reports, and whatever became of the tee itself, the exit
    // code above is already decided: the wrapper's own bookkeeping never
    // decides what the caller learns the child did.
    let a = tee_outcome(tee_a.await);
    let b = match tee_b {
        Some(h) => tee_outcome(h.await),
        None => capture::TeeOutcome::default(),
    };
    let _ = watch_a.await;
    if let Some(watch_b) = watch_b {
        let _ = watch_b.await;
    }

    Ok(Outcome {
        exit_code,
        // Either stream losing its downstream, or either drain reaching its
        // bound, is the same difference from bare. Which one it was is on
        // stderr under the stream's own name — except when stderr is the
        // descriptor that closed, or the merge rule made it the same one as
        // stdout, which are the two shapes this record exists to cover. There
        // the boolean is all there is, and it does not say which stream.
        // Splitting it per stream belongs with F16, which owns the rest of
        // what a record cannot currently say. The first capture failure is
        // carried whole, because a path and an `errno` are what make it
        // actionable and there is nowhere else left to read them.
        forward_closed: a.forward_closed || b.forward_closed,
        drain_capped: a.drain_capped || b.drain_capped,
        capture_capped: a.capture_capped || b.capture_capped,
        capture_error: a.capture_error.or(b.capture_error),
    })
}

/// What one tee is known to have observed, including when the answer is that it
/// stopped without finishing.
///
/// A tee owns its capture, so a tee that errored or panicked took the capture
/// down with it. Defaulting there would report a clean outcome for a capture
/// that stopped dead — the one shape "a capture never silently stops growing"
/// cannot survive.
fn tee_outcome(
    joined: Result<Result<capture::TeeOutcome>, tokio::task::JoinError>,
) -> capture::TeeOutcome {
    match joined {
        Ok(Ok(o)) => o,
        Ok(Err(e)) => capture::TeeOutcome {
            capture_error: Some(format!("{e:#}")),
            ..Default::default()
        },
        Err(e) => capture::TeeOutcome {
            capture_error: Some(format!("tee task died: {e}")),
            ..Default::default()
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::os::fd::AsRawFd;

    /// The crate has no lib target, so `tests/core_test.rs` reaches `run_core`
    /// only through the binary — and an empty command cannot be spelled on a
    /// command line. A unit test is the only place this precondition can be
    /// driven.
    #[tokio::test]
    async fn empty_command_is_an_error_not_a_panic() {
        let tmp = tempfile::tempdir().unwrap();
        let cap = tmp.path().join("cap");
        let cmd: Vec<String> = Vec::new();

        let err = run_core(&cmd, &cap, None, Destination::Caller, |_, _| {}, |_| {})
            .await
            .expect_err("an empty command has nothing to run");

        assert!(matches!(err, CoreError::Other(_)), "got: {err:?}");
        assert!(!cap.exists(), "nothing ran, so nothing should be captured");
    }

    /// Pins what a unit test can check about `Destination::Nowhere` without
    /// touching the process's real fd 1: a single merged capture file rather
    /// than a split pair, the `BACKGROUNDED` condition delivered to `on_spawn`
    /// before the child is even reaped, and `forward_closed` reading false
    /// because the writer behind it never refuses a write.
    ///
    /// It does not pin *which* writer that is. Swapping `sink()` for
    /// `tokio::io::stdout()` in the `Nowhere` arm leaves this test, and the
    /// whole suite, green: a sink and a real stdout both accept every write in
    /// a test process, so nothing here would notice bytes reaching the
    /// caller's descriptors instead of nowhere. That property has no lever in
    /// this file — the only fd it could show up on is the process's own
    /// stdout, which `libtest` is concurrently writing progress lines to, so
    /// redirecting it here would be flaky rather than wrong.
    #[tokio::test]
    async fn a_run_with_no_destination_merges_into_one_capture_and_records_why() {
        let dir = tempfile::tempdir().unwrap();
        // `on_spawn` is `FnOnce`; the assertion inside it only runs if
        // `run_core` actually calls it. Without this flag, a `run_core` that
        // silently stopped calling `on_spawn` would leave this test green
        // while pinning nothing.
        let spawned = Arc::new(std::sync::atomic::AtomicBool::new(false));

        let out = run_core(
            &["sh".into(), "-c".into(), "echo out; echo err 1>&2".into()],
            dir.path(),
            None,
            Destination::Nowhere,
            {
                let spawned = spawned.clone();
                move |_pid, merge| {
                    assert_eq!(
                        merge, BACKGROUNDED,
                        "a run with no caller records why it merged"
                    );
                    spawned.store(true, std::sync::atomic::Ordering::SeqCst);
                }
            },
            |_code| {},
        )
        .await
        .unwrap();

        assert!(
            spawned.load(std::sync::atomic::Ordering::SeqCst),
            "on_spawn must run, or the assertion inside it never does"
        );
        assert_eq!(out.exit_code, 0);
        let captured = std::fs::read_to_string(dir.path().join("output")).unwrap();
        assert!(captured.contains("out"), "{captured}");
        assert!(captured.contains("err"), "{captured}");
        assert!(
            !dir.path().join("stdout").exists(),
            "a merged capture holds one file; the other is absent, not empty"
        );
        assert!(!out.forward_closed, "there was no downstream to close");
    }

    /// The join result is the whole report: a tee that stopped early looks from
    /// here exactly like one that finished with nothing to say, and defaulting
    /// answers "nothing happened" for a capture that stopped dead.
    ///
    /// Neither failing arm is reachable through a wrapped command. With a
    /// capture failure isolated inside `tee`, the only error left is a read
    /// that fails, which no command can be made to produce, and nothing there
    /// panics on purpose — so this drives the arms directly, and the arms are
    /// all it reaches. Whether `run_core` still asks is beyond it: measured,
    /// wiring the two call sites back to `.ok().and_then(|r| r.ok())`
    /// `.unwrap_or_default()` leaves every test in the suite passing, and the
    /// only thing that notices is a dead-code warning on this function.
    #[tokio::test]
    async fn a_tee_that_stopped_early_is_a_failed_capture() {
        let finished = tee_outcome(Ok(Ok(capture::TeeOutcome {
            forward_closed: true,
            ..Default::default()
        })));
        assert_eq!(
            finished.capture_error, None,
            "a finished tee reports what it saw"
        );
        assert!(finished.forward_closed);

        let errored = tee_outcome(Ok(Err(anyhow::anyhow!("read: Input/output error"))));
        assert_eq!(
            errored.capture_error.as_deref(),
            Some("read: Input/output error"),
            "what stopped the tee is what stopped the capture"
        );

        // A panic and an abort are one arm; a panic is the one that happens.
        let panicked = tokio::spawn(async { panic!("tee") }).await.unwrap_err();
        let died = tee_outcome(Err(panicked));
        assert!(
            died.capture_error
                .unwrap_or_default()
                .starts_with("tee task died:"),
            "a capture whose task died says so rather than coming back clean"
        );
    }

    #[test]
    fn two_pipes_to_one_destination_merge() {
        let (r, w) = nix::unistd::pipe().unwrap();
        let w2 = w.try_clone().unwrap();
        assert_eq!(
            decide_merge(w.as_raw_fd(), w2.as_raw_fd()),
            Merge::Merged("both pipes, same destination")
        );
        drop(r);
    }

    #[test]
    fn one_appending_file_under_two_descriptors_merges() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("both");
        let a = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&path)
            .unwrap();
        let b = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&path)
            .unwrap();
        assert_eq!(
            decide_merge(a.as_raw_fd(), b.as_raw_fd()),
            Merge::Merged("both appending, same file")
        );
    }

    #[test]
    fn same_file_without_append_splits() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("both");
        let a = std::fs::File::create(&path).unwrap();
        let b = std::fs::OpenOptions::new().write(true).open(&path).unwrap();
        assert_eq!(
            decide_merge(a.as_raw_fd(), b.as_raw_fd()),
            Merge::Split("same file, but not both appending")
        );
    }

    #[test]
    fn different_files_split() {
        let dir = tempfile::tempdir().unwrap();
        let a = std::fs::File::create(dir.path().join("a")).unwrap();
        let b = std::fs::File::create(dir.path().join("b")).unwrap();
        assert_eq!(
            decide_merge(a.as_raw_fd(), b.as_raw_fd()),
            Merge::Split("different destinations")
        );
    }

    /// `fstat(-1)` fails EBADF deterministically, so this branch needs no
    /// fixture and cannot flake. It is pinned because an inverted arm here would
    /// merge a pair the code never managed to inspect — the misrouting the
    /// function's own doc comment refuses.
    #[test]
    fn an_uninspectable_descriptor_splits() {
        assert_eq!(
            decide_merge(-1, -1),
            Merge::Split("descriptor could not be inspected")
        );
    }

    #[test]
    fn a_read_only_descriptor_splits() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("f");
        std::fs::write(&path, b"x").unwrap();
        let a = std::fs::File::open(&path).unwrap();
        let b = std::fs::File::open(&path).unwrap();
        assert_eq!(
            decide_merge(a.as_raw_fd(), b.as_raw_fd()),
            Merge::Split("not both writable")
        );
    }
}
