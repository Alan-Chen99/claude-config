use anyhow::{anyhow, Context, Result};
use std::path::Path;
use std::sync::Arc;

use crate::core;
use crate::events;
use crate::meta::{self, ChildMeta};
use crate::paths;

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
    let cm = ChildMeta {
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

    use std::sync::Mutex;

    // Shared with the callbacks below, which the core calls at the instant each
    // fact becomes true. Every lock site takes a poisoned guard rather than
    // unwrapping it: a panic here would end the wrapper by panic instead of
    // with the child's exit code, which the spec guarantees.
    let cm = Arc::new(Mutex::new(cm));

    // A failed `write_meta` is recorded as an event and discarded — in both
    // callbacks below and at the `drained_at` write after the core returns.
    // Bookkeeping is the wrapper's failure, not the child's, and must not
    // decide what the caller learns the child did: the exit code is guaranteed.
    // Only the spawn-error write still propagates, where there is no child
    // status to preserve.
    //
    // The cost of discarding is specific, and different per fact. A lost
    // `child_pid` shows as `pid -` in `ps` and in every pushed report, because
    // `status::render` reads the pid from disk — until a later write lands the
    // whole struct, or for the child's whole life if none does, while events
    // from this same process still carry the pid from memory. A lost reap
    // leaves disk saying `reaped: None`, and `status::derive` reads a live
    // wrapper with no reap as `producing`/`quiet` — a child that has already
    // exited, described as still running. A lost `drained_at` costs only the
    // `exited` -> `final` transition: with the reap on disk and the wrapper
    // gone, `derive` reaches `final(status)` anyway.
    let on_spawn = {
        let cm = cm.clone();
        let dir = child_dir.clone();
        let parent = parent_dir.clone();
        let desc = desc.clone();
        let cmdv = cmd.clone();
        move |pid: u32| {
            let mut m = cm.lock().unwrap_or_else(|poisoned| poisoned.into_inner());
            m.child_pid = Some(pid);
            record_meta_write(&parent, wrapper_pid, "child_pid", meta::write_meta(&dir, &m));
            events::append(
                &parent,
                "child_started",
                serde_json::json!({"wrapper_pid": wrapper_pid, "child_pid": pid, "desc": desc, "command": cmdv}),
            )
            .ok();
        }
    };

    let on_reap = {
        let cm = cm.clone();
        let dir = child_dir.clone();
        let parent = parent_dir.clone();
        move |code: i32| {
            // Before the drain, never after: a descendant holding the inherited
            // pipes can delay the drain indefinitely, and the status is known now.
            let mut m = cm.lock().unwrap_or_else(|poisoned| poisoned.into_inner());
            m.reaped = Some(meta::Reaped { at: chrono::Utc::now(), status: code });
            record_meta_write(&parent, wrapper_pid, "reaped", meta::write_meta(&dir, &m));
            events::append(
                &parent,
                "child_exit",
                serde_json::json!({"wrapper_pid": wrapper_pid, "child_pid": m.child_pid, "exit_code": code}),
            )
            .ok();
        }
    };

    let outcome = match core::run_core(&cmd, &child_dir, on_spawn, on_reap).await {
        Ok(o) => o,
        Err(core::CoreError::Spawn(e)) => {
            let mut m = cm.lock().unwrap_or_else(|poisoned| poisoned.into_inner());
            m.spawn_error = Some(e.to_string());
            meta::write_meta(&child_dir, &m)?;
            events::append(
                &parent_dir,
                "spawn_failed",
                serde_json::json!({"wrapper_pid": wrapper_pid, "command": cmd, "error": e.to_string()}),
            )
            .ok();
            return Err(anyhow!("spawn {:?}: {e}", cmd));
        }
        Err(core::CoreError::Other(e)) => return Err(e),
    };

    {
        let mut m = cm.lock().unwrap_or_else(|poisoned| poisoned.into_inner());
        m.drained_at = Some(chrono::Utc::now());
        // Recorded and discarded, like the callbacks' writes: policy above.
        record_meta_write(&parent_dir, wrapper_pid, "drained_at", meta::write_meta(&child_dir, &m));
    }
    events::append(&parent_dir, "drained", serde_json::json!({"wrapper_pid": wrapper_pid}))
        .ok();

    Ok(outcome.exit_code)
}

/// State a best-effort `meta.json` write that failed, so a fact lost to disk is
/// still readable somewhere. Shared by the three sites that discard the error;
/// the spawn-error write propagates instead and does not come through here.
fn record_meta_write(parent: &Path, wrapper_pid: u32, fact: &str, result: Result<()>) {
    if let Err(e) = result {
        events::append(
            parent,
            "meta_write_failed",
            serde_json::json!({"wrapper_pid": wrapper_pid, "fact": fact, "error": format!("{e:#}")}),
        )
        .ok();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn a_write_that_succeeded_is_not_worth_saying() {
        let dir = TempDir::new().unwrap();
        record_meta_write(dir.path(), 42, "reaped", Ok(()));
        assert!(events::read_all(dir.path()).unwrap().is_empty());
    }

    // The `child_pid` call site cannot be driven from an integration test: any
    // way of making its write fail also fails the propagating write that
    // precedes it, aborting the run before the callback. This covers the
    // sequence all three sites now share.
    #[test]
    fn a_failed_write_names_the_fact_and_the_error() {
        let dir = TempDir::new().unwrap();
        record_meta_write(
            dir.path(),
            42,
            "child_pid",
            Err(anyhow!("rename meta.json.tmp -> meta.json: Is a directory")),
        );

        let evts = events::read_all(dir.path()).unwrap();
        assert_eq!(evts.len(), 1);
        assert_eq!(evts[0].kind, "meta_write_failed");
        assert_eq!(evts[0].data["wrapper_pid"], 42);
        assert_eq!(evts[0].data["fact"], "child_pid");
        assert_eq!(
            evts[0].data["error"],
            "rename meta.json.tmp -> meta.json: Is a directory"
        );
    }
}
