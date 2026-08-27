use anyhow::Result;
use std::path::{Path, PathBuf};
use std::process::Stdio;
use std::sync::atomic::AtomicI64;
use std::sync::Arc;
use tokio::process::Command;

use crate::capture;

/// Why the child's two streams did or did not share one destination.
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

/// What the core observed. Everything here explains a difference from bare.
#[derive(Debug, Clone)]
pub struct Outcome {
    pub exit_code: i32,
    pub merge: Merge,
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

    let mut child = Command::new(&cmd[0])
        .args(&cmd[1..])
        .stdin(Stdio::inherit())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(CoreError::Spawn)?;

    let pid = child
        .id()
        .ok_or_else(|| CoreError::Other(anyhow::anyhow!("child pid unavailable")))?;
    on_spawn(pid);

    let stdout_pipe = child
        .stdout
        .take()
        .ok_or_else(|| CoreError::Other(anyhow::anyhow!("no stdout pipe")))?;
    let stderr_pipe = child
        .stderr
        .take()
        .ok_or_else(|| CoreError::Other(anyhow::anyhow!("no stderr pipe")))?;

    let (cancel_tx, cancel_rx) = tokio::sync::watch::channel(false);
    crate::signals::install_forwarding(pid as i32, cancel_rx.clone()).ok();

    let last_stdout = Arc::new(AtomicI64::new(chrono::Utc::now().timestamp_millis()));
    let last_stderr = Arc::new(AtomicI64::new(chrono::Utc::now().timestamp_millis()));

    let dir: PathBuf = capture_dir.to_path_buf();
    let stdout_tee = tokio::spawn(capture::tee(
        "stdout",
        stdout_pipe,
        dir.join("stdout"),
        tokio::io::stdout(),
        last_stdout.clone(),
        dir.clone(),
    ));
    let stderr_tee = tokio::spawn(capture::tee(
        "stderr",
        stderr_pipe,
        dir.join("stderr"),
        tokio::io::stderr(),
        last_stderr.clone(),
        dir.clone(),
    ));
    let s1 = tokio::spawn(capture::watch_silence(
        "stdout",
        last_stdout,
        30_000,
        dir.clone(),
        cancel_rx.clone(),
    ));
    let s2 = tokio::spawn(capture::watch_silence(
        "stderr",
        last_stderr,
        30_000,
        dir.clone(),
        cancel_rx,
    ));

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
    let _ = stdout_tee.await;
    let _ = stderr_tee.await;
    let _ = s1.await;
    let _ = s2.await;

    Ok(Outcome {
        exit_code,
        merge: Merge::Split("not yet decided"),
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
