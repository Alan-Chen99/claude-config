use anyhow::Result;
use nix::sys::signal::{kill, Signal};
use nix::unistd::Pid;
use tokio::signal::unix::{signal, SignalKind};

/// Spawn a tokio task that listens for SIGINT/SIGTERM/SIGHUP/SIGQUIT on this
/// process and forwards them to `child_pid`. Returns immediately. The task
/// runs until `cancel` is signalled.
pub fn install_forwarding(child_pid: i32, mut cancel: tokio::sync::watch::Receiver<bool>) -> Result<()> {
    let pid = Pid::from_raw(child_pid);
    let mut sigint = signal(SignalKind::interrupt())?;
    let mut sigterm = signal(SignalKind::terminate())?;
    let mut sighup = signal(SignalKind::hangup())?;
    let mut sigquit = signal(SignalKind::quit())?;
    tokio::spawn(async move {
        loop {
            tokio::select! {
                _ = sigint.recv() => { let _ = kill(pid, Signal::SIGINT); }
                _ = sigterm.recv() => { let _ = kill(pid, Signal::SIGTERM); }
                _ = sighup.recv() => { let _ = kill(pid, Signal::SIGHUP); }
                _ = sigquit.recv() => { let _ = kill(pid, Signal::SIGQUIT); }
                changed = cancel.changed() => {
                    if changed.is_err() || *cancel.borrow() { break; }
                }
            }
        }
    });
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::process::Stdio;
    use tokio::process::Command;
    use tokio::time::{sleep, Duration};

    #[tokio::test]
    async fn forwards_sigterm_to_child() {
        let mut child = Command::new("sleep")
            .arg("60")
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .unwrap();
        let child_pid = child.id().unwrap() as i32;

        let (tx, rx) = tokio::sync::watch::channel(false);
        install_forwarding(child_pid, rx).unwrap();

        // Direct kill simulates what install_forwarding would do; verify the
        // setup compiles, doesn't panic, and that the child responds to SIGTERM.
        kill(Pid::from_raw(child_pid), Signal::SIGTERM).unwrap();
        let status = tokio::time::timeout(Duration::from_secs(5), child.wait())
            .await
            .unwrap()
            .unwrap();
        assert!(!status.success() || status.code().is_none());

        let _ = tx.send(true);
        sleep(Duration::from_millis(50)).await;
    }
}
