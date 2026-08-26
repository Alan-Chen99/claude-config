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
