use anyhow::{bail, Context, Result};
use chrono::Utc;
use std::collections::BTreeSet;
use std::fs::File;
use std::io::{Read, Seek, SeekFrom};
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant, SystemTime};

use crate::paths;
use crate::ps;
use crate::psrecord::Capture;
use crate::status::{self, Status};

/// A job launched in the same assistant message as the wait can start its
/// wrapper a moment after the wait does, so an empty scope is an error only
/// once this has passed.
const DISCOVERY_GRACE: Duration = Duration::from_secs(5);
const POLL: Duration = Duration::from_secs(1);
/// Enough of a task output file's end to hold its trailer line.
const TAIL_BYTES: u64 = 256;

/// `agent-tools wait`: block until a watched job ends or `max` passes, then
/// print where each stands. Exits 0 either way; the first line says which.
///
/// The caller is an agent nothing re-invokes when a background shell ends: a
/// subagent, or a main thread whose job ends with its final response (a
/// `claude -p` one, which 2.1.310 re-invokes unless `"tengu_tidy_sloth"` is
/// off). A subagent's prompt cache lives 5
/// minutes, and a message to it is delivered only when its current tool call
/// returns, so one bounded call per tool round keeps both working
/// (`notes/cc-2.1.289-subagent-waits.md`).
///
/// With no `files`, the jobs are this agent's runs through `agent-tools run`.
/// With `files`, they are Claude Code background task output files, which is
/// what reaches a job started without the wrapper.
pub fn run(max: Duration, files: Vec<PathBuf>) -> Result<()> {
    if files.is_empty() {
        wait_on_captures(max)
    } else {
        wait_on_task_files(max, &files)
    }
}

/// Scope is the agent the hook-set `AGENT_TOOLS_PARENT_DIR` names, minus the
/// tool call this runs in, so a wait wrapped in `agent-tools run` cannot wait
/// on itself.
fn wait_on_captures(max: Duration) -> Result<()> {
    let parent = paths::parent_dir_from_env()?;
    let (session, agent, own_group) = paths::parse_parent_dir(&parent)?;
    let session_dir = paths::state_root()?.join(&session);
    let started = Instant::now();
    let started_at = Utc::now();
    // A run counts once seen running, or when it started after the wait did:
    // a short one can start and end between two polls.
    let mut watched: BTreeSet<PathBuf> = BTreeSet::new();
    loop {
        let now = Utc::now();
        let mut all = Vec::new();
        ps::collect_captures(&session_dir, &mut all)?;
        let mine: Vec<(Capture, Status)> = all
            .into_iter()
            .filter(|c| c.agent_id == agent && c.tool_use_id != own_group)
            .map(|c| {
                let s = status::derive(&c.capture_dir, now);
                (c, s)
            })
            .collect();
        for (c, s) in &mine {
            let started_since = c.meta.as_ref().is_some_and(|m| m.started_at >= started_at);
            if s.key.is_still_running() || started_since {
                watched.insert(c.capture_dir.clone());
            }
        }
        let (running, ended): (Vec<_>, Vec<_>) = mine
            .iter()
            .filter(|(c, _)| watched.contains(&c.capture_dir))
            .partition(|(_, s)| s.key.is_still_running());
        let line = |(c, s): &&(Capture, Status)| status::render(&c.capture_dir, s, now);
        let ended: Vec<String> = ended.iter().map(line).collect();
        let running: Vec<String> = running.iter().map(line).collect();
        if !ended.is_empty() || (started.elapsed() >= max && !watched.is_empty()) {
            report(started, &ended, &running);
            return Ok(());
        }
        if watched.is_empty() && started.elapsed() >= DISCOVERY_GRACE {
            bail!(
                "nothing of this agent's is running under {}, so there is nothing to wait on. \
                 A command started without `agent-tools run` is invisible here: pass its task \
                 output file instead (`agent-tools wait <file>`). `agent-tools ps --all` lists \
                 what already ended.",
                session_dir.join(agent.as_deref().unwrap_or("")).display()
            );
        }
        std::thread::sleep(POLL);
    }
}

/// A file that has already ended when the wait starts is listed but does not
/// end the wait while another runs, so passing it again cannot turn the loop
/// into a busy poll; when every file has ended, the wait returns at once.
fn wait_on_task_files(max: Duration, files: &[PathBuf]) -> Result<()> {
    for f in files {
        if !f.is_file() {
            bail!(
                "{}: no such file. Pass the path a background launch printed after \
                 `Output is being written to:`.",
                f.display()
            );
        }
    }
    let started = Instant::now();
    let mut seen_running: BTreeSet<&PathBuf> = BTreeSet::new();
    loop {
        let now = SystemTime::now();
        let mut ended = Vec::new();
        let mut ended_before = Vec::new();
        let mut running = Vec::new();
        for f in files {
            let t = read_task_file(f)?;
            match t.trailer {
                Some(trailer) => {
                    let line = format!("{}: {trailer}, {}B", f.display(), t.bytes);
                    if seen_running.contains(f) {
                        ended.push(line);
                    } else {
                        ended_before.push(line);
                    }
                }
                None => {
                    seen_running.insert(f);
                    let age = now.duration_since(t.modified).unwrap_or_default();
                    let age = status::fmt_duration(age.as_secs_f64());
                    running.push(format!("{}: running, {}B, last write {age} ago", f.display(), t.bytes));
                }
            }
        }
        if !ended.is_empty() || running.is_empty() || started.elapsed() >= max {
            report(started, &ended, &running);
            if !ended_before.is_empty() {
                println!("ended before the wait:");
                ended_before.iter().for_each(|l| println!("  {l}"));
            }
            return Ok(());
        }
        std::thread::sleep(POLL);
    }
}

fn report(started: Instant, ended: &[String], running: &[String]) {
    let waited = status::fmt_duration(started.elapsed().as_secs_f64());
    if !ended.is_empty() {
        println!("ended within {waited} of waiting:");
        ended.iter().for_each(|l| println!("  {l}"));
        if !running.is_empty() {
            println!("still running:");
        }
    } else if !running.is_empty() {
        println!("nothing ended in {waited}; still running:");
    }
    running.iter().for_each(|l| println!("  {l}"));
}

struct TaskFile {
    bytes: u64,
    modified: SystemTime,
    trailer: Option<String>,
}

fn read_task_file(path: &Path) -> Result<TaskFile> {
    let mut f = File::open(path).with_context(|| format!("open {}", path.display()))?;
    let md = f.metadata().with_context(|| format!("stat {}", path.display()))?;
    f.seek(SeekFrom::Start(md.len().saturating_sub(TAIL_BYTES)))?;
    let mut tail = Vec::new();
    f.read_to_end(&mut tail)?;
    let tail = String::from_utf8_lossy(&tail);
    let last = tail.trim_end_matches('\n').rsplit('\n').next().unwrap_or("");
    Ok(TaskFile {
        bytes: md.len(),
        modified: md.modified()?,
        trailer: is_trailer(last).then(|| last.to_string()),
    })
}

/// The line Claude Code appends to a background shell task's output file when
/// the task ends (2.1.289): `[exited with code N]` (`unknown` when there is
/// none), or `[killed]`, which a TaskStop and the `-p` background time limit
/// both write (`notes/cc-2.1.289-subagent-waits.md`). `[stopped <reason>]`
/// is read off the decompile for served background commands and not seen here.
fn is_trailer(line: &str) -> bool {
    let Some(inner) = line.strip_prefix('[').and_then(|l| l.strip_suffix(']')) else {
        return false;
    };
    inner == "killed"
        || inner.strip_prefix("exited with code ").is_some_and(|c| !c.is_empty())
        || inner.strip_prefix("stopped ").is_some_and(|r| !r.is_empty())
}
