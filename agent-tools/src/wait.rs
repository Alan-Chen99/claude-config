use anyhow::{anyhow, bail, Context, Result};
use chrono::{DateTime, Utc};
use std::collections::BTreeSet;
use std::env;
use std::fs::{self, File};
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
/// A 5-minute cache, or one whose lifetime the transcript does not show: the
/// next request lands inside it with a minute to generate it. Held for the
/// whole wait, past the point where the wakes have cost more than one rebuild:
/// measured waits end too soon for a cold wait after it to pay
/// (`notes/cc-2.1.310-subagent-wait-costs.md`, finding 6).
const BOUND_5M: Duration = Duration::from_secs(240);
/// A 1-hour cache: ten minutes spare, as `scripts/cache-keepalive` takes.
const BOUND_1H: Duration = Duration::from_secs(3000);
/// What the call keeps of its own Bash `timeout` to print and exit before
/// Claude Code moves it to the background.
const TIMEOUT_MARGIN: Duration = Duration::from_secs(20);
/// How much of the transcript's end to search for the latest cache write.
const TRANSCRIPT_TAIL: u64 = 4 << 20;

/// `agent-tools wait`: block until a watched job ends, a message is queued
/// for the caller, or the bound passes, then print where each job stands.
/// Exits 0 in every one of those cases; the first line says which.
///
/// The caller is an agent nothing re-invokes when a background shell ends: a
/// subagent, or a main thread whose job ends with its final response (a
/// `claude -p` one, which 2.1.310 re-invokes unless `"tengu_tidy_sloth"` is
/// off). A message to it is delivered only when its current tool call
/// returns, and SendMessage never cuts that call short (2.1.310), so the wait
/// returns as soon as `hook-post` records one in its inbox. The bound keeps
/// the next request inside the prompt cache: a subagent's lives 5 minutes
/// unless its frontmatter sets `experimental.cacheTtl: 1h`
/// (`notes/cc-2.1.289-subagent-waits.md`, `agents/gp-cache1h.md`).
///
/// With no `files`, the jobs are this agent's runs through `agent-tools run`.
/// With `files`, they are Claude Code background task output files, which is
/// what reaches a job started without the wrapper.
pub fn run(max: Option<Duration>, print_bound: bool, files: Vec<PathBuf>) -> Result<()> {
    let caller = Caller::from_env()?;
    let (max, note) = bound(max, caller.as_ref())?;
    if print_bound {
        println!("{}", max.as_secs());
        if let Some(n) = note {
            println!("{n}");
        }
        return Ok(());
    }
    let inbox = match &caller {
        Some(c) => Some(paths::inbox_path(&c.session, c.agent.as_deref())?),
        None => None,
    };
    let w = Watch { max, inbox, started: Instant::now() };
    if files.is_empty() {
        let c = caller.ok_or_else(|| {
            anyhow!(
                "AGENT_TOOLS_PARENT_DIR is not set, so there is no agent whose `agent-tools run` \
                 jobs to watch: pass task output files instead"
            )
        })?;
        wait_on_captures(&w, &c)?;
    } else {
        wait_on_task_files(&w, &files)?;
    }
    if let Some(n) = note {
        println!("{n}");
    }
    Ok(())
}

/// The agent a hook-set `AGENT_TOOLS_PARENT_DIR` names, and the tool call this
/// wait runs in.
struct Caller {
    session: String,
    agent: Option<String>,
    own_group: String,
}

impl Caller {
    /// `None` only when the variable is absent: a wait run by hand on task
    /// files, which then has no inbox and no transcript to size its bound by.
    fn from_env() -> Result<Option<Caller>> {
        if env::var_os("AGENT_TOOLS_PARENT_DIR").is_none() {
            return Ok(None);
        }
        let parent = paths::parent_dir_from_env()?;
        let (session, agent, own_group) = paths::parse_parent_dir(&parent)?;
        Ok(Some(Caller { session, agent, own_group }))
    }
}

struct Watch {
    max: Duration,
    inbox: Option<PathBuf>,
    started: Instant,
}

impl Watch {
    /// The line announcing queued messages, if any are. `hook-post` empties
    /// the inbox when this agent's tool round ends, which is also when Claude
    /// Code delivers what is queued, so a line left there is still undelivered.
    fn messages(&self) -> Result<Option<String>> {
        let Some(path) = &self.inbox else { return Ok(None) };
        let text = match fs::read_to_string(path) {
            Ok(t) => t,
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Ok(None),
            Err(e) => return Err(e).with_context(|| format!("read {}", path.display())),
        };
        let entries: Vec<&str> = text.lines().filter(|l| !l.is_empty()).collect();
        let Some(last) = entries.last() else { return Ok(None) };
        let (at, from) = last
            .split_once('\t')
            .with_context(|| format!("{}: line without a tab: {last:?}", path.display()))?;
        let at = DateTime::parse_from_rfc3339(at)
            .with_context(|| format!("{}: bad time in {last:?}", path.display()))?;
        let age = (Utc::now() - at.with_timezone(&Utc)).num_milliseconds().max(0) as f64 / 1000.0;
        let age = status::fmt_duration(age);
        Ok(Some(if entries.len() == 1 {
            format!("a message from {from}, queued {age} ago, arrives with this result")
        } else {
            format!(
                "{} messages, the last from {from} queued {age} ago, arrive with this result",
                entries.len()
            )
        }))
    }
}

/// `explicit` when given, else for a subagent its cache lifetime read from
/// its transcript; either way short enough to return before the call's own
/// `timeout` (exported by `hook-pre` as `AGENT_TOOLS_CALL_TIMEOUT_MS`) moves
/// it to the background. A main thread keeps the 5-minute bound though its
/// cache lives an hour: its background agents' reports and its subagents'
/// messages also wait for its call to return, and no inbox records them. The
/// note says when the transcript could not be read, so a layout change in a
/// Claude Code release shows rather than silently costing an hour-cache agent
/// eleven extra wakes an hour.
fn bound(explicit: Option<Duration>, caller: Option<&Caller>) -> Result<(Duration, Option<String>)> {
    let (b, note) = match (explicit, caller) {
        (Some(d), _) => (d, None),
        (None, None) => (BOUND_5M, None),
        (None, Some(c)) if c.agent.is_none() => (BOUND_5M, None),
        (None, Some(c)) => match last_cache_write(c) {
            Ok(Some(Ttl::OneHour)) => (BOUND_1H, None),
            Ok(Some(Ttl::FiveMinutes)) | Ok(None) => (BOUND_5M, None),
            Err(e) => (
                BOUND_5M,
                Some(format!("note: waited as for a 5-minute cache, as its lifetime is unknown: {e:#}")),
            ),
        },
    };
    let b = match call_timeout()? {
        Some(t) => b.min(t.saturating_sub(TIMEOUT_MARGIN).max(POLL)),
        None => b,
    };
    Ok((b, note))
}

fn call_timeout() -> Result<Option<Duration>> {
    let Some(v) = env::var_os("AGENT_TOOLS_CALL_TIMEOUT_MS") else { return Ok(None) };
    let v = v.to_string_lossy();
    let ms: u64 = v
        .parse()
        .with_context(|| format!("AGENT_TOOLS_CALL_TIMEOUT_MS is not a whole number of milliseconds: {v:?}"))?;
    Ok(Some(Duration::from_millis(ms)))
}

enum Ttl {
    FiveMinutes,
    OneHour,
}

/// The lifetime of the caller's latest cache write, from the `usage` Claude
/// Code records on each assistant message: `None` when none in the
/// transcript's tail wrote anything, as before an agent's first response is
/// recorded. Records are matched on `agentId` so that nothing a fork carries
/// over from its parent decides it.
fn last_cache_write(c: &Caller) -> Result<Option<Ttl>> {
    let path = transcript(c)?;
    let mut f = File::open(&path).with_context(|| format!("open {}", path.display()))?;
    let len = f.metadata().with_context(|| format!("stat {}", path.display()))?.len();
    let start = len.saturating_sub(TRANSCRIPT_TAIL);
    f.seek(SeekFrom::Start(start))?;
    let mut buf = Vec::new();
    f.read_to_end(&mut buf)?;
    let text = String::from_utf8_lossy(&buf);
    // The first line of a tail cut mid-file is a fragment; the last may be one
    // still being written. Neither parses, and neither is the record sought.
    for line in text.lines().rev() {
        if !line.contains("\"cache_creation\"") {
            continue;
        }
        let Ok(r) = serde_json::from_str::<serde_json::Value>(line) else { continue };
        if r["type"] != "assistant" || r["agentId"].as_str() != c.agent.as_deref() {
            continue;
        }
        let cc = &r["message"]["usage"]["cache_creation"];
        if cc["ephemeral_1h_input_tokens"].as_u64().unwrap_or(0) > 0 {
            return Ok(Some(Ttl::OneHour));
        }
        if cc["ephemeral_5m_input_tokens"].as_u64().unwrap_or(0) > 0 {
            return Ok(Some(Ttl::FiveMinutes));
        }
    }
    Ok(None)
}

/// A subagent's transcript: `agent-<id>.jsonl` under
/// `<config>/projects/<cwd slug>/<session>/subagents/`, one level down for a
/// workflow's agents (`subagents/workflows/<run>/`), 2.1.310. The slug is
/// Claude Code's encoding of the launch directory, so it is found rather than
/// rebuilt.
fn transcript(c: &Caller) -> Result<PathBuf> {
    let agent = c.agent.as_deref().expect("only a subagent's bound is read from its transcript");
    let config = match env::var_os("CLAUDE_CONFIG_DIR") {
        Some(d) => PathBuf::from(d),
        None => PathBuf::from(env::var("HOME").context("HOME not set")?).join(".claude"),
    };
    let projects = config.join("projects");
    let entries = fs::read_dir(&projects).with_context(|| format!("list {}", projects.display()))?;
    let name = format!("agent-{agent}.jsonl");
    for e in entries.flatten() {
        if let Some(p) = find_file(&e.path().join(&c.session).join("subagents"), &name, 3) {
            return Ok(p);
        }
    }
    bail!(
        "no transcript {}/subagents/**/{name} in any project under {}",
        c.session,
        projects.display()
    )
}

fn find_file(dir: &Path, name: &str, depth: u32) -> Option<PathBuf> {
    let direct = dir.join(name);
    if direct.is_file() {
        return Some(direct);
    }
    if depth == 0 {
        return None;
    }
    fs::read_dir(dir)
        .ok()?
        .flatten()
        .map(|e| e.path())
        .filter(|p| p.is_dir())
        .find_map(|p| find_file(&p, name, depth - 1))
}

/// Scope is the caller's agent, minus the tool call this runs in, so a wait
/// wrapped in `agent-tools run` cannot wait on itself.
fn wait_on_captures(w: &Watch, c: &Caller) -> Result<()> {
    let session_dir = paths::state_root()?.join(&c.session);
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
            .filter(|cap| cap.agent_id == c.agent && cap.tool_use_id != c.own_group)
            .map(|cap| {
                let s = status::derive(&cap.capture_dir, now);
                (cap, s)
            })
            .collect();
        for (cap, s) in &mine {
            let started_since = cap.meta.as_ref().is_some_and(|m| m.started_at >= started_at);
            if s.key.is_still_running() || started_since {
                watched.insert(cap.capture_dir.clone());
            }
        }
        let (running, ended): (Vec<_>, Vec<_>) = mine
            .iter()
            .filter(|(cap, _)| watched.contains(&cap.capture_dir))
            .partition(|(_, s)| s.key.is_still_running());
        let line = |(cap, s): &&(Capture, Status)| status::render(&cap.capture_dir, s, now);
        let ended: Vec<String> = ended.iter().map(line).collect();
        let running: Vec<String> = running.iter().map(line).collect();
        let message = w.messages()?;
        if message.is_some() || !ended.is_empty() || (w.started.elapsed() >= w.max && !watched.is_empty()) {
            report(w.started, message, &ended, &running);
            return Ok(());
        }
        if watched.is_empty() && w.started.elapsed() >= DISCOVERY_GRACE {
            bail!(
                "nothing of this agent's is running under {}, so there is nothing to wait on. \
                 A command started without `agent-tools run` is invisible here: pass its task \
                 output file instead (`agent-tools wait <file>`). `agent-tools ps --all` lists \
                 what already ended.",
                session_dir.join(c.agent.as_deref().unwrap_or("")).display()
            );
        }
        std::thread::sleep(POLL);
    }
}

/// A file that has already ended when the wait starts is listed but does not
/// end the wait while another runs, so passing it again cannot turn the loop
/// into a busy poll; when every file has ended, the wait returns at once.
fn wait_on_task_files(w: &Watch, files: &[PathBuf]) -> Result<()> {
    for f in files {
        if !f.is_file() {
            bail!(
                "{}: no such file. Pass the path a background launch printed after \
                 `Output is being written to:`.",
                f.display()
            );
        }
    }
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
        let message = w.messages()?;
        if message.is_some() || !ended.is_empty() || running.is_empty() || w.started.elapsed() >= w.max {
            report(w.started, message, &ended, &running);
            if !ended_before.is_empty() {
                println!("ended before the wait:");
                ended_before.iter().for_each(|l| println!("  {l}"));
            }
            return Ok(());
        }
        std::thread::sleep(POLL);
    }
}

fn report(started: Instant, message: Option<String>, ended: &[String], running: &[String]) {
    if let Some(m) = message {
        println!("{m}");
    }
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
