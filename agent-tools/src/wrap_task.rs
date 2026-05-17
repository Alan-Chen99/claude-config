use anyhow::{anyhow, Context, Result};
use std::path::PathBuf;
use std::process::Stdio;
use std::sync::Arc;
use std::sync::atomic::AtomicI64;
use tokio::process::Command;

use crate::capture;
use crate::events;
use crate::meta::{self, Meta};
use crate::signals;

pub async fn run(task_dir: PathBuf) -> Result<i32> {
    if !task_dir.is_dir() {
        return Err(anyhow!("task_dir does not exist: {}", task_dir.display()));
    }
    let command_sh = task_dir.join("command.sh");
    if !command_sh.is_file() {
        return Err(anyhow!("missing command.sh under {}", task_dir.display()));
    }
    let stdout_path = task_dir.join("stdout");
    let stderr_path = task_dir.join("stderr");

    let mut cmd = Command::new("bash");
    cmd.args(["--noprofile", "--norc"])
        .arg(&command_sh)
        .env("AGENT_TOOLS_TASK_ID", &task_dir)
        .stdin(Stdio::inherit())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    strip_mitm_proxy_env(&mut cmd);
    let mut child = cmd
        .spawn()
        .with_context(|| "spawn bash for command.sh")?;
    let pid = child.id().context("child pid unavailable")? as i32;

    let mut current = meta::read_meta(&task_dir)?;
    if let Meta::Task(ref mut t) = current {
        t.pid = Some(pid as u32);
        t.started_at = Some(chrono::Utc::now());
    }
    meta::write_meta(&task_dir, &current)?;
    events::append(&task_dir, "task_started", serde_json::json!({"pid": pid})).ok();

    let stdout_pipe = child.stdout.take().context("no stdout pipe")?;
    let stderr_pipe = child.stderr.take().context("no stderr pipe")?;

    let (cancel_tx, cancel_rx) = tokio::sync::watch::channel(false);
    signals::install_forwarding(pid, cancel_rx.clone()).ok();

    let last_stdout = Arc::new(AtomicI64::new(chrono::Utc::now().timestamp_millis()));
    let last_stderr = Arc::new(AtomicI64::new(chrono::Utc::now().timestamp_millis()));

    let silence_threshold = if let Meta::Task(t) = &current { t.silence_threshold_ms } else { 30_000 };

    let tdir = task_dir.clone();
    let stdout_tee = tokio::spawn(capture::tee(
        "stdout",
        stdout_pipe,
        stdout_path.clone(),
        tokio::io::stdout(),
        last_stdout.clone(),
        tdir.clone(),
    ));
    let stderr_tee = tokio::spawn(capture::tee(
        "stderr",
        stderr_pipe,
        stderr_path.clone(),
        tokio::io::stderr(),
        last_stderr.clone(),
        tdir.clone(),
    ));

    let s1 = tokio::spawn(capture::watch_silence(
        "stdout",
        last_stdout,
        silence_threshold,
        tdir.clone(),
        cancel_rx.clone(),
    ));
    let s2 = tokio::spawn(capture::watch_silence(
        "stderr",
        last_stderr,
        silence_threshold,
        tdir.clone(),
        cancel_rx,
    ));

    let status = child.wait().await?;
    let _ = cancel_tx.send(true);
    let _ = stdout_tee.await;
    let _ = stderr_tee.await;
    let _ = s1.await;
    let _ = s2.await;

    let exit_code = status.code().unwrap_or_else(|| {
        #[cfg(unix)]
        {
            use std::os::unix::process::ExitStatusExt;
            if let Some(sig) = status.signal() { return 128 + sig; }
        }
        1
    });

    if let Meta::Task(ref mut t) = current {
        t.ended_at = Some(chrono::Utc::now());
        t.exit_code = Some(exit_code);
    }
    meta::write_meta(&task_dir, &current)?;
    events::append(&task_dir, "task_exit", serde_json::json!({"exit_code": exit_code})).ok();

    Ok(exit_code)
}

/// MITM intercept env is stripped so user bash commands don't route through
/// the Claude API intercept proxy. Mirrors the exports in
/// `/workspace/scripts/claude.sh`.
fn strip_mitm_proxy_env(cmd: &mut Command) {
    const VARS: &[&str] = &["HTTPS_PROXY", "NODE_EXTRA_CA_CERTS", "NODE_OPTIONS"];
    for v in VARS {
        cmd.env_remove(v);
    }
}
