use anyhow::Result;
use std::path::{Path, PathBuf};
use std::process::Stdio;
use std::sync::atomic::AtomicI64;
use std::sync::Arc;
use tokio::process::Command;

use crate::capture;

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
        return Merge::Split("different destinations");
    }

    let (f_out, f_err) = match (
        fcntl(fd_out, FcntlArg::F_GETFL),
        fcntl(fd_err, FcntlArg::F_GETFL),
    ) {
        (Ok(a), Ok(b)) => (
            OFlag::from_bits_truncate(a),
            OFlag::from_bits_truncate(b),
        ),
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

    let is_fifo = |s: &FileStat| {
        SFlag::from_bits_truncate(s.st_mode).contains(SFlag::S_IFIFO)
    };
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

/// What the core observed. Everything here explains a difference from bare.
#[derive(Debug, Clone)]
pub struct Outcome {
    pub exit_code: i32,
    pub merge: Merge,
    /// A downstream stopped accepting writes, on either stream, and forwarding
    /// to it stopped. The child ran on and the capture kept growing.
    pub forward_closed: bool,
    /// Bytes captured after that, summed over both streams.
    pub post_close_bytes: u64,
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

/// Run `cmd`, capturing both streams under `capture_dir` and forwarding them to
/// this process's own stdout/stderr.
///
/// `on_spawn` receives the child pid the moment it exists; `on_reap` receives the
/// exit code the moment the child is reaped, before any draining. `run` uses those
/// to persist facts in the order the invariant requires; `run-core` ignores them.
pub async fn run_core<S, R>(
    cmd: &[String],
    capture_dir: &Path,
    on_spawn: S,
    on_reap: R,
) -> Result<Outcome, CoreError>
where
    S: FnOnce(u32),
    R: FnOnce(i32),
{
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

    // The wrapper's own descriptors: what the caller sees, and so what the
    // decision must be about.
    let merge = decide_merge(libc::STDOUT_FILENO, libc::STDERR_FILENO);

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
    on_spawn(pid);

    let (cancel_tx, cancel_rx) = tokio::sync::watch::channel(false);
    crate::signals::install_forwarding(pid as i32, cancel_rx.clone()).ok();

    let last_stdout = Arc::new(AtomicI64::new(chrono::Utc::now().timestamp_millis()));
    let last_stderr = Arc::new(AtomicI64::new(chrono::Utc::now().timestamp_millis()));

    let dir: PathBuf = capture_dir.to_path_buf();
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
                tokio::io::stdout(),
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
                tokio::io::stdout(),
                last_stdout.clone(),
                dir.clone(),
            ));
            let tee_err = tokio::spawn(capture::tee(
                "stderr",
                stderr_pipe,
                dir.join("stderr"),
                tokio::io::stderr(),
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
    // A tee that panicked or failed its capture reports nothing, exactly as
    // before this returned anything: the exit code is guaranteed and the
    // wrapper's own bookkeeping never decides what the caller learns the child
    // did. Isolating a failed capture is its own fix; this only stops the
    // forward close from being discarded.
    let a = tee_a.await.ok().and_then(|r| r.ok()).unwrap_or_default();
    let b = match tee_b {
        Some(h) => h.await.ok().and_then(|r| r.ok()).unwrap_or_default(),
        None => capture::TeeOutcome::default(),
    };
    let _ = watch_a.await;
    if let Some(watch_b) = watch_b {
        let _ = watch_b.await;
    }

    Ok(Outcome {
        exit_code,
        merge,
        // Either stream losing its downstream is the same difference from bare;
        // which one it was is already on stderr, under the stream's own name.
        forward_closed: a.forward_closed || b.forward_closed,
        post_close_bytes: a.post_close_bytes + b.post_close_bytes,
    })
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

        let err = run_core(&cmd, &cap, |_| {}, |_| {})
            .await
            .expect_err("an empty command has nothing to run");

        assert!(matches!(err, CoreError::Other(_)), "got: {err:?}");
        assert!(!cap.exists(), "nothing ran, so nothing should be captured");
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
        let a = std::fs::OpenOptions::new().create(true).append(true).open(&path).unwrap();
        let b = std::fs::OpenOptions::new().create(true).append(true).open(&path).unwrap();
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
