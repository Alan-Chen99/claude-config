use anyhow::{Context, Result};
use chrono::Utc;
use nix::sys::signal;
use nix::unistd::Pid;
use std::fmt::Write as _;
use std::fs;
use std::path::{Path, PathBuf};

use crate::events::{self, Event};
use crate::meta::{self, ChildMeta, Meta, TaskMeta};
use crate::paths;

pub fn run(task_filter: Option<String>, session_override: Option<String>) -> Result<()> {
    let session_id = match session_override {
        Some(s) => s,
        None => {
            let task_dir = paths::task_dir_from_env()
                .context("AGENT_TOOLS_TASK_ID is not set; pass --session-id or run inside a wrap-task")?;
            let (sid, _, _) = paths::parse_task_dir(&task_dir)?;
            sid
        }
    };

    let session_dir = paths::state_root()?.join(&session_id);
    if !session_dir.is_dir() {
        println!("session: {session_id}");
        println!("(no state on disk)");
        return Ok(());
    }

    let mut buf = String::new();
    writeln!(buf, "session: {session_id}")?;

    let mut tasks: Vec<(Option<String>, TaskMeta, PathBuf)> = Vec::new();
    collect_tasks(&session_dir, None, &mut tasks)?;

    if let Some(ref t) = task_filter {
        tasks.retain(|(_, m, _)| &m.task_id == t);
    }
    tasks.sort_by_key(|(_, m, _)| m.started_at.unwrap_or_else(Utc::now));

    let mut current_agent: Option<String> = None;
    let mut all_events: Vec<(String, Event)> = Vec::new();
    for (agent_id, meta, task_dir) in &tasks {
        if agent_id != &current_agent {
            current_agent = agent_id.clone();
            writeln!(buf, "agent: {}", agent_id.clone().unwrap_or_else(|| "_main".into()))?;
        }
        write_task(&mut buf, meta, task_dir)?;
        if let Ok(evts) = events::read_all(task_dir) {
            for e in evts { all_events.push((meta.task_id.clone(), e)); }
        }
    }

    all_events.sort_by_key(|(_, e)| e.ts);
    if !all_events.is_empty() {
        writeln!(buf, "\nevents (chronological, all tasks):")?;
        for (tid, e) in &all_events {
            writeln!(buf, "  {}  {:<20} {:<20} {}",
                e.ts.format("%H:%M:%S%.3f"), e.kind, tid, e.data)?;
        }
    }

    print!("{buf}");
    Ok(())
}

fn collect_tasks(
    dir: &Path,
    agent: Option<String>,
    out: &mut Vec<(Option<String>, TaskMeta, PathBuf)>,
) -> Result<()> {
    let rd = fs::read_dir(dir)?;
    for entry in rd {
        let entry = entry?;
        let path = entry.path();
        if !path.is_dir() {
            continue;
        }
        let meta_path = path.join("meta.json");
        if meta_path.is_file() {
            if let Ok(Meta::Task(t)) = meta::read_meta(&path) {
                out.push((agent.clone(), t, path));
            }
        } else if agent.is_none() {
            let aid = path.file_name().unwrap().to_string_lossy().into_owned();
            collect_tasks(&path, Some(aid), out)?;
        }
    }
    Ok(())
}

fn write_task(buf: &mut String, m: &TaskMeta, task_dir: &Path) -> Result<()> {
    let live = is_live(m);
    let status = if live {
        "[running]".to_string()
    } else {
        format!("[exited {}]", m.exit_code.map(|c| c.to_string()).unwrap_or_else(|| "?".into()))
    };
    writeln!(buf, "\ntask {} {}", m.task_id, status)?;
    if let Some(d) = &m.desc {
        writeln!(buf, "  desc:           {d}")?;
    }
    if let Some(s) = m.started_at {
        let dur = (Utc::now() - s).num_seconds().max(0);
        writeln!(buf, "  started:        {}  ({}s ago)", s.format("%Y-%m-%dT%H:%M:%SZ"), dur)?;
    }
    writeln!(buf, "  silence-warn:   {}ms", m.silence_threshold_ms)?;
    if let Some(p) = m.pid { writeln!(buf, "  pid:            {p}")?; }
    let cmd_path = task_dir.join("command.sh");
    if cmd_path.is_file() {
        let raw = fs::read_to_string(&cmd_path).unwrap_or_default();
        let trimmed: String = raw.chars().take(120).collect();
        writeln!(buf, "  cmd (truncated): {trimmed}")?;
    }
    let stdout_p = task_dir.join("stdout");
    let stderr_p = task_dir.join("stderr");
    writeln!(buf, "  stdout:         {}  ({} bytes)",
        stdout_p.display(),
        stdout_p.metadata().map(|m| m.len()).unwrap_or(0))?;
    writeln!(buf, "  stderr:         {}  ({} bytes)",
        stderr_p.display(),
        stderr_p.metadata().map(|m| m.len()).unwrap_or(0))?;

    let children_dir = task_dir.join("children");
    if children_dir.is_dir() {
        let mut kids: Vec<ChildMeta> = Vec::new();
        if let Ok(rd) = fs::read_dir(&children_dir) {
            for entry in rd.flatten() {
                let p = entry.path();
                if p.is_dir() {
                    if let Ok(Meta::Child(c)) = meta::read_meta(&p) {
                        kids.push(c);
                    }
                }
            }
        }
        kids.sort_by_key(|c| c.started_at.unwrap_or_else(Utc::now));
        if !kids.is_empty() {
            writeln!(buf, "  children:")?;
            for c in &kids {
                let st = if c.ended_at.is_none() && is_pid_alive(c.pid as i32) {
                    "[running]".to_string()
                } else {
                    format!("[exited {}]", c.exit_code.map(|e| e.to_string()).unwrap_or_else(|| "?".into()))
                };
                writeln!(buf, "    pid {} {}", c.pid, st)?;
                if let Some(d) = &c.desc { writeln!(buf, "      desc:     {d}")?; }
                writeln!(buf, "      cmd:      {}", c.command.join(" "))?;
                writeln!(buf, "      stdout:   {}", task_dir.join("children").join(c.pid.to_string()).join("stdout").display())?;
                writeln!(buf, "      stderr:   {}", task_dir.join("children").join(c.pid.to_string()).join("stderr").display())?;
            }
        }
    }
    Ok(())
}

fn is_live(m: &TaskMeta) -> bool {
    if m.ended_at.is_some() { return false; }
    match m.pid {
        Some(p) => is_pid_alive(p as i32),
        None => true,
    }
}

fn is_pid_alive(pid: i32) -> bool {
    signal::kill(Pid::from_raw(pid), None).is_ok()
}
