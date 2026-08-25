use anyhow::{anyhow, Context, Result};
use std::process::Stdio;
use std::sync::atomic::AtomicI64;
use std::sync::Arc;
use tokio::process::Command;

use crate::capture;
use crate::events;
use crate::meta::{self, ChildMeta};
use crate::paths;
use crate::signals;

pub async fn run(desc: Option<String>, hide_cmdline: bool, cmd: Vec<String>) -> Result<i32> {
    if cmd.is_empty() {
        return Err(anyhow!("run: no command supplied after --"));
    }

    // Default: set a helpful process title (`comm`) so `ps -o comm=`
    // shows what this wrapper is running without hiding the full argv.
    // Clarity is the priority for general debugging.
    //
    // Opt-in: --hide-cmdline additionally overwrites /proc/self/cmdline
    // so peer processes reading `ps aux` cannot recover the `--desc`
    // string or the wrapped command line. Round-19 F88 named the leak:
    // E-k3-nodontact quoted verbatim `agent-tools run --desc E-k3-v8:
    // Kimi K3 + v8 + H17` from `ps aux`. `desc` remains available in
    // meta.json for the intended observability path regardless of this
    // flag; only the argv memory changes.
    let comm_hint = desc.as_deref().unwrap_or(&cmd[0]);
    if hide_cmdline {
        crate::procname::hide_cmdline(&format!("agent-tools: {}", cmd[0]));
    } else {
        crate::procname::set_comm(comm_hint);
    }

    let parent_dir = paths::parent_dir_from_env().map_err(|_| {
        anyhow!(
            "AGENT_TOOLS_PARENT_DIR is not set.\n\
             The PreToolUse hook (agent-tools hook-pre) must run before this command.\n\
             If you see this from inside a Claude Code Bash tool, the hook is not installed."
        )
    })?;
    std::fs::create_dir_all(&parent_dir)
        .with_context(|| format!("mkdir {}", parent_dir.display()))?;

    // The capture dir is named by the WRAPPER's pid: it exists before the
    // child does, so a command that fails to exec still has a directory to be
    // reported from.
    let wrapper_pid = std::process::id();
    let wrapper_started_ticks = crate::procstat::start_ticks(wrapper_pid)?;
    let child_dir = parent_dir.join(wrapper_pid.to_string());
    std::fs::create_dir_all(&child_dir)
        .with_context(|| format!("mkdir {}", child_dir.display()))?;

    let started_at = chrono::Utc::now();
    let mut cm = ChildMeta {
        wrapper_pid,
        wrapper_started_ticks,
        child_pid: None,
        desc: desc.clone(),
        command: cmd.clone(),
        started_at,
        spawn_error: None,
        reaped: None,
        drained_at: None,
    };
    meta::write_meta(&child_dir, &cm)?;

    let spawned = Command::new(&cmd[0])
        .args(&cmd[1..])
        .stdin(Stdio::inherit())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn();

    let mut child = match spawned {
        Ok(c) => c,
        Err(e) => {
            cm.spawn_error = Some(e.to_string());
            meta::write_meta(&child_dir, &cm)?;
            events::append(
                &parent_dir,
                "spawn_failed",
                serde_json::json!({"wrapper_pid": wrapper_pid, "command": cmd, "error": e.to_string()}),
            )
            .ok();
            return Err(anyhow!("spawn {:?}: {e}", cmd));
        }
    };

    let pid = child.id().context("child pid unavailable")?;
    cm.child_pid = Some(pid);
    meta::write_meta(&child_dir, &cm)?;
    events::append(
        &parent_dir,
        "child_started",
        serde_json::json!({"wrapper_pid": wrapper_pid, "child_pid": pid, "desc": desc, "command": cmd}),
    )
    .ok();

    let stdout_pipe = child.stdout.take().context("no stdout pipe")?;
    let stderr_pipe = child.stderr.take().context("no stderr pipe")?;

    let (cancel_tx, cancel_rx) = tokio::sync::watch::channel(false);
    signals::install_forwarding(pid as i32, cancel_rx.clone()).ok();

    let last_stdout = Arc::new(AtomicI64::new(chrono::Utc::now().timestamp_millis()));
    let last_stderr = Arc::new(AtomicI64::new(chrono::Utc::now().timestamp_millis()));

    let stdout_tee = tokio::spawn(capture::tee(
        "stdout",
        stdout_pipe,
        child_dir.join("stdout"),
        tokio::io::stdout(),
        last_stdout.clone(),
        child_dir.clone(),
    ));
    let stderr_tee = tokio::spawn(capture::tee(
        "stderr",
        stderr_pipe,
        child_dir.join("stderr"),
        tokio::io::stderr(),
        last_stderr.clone(),
        child_dir.clone(),
    ));
    let s1 = tokio::spawn(capture::watch_silence(
        "stdout",
        last_stdout,
        30_000,
        child_dir.clone(),
        cancel_rx.clone(),
    ));
    let s2 = tokio::spawn(capture::watch_silence(
        "stderr",
        last_stderr,
        30_000,
        child_dir.clone(),
        cancel_rx,
    ));

    let status = child.wait().await?;
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

    // Record the reap BEFORE draining. A descendant holding the inherited
    // pipes can delay the drain indefinitely; the status is known now.
    cm.reaped = Some(meta::Reaped { at: chrono::Utc::now(), status: exit_code });
    meta::write_meta(&child_dir, &cm)?;
    events::append(
        &parent_dir,
        "child_exit",
        serde_json::json!({"wrapper_pid": wrapper_pid, "child_pid": pid, "exit_code": exit_code}),
    )
    .ok();

    let _ = cancel_tx.send(true);
    let _ = stdout_tee.await;
    let _ = stderr_tee.await;
    let _ = s1.await;
    let _ = s2.await;

    cm.drained_at = Some(chrono::Utc::now());
    meta::write_meta(&child_dir, &cm)?;
    events::append(
        &parent_dir,
        "drained",
        serde_json::json!({"wrapper_pid": wrapper_pid}),
    )
    .ok();

    Ok(exit_code)
}
