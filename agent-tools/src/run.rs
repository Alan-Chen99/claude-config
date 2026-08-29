use anyhow::{anyhow, Context, Result};
use std::path::Path;
use std::sync::{Arc, Mutex};

use crate::background;
use crate::core;
use crate::events;
use crate::meta::{self, ChildMeta};
use crate::paths;

pub async fn run(
    desc: Option<String>,
    hide_cmdline: bool,
    drain_cap_bytes: Option<u64>,
    reporter: Option<background::Reporter>,
    cmd: Vec<String>,
) -> Result<i32> {
    // A caller that asked for `--background` is blocked on this and on nothing
    // else, and its presence is the whole of "is this run backgrounded" — one
    // fact with one representation, rather than a flag beside it that could
    // come to disagree. Shared because the two sites that finish the protocol,
    // the spawn callback and the spawn-error arm below, are exclusive in fact
    // and not in a way the borrow checker can see: `on_spawn` is `FnOnce` and
    // must own what it consumes, while the error arm runs only if it never
    // fired.
    let reporter = Arc::new(Mutex::new(reporter));

    // A failure before the spawn is the caller's to hear about while it is
    // still listening. Without this every early return below reaches it as
    // "exited before saying whether it started" — the reason lost, and with it
    // the difference from the shell's `&` this flag exists to be.
    macro_rules! bail_to_caller {
        ($e:expr) => {{
            let e: anyhow::Error = $e;
            match take_reporter(&reporter) {
                Some(r) => r.failed(&e),
                None => return Err(e),
            }
        }};
    }

    if cmd.is_empty() {
        bail_to_caller!(anyhow!("no command supplied after --"));
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

    // `scope_for_run` picks the capture's home: a hook-set AGENT_TOOLS_PARENT_DIR
    // when one ran, otherwise the session's `user-shell` bucket for a `!` command
    // (which fires no hook at all), and a loud failure rather than a silent
    // demotion when the hook ran but left something unusable — see its doc
    // comment in paths.rs for why the three cases stay apart.
    let (parent_dir, _origin) = match paths::scope_for_run() {
        Ok(v) => v,
        Err(e) => bail_to_caller!(e),
    };
    match std::fs::create_dir_all(&parent_dir)
        .with_context(|| format!("mkdir {}", parent_dir.display()))
    {
        Ok(()) => {}
        Err(e) => bail_to_caller!(e),
    }

    // The capture dir is named by the WRAPPER's pid: it exists before the
    // child does, so a command that fails to exec still has a directory to be
    // reported from.
    let wrapper_pid = std::process::id();
    let wrapper_started_ticks = match crate::procstat::start_ticks(wrapper_pid) {
        Ok(t) => t,
        Err(e) => bail_to_caller!(e),
    };
    let started_at = chrono::Utc::now();
    // Parsed once so `claude_pid` and `claude_started_ticks` cannot end up
    // describing two different pids if one of these call sites is edited
    // later without the other.
    let claude_pid: Option<u32> = std::env::var("CLAUDE_PID")
        .ok()
        .and_then(|s| s.parse().ok());
    let claude_started_ticks = claude_pid.and_then(|pid| crate::procstat::start_ticks(pid).ok());
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
        merge: None,
        forward_closed: false,
        drain_capped: false,
        capture_error: None,
        claude_pid,
        claude_started_ticks,
    };
    let child_dir = match publish_child_dir(&parent_dir, wrapper_pid, &cm) {
        Ok(d) => d,
        Err(e) => bail_to_caller!(e),
    };

    // Shared with the callbacks below, which the core calls at the instant each
    // fact becomes true. Every lock site takes a poisoned guard rather than
    // unwrapping it: a panic here would end the wrapper by panic instead of
    // with the child's exit code, which the spec guarantees.
    let cm = Arc::new(Mutex::new(cm));

    // Five sites write `meta.json`. At four of them — both callbacks below, the
    // `drained_at` write after the core returns, and the spawn-error write — a
    // failed write is recorded as an event and discarded. Bookkeeping is the
    // wrapper's failure, not the child's, and must not decide what the caller
    // learns the child did.
    //
    // The fifth is the pre-spawn write above, whose failure reaches the caller
    // — by return, or through the reporter when the run is backgrounded — and
    // displaces nothing by doing so: no child exists yet, and `run` goes no
    // further, so there is no child status for the write error to stand in
    // place of and no later fault it could be reported instead of.
    //
    // The cost of discarding is specific, and different per fact. The
    // `child_pid` write carries two, and loses both together. A lost pid shows
    // as `pid -` in `ps` and in every pushed report, because `status::render`
    // reads the pid from disk — until a later write lands the whole struct, or
    // for the child's whole life if none does, while events from this same
    // process still carry the pid from memory. A lost `merge` costs the reason
    // a capture has the shape it has: `status::render` reads the condition from
    // disk to decide whether a split lost interleaving the caller had, so the
    // note that split is owed goes unsaid, for exactly as long as the pid does.
    // The write is named for the pid alone in the event stream, because that is
    // the site's name and not an inventory of what rode on it. A lost reap
    // leaves disk saying `reaped: None`, and `status::derive` reads a live
    // wrapper with no reap as `producing`/`quiet` — a child that has already
    // exited, described as still running. A lost `drained_at` costs only the
    // `exited` -> `final` transition: with the reap on disk and the wrapper
    // gone, `derive` reaches `final(status)` anyway. A lost spawn error costs
    // the reason: `derive` sees no spawn error, no reap and a wrapper that has
    // already gone, and answers `abandoned` rather than `spawn-failed(...)`.
    //
    // A failed spawn is the one site with no child status to preserve, so
    // nothing about the exit code argues for discarding there. What argues for
    // it is the report: the spawn error is the only fault there is, and
    // propagating the write error would return that in its place and skip the
    // `spawn_failed` event below it, leaving the thing that actually went wrong
    // the one thing never said.
    //
    // That argument is the whole of the reason, and no test holds it up.
    // `run_facts_test::spawn_failure_is_recorded` drives only this write's
    // success path, and the failure path is out of an integration test's reach
    // for the same cause the `child_pid` site's is: anything that makes this
    // write fail also fails the pre-spawn write, which propagates and ends the
    // run before a spawn is ever attempted. A `?` here would leave the whole
    // suite green — measured — so the reason is written down rather than left
    // to be found by mutating.
    let on_spawn = {
        let cm = cm.clone();
        let dir = child_dir.clone();
        let parent = parent_dir.clone();
        let desc = desc.clone();
        let cmdv = cmd.clone();
        let reporter = reporter.clone();
        move |pid: u32, merge: &'static str| {
            let mut m = cm.lock().unwrap_or_else(|poisoned| poisoned.into_inner());
            m.child_pid = Some(pid);
            // Decided before the spawn, so it lands with the first fact there is
            // a child for: a capture's shape is explicable from the moment there
            // is a capture, rather than only once the wrapper is done with it.
            // The other three are true mid-run at the earliest and cannot.
            m.merge = Some(merge.to_string());
            record_meta_write(
                &parent,
                wrapper_pid,
                "child_pid",
                meta::write_meta(&dir, &m),
            );
            events::append(
                &parent,
                "child_started",
                serde_json::json!({"wrapper_pid": wrapper_pid, "child_pid": pid, "desc": desc, "command": cmdv}),
            )
            .ok();
            // Last, so everything a reader goes looking for on the strength of
            // this line is already on disk when the caller receives it. Here
            // rather than anywhere earlier because this is where the child pid
            // becomes knowable, and a start nobody can name is one nobody can
            // watch, kill, or wait for.
            //
            // The directory is escaped for the reason `ChildMeta::display_name`
            // escapes: this line is read one line at a time, so a scope
            // directory whose name carries a newline would print a second line
            // that reads as a status line for a run that does not exist.
            // Nothing else here can — the pids are numbers, and `--desc` never
            // reaches this line.
            if let Some(r) = take_reporter(&reporter) {
                r.started(&format!(
                    "{}  wrapper pid {wrapper_pid}  child pid {pid}",
                    meta::escape_control(&dir.display().to_string())
                ));
            }
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
            m.reaped = Some(meta::Reaped {
                at: chrono::Utc::now(),
                status: code,
            });
            record_meta_write(&parent, wrapper_pid, "reaped", meta::write_meta(&dir, &m));
            events::append(
                &parent,
                "child_exit",
                serde_json::json!({"wrapper_pid": wrapper_pid, "child_pid": m.child_pid, "exit_code": code}),
            )
            .ok();
        }
    };

    // The same fact as the reporter's presence, read off the same cell rather
    // than off a second flag beside it: a run with a report still to make is a
    // run whose caller has already been answered and moved on, so forwarding to
    // this process's descriptors would write into whatever it ran next. The
    // capture is the whole record there.
    let destination = if reporter
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
        .is_some()
    {
        core::Destination::Nowhere
    } else {
        core::Destination::Caller
    };

    let outcome = match core::run_core(
        &cmd,
        &child_dir,
        drain_cap_bytes,
        destination,
        on_spawn,
        on_reap,
    )
    .await
    {
        Ok(o) => o,
        Err(core::CoreError::Spawn(e)) => {
            let mut m = cm.lock().unwrap_or_else(|poisoned| poisoned.into_inner());
            m.spawn_error = Some(e.to_string());
            record_meta_write(
                &parent_dir,
                wrapper_pid,
                "spawn_error",
                meta::write_meta(&child_dir, &m),
            );
            events::append(
                &parent_dir,
                "spawn_failed",
                serde_json::json!({"wrapper_pid": wrapper_pid, "command": cmd, "error": e.to_string()}),
            )
            .ok();
            // The spawn is the last thing that can fail before a child exists,
            // so `on_spawn` never ran and the report is still unmade. Without
            // this the caller learns only that the wrapper exited, and the one
            // thing that actually went wrong is the one thing never said.
            let failed = anyhow!("spawn {:?}: {e}", cmd);
            if let Some(r) = take_reporter(&reporter) {
                r.failed(&failed);
            }
            return Err(failed);
        }
        Err(core::CoreError::Other(e)) => {
            // Raised on both sides of the spawn: `run_core` reports its pipe
            // and directory failures under this name as well as its failures to
            // wait on a running child. Which one this is needs no test here,
            // because the cell answers it — `on_spawn` empties it the instant a
            // child exists — so a failure before any start is reported, and one
            // after it is not reported twice.
            if let Some(r) = take_reporter(&reporter) {
                r.failed(&e);
            }
            return Err(e);
        }
    };

    {
        let mut m = cm.lock().unwrap_or_else(|poisoned| poisoned.into_inner());
        m.drained_at = Some(chrono::Utc::now());
        // The core's end-of-run facts ride the same write as `drained_at`, so a
        // reader never finds a drained capture whose difference from bare is
        // missing. `merge` is not among them: it was known before the child
        // existed and went to disk with the pid.
        m.forward_closed = outcome.forward_closed;
        m.drain_capped = outcome.drain_capped;
        m.capture_error = outcome.capture_error.clone();
        // Recorded and discarded, like the callbacks' writes: policy above.
        record_meta_write(
            &parent_dir,
            wrapper_pid,
            "drained_at",
            meta::write_meta(&child_dir, &m),
        );
    }
    events::append(
        &parent_dir,
        "drained",
        serde_json::json!({"wrapper_pid": wrapper_pid}),
    )
    .ok();

    Ok(outcome.exit_code)
}

/// Take the one report the caller is still blocking on, if nothing has made it
/// yet.
///
/// Presence is the whole state of the protocol: the reporter stays here until
/// either there is a child to name or the run has failed before there was one,
/// and exactly one of those consumes it. A site that finds it gone is a site
/// running after the caller has already been answered, and its silence is
/// correct — a second report would be written to a pipe nobody is reading.
///
/// A poisoned lock is taken rather than unwrapped, for the reason the `cm`
/// lock's sites give and one more: a panic here would leave the caller blocked
/// on a pipe until this process dies, and then reading nothing.
fn take_reporter(cell: &Mutex<Option<background::Reporter>>) -> Option<background::Reporter> {
    cell.lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
        .take()
}

/// State a best-effort `meta.json` write that failed, so a fact lost to disk is
/// still readable somewhere. Every write made once there is a child to report on
/// comes through here: the fault that reaches the caller is the one the run had,
/// never the one recording it had. The pre-spawn write in `run` is the fifth
/// site and the exception, propagating because it has no child status to
/// displace; the policy comment above it is where that is argued.
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

/// Create the capture directory holding its first `meta.json`, so that no
/// scanner ever sees the one without the other.
///
/// `hook_post` and `ps` both select capture directories by a numeric name and
/// derive `abandoned` — a terminal key — from one whose meta will not read. A
/// scan landing between a plain `mkdir` and the first meta write therefore
/// reports a child that is merely starting as terminally gone. Building under a
/// name those scanners skip and renaming into place closes that window: rename
/// is atomic, so the pid-named directory only ever exists complete.
fn publish_child_dir(
    parent_dir: &std::path::Path,
    wrapper_pid: u32,
    cm: &ChildMeta,
) -> Result<std::path::PathBuf> {
    let child_dir = parent_dir.join(wrapper_pid.to_string());
    // A directory already under this name belongs to an earlier wrapper whose
    // pid this one reuses. It is already published with a meta in it, so there
    // is no coming-into-existence for a scanner to catch; write in place. Two
    // *live* wrappers holding one pid would need separate pid namespaces over a
    // shared scope directory; there the rename below fails and the wrapper says
    // so, rather than the two children silently sharing one capture.
    if child_dir.is_dir() {
        meta::write_meta(&child_dir, cm)?;
        return Ok(child_dir);
    }
    let staging = parent_dir.join(format!(".starting-{wrapper_pid}"));
    std::fs::create_dir_all(&staging).with_context(|| format!("mkdir {}", staging.display()))?;
    meta::write_meta(&staging, cm)?;
    std::fs::rename(&staging, &child_dir)
        .with_context(|| format!("rename {} -> {}", staging.display(), child_dir.display()))?;
    Ok(child_dir)
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    /// Both scanners select capture directories by a numeric name and derive
    /// `abandoned` — a terminal key — when the meta inside will not read. A
    /// directory must therefore never carry its final name before its meta is
    /// in it.
    #[test]
    fn a_capture_directory_is_never_visible_without_its_meta() {
        use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
        use std::sync::Arc;

        let dir = TempDir::new().unwrap();
        let parent = dir.path().to_path_buf();
        let stop = Arc::new(AtomicBool::new(false));
        let sightings = Arc::new(AtomicUsize::new(0));

        let scanner = {
            let parent = parent.clone();
            let stop = Arc::clone(&stop);
            let sightings = Arc::clone(&sightings);
            std::thread::spawn(move || {
                while !stop.load(Ordering::Relaxed) {
                    let Ok(entries) = std::fs::read_dir(&parent) else {
                        continue;
                    };
                    for e in entries.flatten() {
                        let named_for_a_pid = e
                            .file_name()
                            .to_str()
                            .map(|n| n.parse::<u32>().is_ok())
                            .unwrap_or(false);
                        if named_for_a_pid && !e.path().join("meta.json").exists() {
                            sightings.fetch_add(1, Ordering::Relaxed);
                        }
                    }
                }
            })
        };

        for pid in 1..=500u32 {
            let cm = ChildMeta {
                wrapper_pid: pid,
                wrapper_started_ticks: 1,
                child_pid: None,
                desc: None,
                command: vec!["true".to_string()],
                started_at: chrono::Utc::now(),
                spawn_error: None,
                reaped: None,
                drained_at: None,
                merge: None,
                forward_closed: false,
                drain_capped: false,
                capture_error: None,
                claude_pid: None,
                claude_started_ticks: None,
            };
            publish_child_dir(&parent, pid, &cm).unwrap();
        }
        stop.store(true, Ordering::Relaxed);
        scanner.join().unwrap();

        assert_eq!(
            sightings.load(Ordering::Relaxed),
            0,
            "a scanner saw a capture directory with no meta.json in it"
        );
    }

    #[test]
    fn a_write_that_succeeded_is_not_worth_saying() {
        let dir = TempDir::new().unwrap();
        record_meta_write(dir.path(), 42, "reaped", Ok(()));
        assert!(events::read_all(dir.path()).unwrap().events.is_empty());
    }

    // The `child_pid` call site cannot be driven from an integration test: any
    // way of making its write fail also fails the propagating write that
    // precedes it, aborting the run before the callback. This covers the
    // sequence all four sites share.
    #[test]
    fn a_failed_write_names_the_fact_and_the_error() {
        let dir = TempDir::new().unwrap();
        record_meta_write(
            dir.path(),
            42,
            "child_pid",
            Err(anyhow!("rename meta.json.tmp -> meta.json: Is a directory")),
        );

        let evts = events::read_all(dir.path()).unwrap().events;
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
