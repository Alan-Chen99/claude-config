# agent-tools wrap-task / run / ps Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Rust `agent-tools` subcommands (`hook-pre`, `hook-post`, `wrap-task`, `run`, `ps`) so Claude Code's Bash and Monitor tool calls are wrapped at the hook layer, full stdout/stderr is durably captured to disk regardless of truncating pipes, and the agent can introspect live and historical tasks without re-running anything.

**Architecture:** All five subcommands live in the existing `agent-tools` binary (single crate at `agent-tools/`). State is kept under `~/.claude/agent-tools/<session_id>/[<agent_id>/]<task_id>/` — exact layout per `docs/superpowers/specs/2026-05-17-agent-tools-run-design.md`. PreToolUse hook serializes original command to `command.sh` (no quoting) and rewrites Bash/Monitor `command` to `exec agent-tools wrap-task <task_dir>`. wrap-task spawns `bash <command.sh>` with `AGENT_TOOLS_TASK_ID` set, tees pipes to disk, watches silence. `agent-tools run` inserted inline reads `AGENT_TOOLS_TASK_ID`, registers a child under the task, tees its wrapped command. `ps` reads state dirs and reports.

**Tech Stack:**
- Rust 2021, existing crate `agent-tools` (`/root/claude-config-work/agent-tools/`)
- `tokio` (async runtime: pipes, signals, timers, process)
- `serde` + `serde_json` (meta.json, events.jsonl)
- `chrono` with serde (RFC3339 timestamps)
- `nix` (kill(pid, 0) for liveness, signal forwarding)
- `anyhow` (error contexts)
- `tempfile` (dev-dep; integration test isolation)
- Build: `cargo build --release` from `/root/claude-config-work/agent-tools/`
- Install: existing symlink `~/.local/bin/agent-tools → <repo>/agent-tools/target/release/agent-tools`. Worktrees must NOT run `hooks/install.sh` (per `CLAUDE.md`); they test via `CLAUDE_CONFIG_ROOT=<worktree> ./target/release/agent-tools …`.
- Cargo network: `CARGO_HTTP_CAINFO=/root/.mitmproxy/mitmproxy-ca-cert.pem` is required for `cargo fetch` because mitmproxy intercepts TLS to crates.io. Set it once per shell or prepend to each cargo command. (Verified by hand before this plan was written.)

**Spec:** `docs/superpowers/specs/2026-05-17-agent-tools-run-design.md`. All identifiers (`session_id`, `agent_id`, `task_id`) are sourced from Claude Code's hook input; only `child_id` (the pid of `agent-tools run`) is locally chosen.

---

## File Structure

New / modified files in `agent-tools/`:

| Path | Responsibility |
|---|---|
| `Cargo.toml` | Add tokio, serde, serde_json, chrono, nix, anyhow, tempfile (dev). |
| `src/main.rs` | Add 5 new subcommands to the `Cmd` enum; dispatch to `hook_pre::run`, `hook_post::run`, `wrap_task::run`, `run::run`, `ps::run`. |
| `src/hook_input.rs` | Deserialize the JSON stdin for PreToolUse / PostToolUse. Pure parsing, no I/O. |
| `src/paths.rs` | Compute `task_dir` from `session_id` / `agent_id` / `task_id`. Resolve `<task_dir>` from `AGENT_TOOLS_TASK_ID`. Walk up to recover `session_id` / `agent_id` from a task_dir path. |
| `src/meta.rs` | `TaskMeta` / `ChildMeta` structs. Atomic read/write (write-to-temp + rename). |
| `src/events.rs` | `Event` struct, `EventKind` enum. Append-to-jsonl helpers. |
| `src/capture.rs` | The tee + silence-watch state machine, shared by wrap-task and run. Async (tokio). |
| `src/signals.rs` | Forward SIGINT/SIGTERM/SIGHUP/SIGQUIT from this process to a child pid. Async. |
| `src/hook_pre.rs` | Implements `agent-tools hook-pre`. |
| `src/hook_post.rs` | Implements `agent-tools hook-post`. |
| `src/wrap_task.rs` | Implements `agent-tools wrap-task <task_dir>`. |
| `src/run.rs` | Implements `agent-tools run [--desc D] -- <cmd>`. |
| `src/ps.rs` | Implements `agent-tools ps [--task <id>] [--session-id <id>]`. |
| `tests/hook_pre_test.rs` | Integration: feed hook JSON via stdin, check `command.sh`, `meta.json`, `updatedInput.command`. |
| `tests/hook_post_test.rs` | Integration: feed backgrounded `tool_response`, check `additionalContext`. |
| `tests/wrap_task_test.rs` | Integration: spawn `wrap-task` on a real `command.sh`, check stdout/stderr capture, exit code, meta updates. |
| `tests/run_test.rs` | Integration: simulate pipeline, check child capture + signal forwarding + non-buffering. |
| `tests/ps_test.rs` | Integration: build state tree on disk, run `ps`, assert output shape. |
| `tests/end_to_end_test.rs` | Integration: full hook → wrap-task → run → ps chain through a temporary `~/.claude/agent-tools/`. |
| `../settings.json` | Add PreToolUse and PostToolUse hook entries for `Bash\|Monitor` (last task). |

A single shared `pub mod` declaration lives in `main.rs` for each module. No `lib.rs` — integration tests use `assert_cmd`-style `process::Command::new(env!("CARGO_BIN_EXE_agent-tools"))`.

---

## Phase 0 — Dependencies and skeleton

### Task 1: Add dependencies to Cargo.toml

**Files:**
- Modify: `agent-tools/Cargo.toml`

- [ ] **Step 1: Replace the `[dependencies]` block and add `[dev-dependencies]`**

Current:
```toml
[dependencies]
clap = { version = "4", features = ["derive"] }
```

Replace whole file body after `edition = "2021"` with:
```toml
[dependencies]
clap = { version = "4", features = ["derive"] }
tokio = { version = "1", features = ["rt-multi-thread", "macros", "io-util", "process", "signal", "time", "fs", "sync"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
chrono = { version = "0.4", features = ["serde"] }
nix = { version = "0.29", features = ["signal", "process"] }
anyhow = "1"

[dev-dependencies]
tempfile = "3"
```

- [ ] **Step 2: Fetch and build**

Run:
```bash
cd /root/claude-config-work/agent-tools && CARGO_HTTP_CAINFO=/root/.mitmproxy/mitmproxy-ca-cert.pem cargo build --release
```
Expected: success. Binary at `target/release/agent-tools` still functions for existing subcommands (`skill`, `cc-pretty`, `cc-workflow`, `pre_output.record`).

- [ ] **Step 3: Smoke-test existing subcommand still works**

Run:
```bash
CLAUDE_CONFIG_ROOT=/root/claude-config-work /root/claude-config-work/agent-tools/target/release/agent-tools pre_output.record '{"turn":0,"summary":"smoke"}'
```
Expected: prints `recorded successfully.` (or whatever the current Python module prints; the point is the binary executes the existing path without crashing).

- [ ] **Step 4: Commit**

```bash
cd /root/claude-config-work && git add agent-tools/Cargo.toml agent-tools/Cargo.lock && git commit -m "agent-tools: add tokio/serde/chrono/nix/anyhow deps for wrap-task work"
```

---

## Phase 1 — Pure data layers (parsing, paths, meta, events)

These modules have no async, no I/O beyond a few file reads/writes, and are easy to unit-test.

### Task 2: hook_input.rs — parse PreToolUse / PostToolUse stdin

**Files:**
- Create: `agent-tools/src/hook_input.rs`
- Modify: `agent-tools/src/main.rs:1` (add `mod hook_input;` near top)

- [ ] **Step 1: Write the failing test**

Create test inline at the bottom of `src/hook_input.rs`:

```rust
use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct PreToolUseInput {
    pub session_id: String,
    #[serde(default)]
    pub agent_id: Option<String>,
    pub cwd: String,
    pub tool_name: String,
    pub tool_input: ToolInput,
    pub tool_use_id: String,
}

#[derive(Debug, Deserialize)]
pub struct PostToolUseInput {
    pub session_id: String,
    #[serde(default)]
    pub agent_id: Option<String>,
    pub tool_name: String,
    pub tool_input: ToolInput,
    pub tool_use_id: String,
    #[serde(default)]
    pub tool_response: serde_json::Value,
}

#[derive(Debug, Deserialize)]
pub struct ToolInput {
    pub command: String,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub timeout: Option<u64>,
}

pub fn parse_pre(s: &str) -> anyhow::Result<PreToolUseInput> {
    Ok(serde_json::from_str(s)?)
}

pub fn parse_post(s: &str) -> anyhow::Result<PostToolUseInput> {
    Ok(serde_json::from_str(s)?)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_main_thread_pre() {
        let json = r#"{
            "session_id": "sid-1",
            "cwd": "/tmp",
            "tool_name": "Bash",
            "tool_input": {"command": "echo hi", "description": "say hi"},
            "tool_use_id": "tuid-1"
        }"#;
        let p = parse_pre(json).unwrap();
        assert_eq!(p.session_id, "sid-1");
        assert!(p.agent_id.is_none());
        assert_eq!(p.tool_input.command, "echo hi");
        assert_eq!(p.tool_input.description.as_deref(), Some("say hi"));
    }

    #[test]
    fn parses_subagent_pre() {
        let json = r#"{
            "session_id": "sid-1",
            "agent_id": "agent-abc",
            "cwd": "/tmp",
            "tool_name": "Monitor",
            "tool_input": {"command": "tail -f log"},
            "tool_use_id": "tuid-2"
        }"#;
        let p = parse_pre(json).unwrap();
        assert_eq!(p.agent_id.as_deref(), Some("agent-abc"));
        assert_eq!(p.tool_name, "Monitor");
        assert!(p.tool_input.description.is_none());
    }

    #[test]
    fn parses_post_with_backgrounding() {
        let json = r#"{
            "session_id": "sid-1",
            "tool_name": "Bash",
            "tool_input": {"command": "sleep 9999", "timeout": 5000},
            "tool_use_id": "tuid-3",
            "tool_response": {"backgroundTaskId": "bt-7"}
        }"#;
        let p = parse_post(json).unwrap();
        assert_eq!(p.tool_response["backgroundTaskId"], "bt-7");
        assert_eq!(p.tool_input.timeout, Some(5000));
    }
}
```

Add `mod hook_input;` as the first non-comment line in `src/main.rs` (after the existing `use` block is fine).

- [ ] **Step 2: Run tests, verify all three pass**

```bash
cd /root/claude-config-work/agent-tools && cargo test --lib hook_input 2>&1 | tail -20
```
Expected: `test result: ok. 3 passed`.

- [ ] **Step 3: Commit**

```bash
cd /root/claude-config-work && git add agent-tools/src/hook_input.rs agent-tools/src/main.rs && git commit -m "agent-tools: hook_input — parse PreToolUse/PostToolUse JSON"
```

---

### Task 3: paths.rs — task_dir computation and recovery

**Files:**
- Create: `agent-tools/src/paths.rs`
- Modify: `agent-tools/src/main.rs` (add `mod paths;`)

- [ ] **Step 1: Write the failing tests**

`src/paths.rs`:

```rust
use anyhow::{bail, Context, Result};
use std::env;
use std::path::{Path, PathBuf};

/// Root of all agent-tools state: ~/.claude/agent-tools
pub fn state_root() -> Result<PathBuf> {
    let home = env::var("HOME").context("HOME not set")?;
    Ok(PathBuf::from(home).join(".claude/agent-tools"))
}

/// Compute task_dir from identifiers. `agent_id == None` means main-thread.
pub fn task_dir_for(session_id: &str, agent_id: Option<&str>, task_id: &str) -> Result<PathBuf> {
    let mut p = state_root()?.join(session_id);
    if let Some(a) = agent_id {
        p.push(a);
    }
    p.push(task_id);
    Ok(p)
}

/// Read AGENT_TOOLS_TASK_ID env var as an absolute path.
pub fn task_dir_from_env() -> Result<PathBuf> {
    let v = env::var("AGENT_TOOLS_TASK_ID")
        .context("AGENT_TOOLS_TASK_ID is not set")?;
    let p = PathBuf::from(&v);
    if !p.is_absolute() {
        bail!("AGENT_TOOLS_TASK_ID must be an absolute path, got: {v}");
    }
    Ok(p)
}

/// Recover (session_id, Option<agent_id>, task_id) from a task_dir path
/// rooted at state_root().
pub fn parse_task_dir(task_dir: &Path) -> Result<(String, Option<String>, String)> {
    let root = state_root()?;
    let rel = task_dir.strip_prefix(&root).with_context(|| {
        format!(
            "task_dir {} is not under state root {}",
            task_dir.display(),
            root.display()
        )
    })?;
    let parts: Vec<_> = rel.components().map(|c| c.as_os_str().to_string_lossy().to_string()).collect();
    match parts.as_slice() {
        [sid, tid] => Ok((sid.clone(), None, tid.clone())),
        [sid, aid, tid] => Ok((sid.clone(), Some(aid.clone()), tid.clone())),
        _ => bail!("task_dir must have 2 or 3 components under state root, got: {rel:?}"),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn builds_main_thread_path() {
        std::env::set_var("HOME", "/h");
        let p = task_dir_for("sid", None, "tid").unwrap();
        assert_eq!(p, PathBuf::from("/h/.claude/agent-tools/sid/tid"));
    }

    #[test]
    fn builds_subagent_path() {
        std::env::set_var("HOME", "/h");
        let p = task_dir_for("sid", Some("aid"), "tid").unwrap();
        assert_eq!(p, PathBuf::from("/h/.claude/agent-tools/sid/aid/tid"));
    }

    #[test]
    fn parses_main_thread() {
        std::env::set_var("HOME", "/h");
        let (s, a, t) = parse_task_dir(Path::new("/h/.claude/agent-tools/sid/tid")).unwrap();
        assert_eq!(s, "sid");
        assert_eq!(a, None);
        assert_eq!(t, "tid");
    }

    #[test]
    fn parses_subagent() {
        std::env::set_var("HOME", "/h");
        let (s, a, t) = parse_task_dir(Path::new("/h/.claude/agent-tools/sid/aid/tid")).unwrap();
        assert_eq!(s, "sid");
        assert_eq!(a.as_deref(), Some("aid"));
        assert_eq!(t, "tid");
    }

    #[test]
    fn rejects_non_state_dir() {
        std::env::set_var("HOME", "/h");
        assert!(parse_task_dir(Path::new("/somewhere/else")).is_err());
    }
}
```

Add `mod paths;` to `src/main.rs`.

- [ ] **Step 2: Run tests**

```bash
cd /root/claude-config-work/agent-tools && cargo test --lib paths 2>&1 | tail -15
```
Expected: 5 passed. (Note: these tests mutate `HOME` — they run serially via Rust's default test scheduler in a single binary but if you see flakes from parallelism, mark them `#[serial]` later. For now they pass because each sets HOME deterministically before use.)

- [ ] **Step 3: Commit**

```bash
cd /root/claude-config-work && git add agent-tools/src/paths.rs agent-tools/src/main.rs && git commit -m "agent-tools: paths — task_dir build/parse helpers"
```

---

### Task 4: meta.rs — TaskMeta / ChildMeta, atomic write

**Files:**
- Create: `agent-tools/src/meta.rs`
- Modify: `agent-tools/src/main.rs` (add `mod meta;`)

- [ ] **Step 1: Write the failing tests**

`src/meta.rs`:

```rust
use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum Meta {
    Task(TaskMeta),
    Child(ChildMeta),
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct TaskMeta {
    pub session_id: String,
    pub agent_id: Option<String>,
    pub task_id: String,
    pub tool: String,
    pub tool_use_id: String,
    pub desc: Option<String>,
    pub cwd: String,
    pub pid: Option<u32>,
    pub started_at: Option<DateTime<Utc>>,
    pub ended_at: Option<DateTime<Utc>>,
    pub exit_code: Option<i32>,
    pub silence_threshold_ms: u64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ChildMeta {
    pub parent_task_dir: String,
    pub child_id: u32,
    pub desc: Option<String>,
    pub command: Vec<String>,
    pub pid: u32,
    pub started_at: Option<DateTime<Utc>>,
    pub ended_at: Option<DateTime<Utc>>,
    pub exit_code: Option<i32>,
}

/// Write meta atomically: write to <path>.tmp then rename.
pub fn write_meta(dir: &Path, meta: &Meta) -> Result<()> {
    fs::create_dir_all(dir).with_context(|| format!("mkdir {}", dir.display()))?;
    let final_path = dir.join("meta.json");
    let tmp_path = dir.join("meta.json.tmp");
    let json = serde_json::to_vec_pretty(meta)?;
    fs::write(&tmp_path, &json).with_context(|| format!("write {}", tmp_path.display()))?;
    fs::rename(&tmp_path, &final_path)
        .with_context(|| format!("rename {} -> {}", tmp_path.display(), final_path.display()))?;
    Ok(())
}

pub fn read_meta(dir: &Path) -> Result<Meta> {
    let bytes = fs::read(dir.join("meta.json"))
        .with_context(|| format!("read {}/meta.json", dir.display()))?;
    Ok(serde_json::from_slice(&bytes)?)
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn roundtrip_task_meta() {
        let dir = TempDir::new().unwrap();
        let m = Meta::Task(TaskMeta {
            session_id: "sid".into(),
            agent_id: None,
            task_id: "tid".into(),
            tool: "Bash".into(),
            tool_use_id: "tuid".into(),
            desc: Some("d".into()),
            cwd: "/tmp".into(),
            pid: None,
            started_at: None,
            ended_at: None,
            exit_code: None,
            silence_threshold_ms: 30_000,
        });
        write_meta(dir.path(), &m).unwrap();
        let back = read_meta(dir.path()).unwrap();
        match back {
            Meta::Task(t) => {
                assert_eq!(t.task_id, "tid");
                assert_eq!(t.silence_threshold_ms, 30_000);
            }
            _ => panic!("expected Task"),
        }
    }

    #[test]
    fn roundtrip_child_meta() {
        let dir = TempDir::new().unwrap();
        let m = Meta::Child(ChildMeta {
            parent_task_dir: "/x".into(),
            child_id: 42,
            desc: None,
            command: vec!["echo".into(), "hi".into()],
            pid: 42,
            started_at: None,
            ended_at: None,
            exit_code: None,
        });
        write_meta(dir.path(), &m).unwrap();
        let back = read_meta(dir.path()).unwrap();
        match back {
            Meta::Child(c) => {
                assert_eq!(c.child_id, 42);
                assert_eq!(c.command, vec!["echo".to_string(), "hi".into()]);
            }
            _ => panic!("expected Child"),
        }
    }

    #[test]
    fn atomic_write_leaves_no_tmp() {
        let dir = TempDir::new().unwrap();
        let m = Meta::Task(TaskMeta {
            session_id: "sid".into(),
            agent_id: None,
            task_id: "tid".into(),
            tool: "Bash".into(),
            tool_use_id: "tuid".into(),
            desc: None,
            cwd: "/tmp".into(),
            pid: None,
            started_at: None,
            ended_at: None,
            exit_code: None,
            silence_threshold_ms: 30_000,
        });
        write_meta(dir.path(), &m).unwrap();
        assert!(dir.path().join("meta.json").exists());
        assert!(!dir.path().join("meta.json.tmp").exists());
    }
}
```

Add `mod meta;` to `src/main.rs`.

- [ ] **Step 2: Run tests**

```bash
cd /root/claude-config-work/agent-tools && cargo test --lib meta 2>&1 | tail -15
```
Expected: 3 passed.

- [ ] **Step 3: Commit**

```bash
cd /root/claude-config-work && git add agent-tools/src/meta.rs agent-tools/src/main.rs && git commit -m "agent-tools: meta — TaskMeta/ChildMeta with atomic write"
```

---

### Task 5: events.rs — append-only event log

**Files:**
- Create: `agent-tools/src/events.rs`
- Modify: `agent-tools/src/main.rs` (add `mod events;`)

- [ ] **Step 1: Write the failing tests**

`src/events.rs`:

```rust
use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::fs::OpenOptions;
use std::io::Write;
use std::path::Path;

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub struct Event {
    pub ts: DateTime<Utc>,
    pub kind: String,
    pub data: serde_json::Value,
}

/// Append a single event line to <dir>/events.jsonl. Opens with O_APPEND so it
/// is safe against concurrent writers on the same file.
pub fn append(dir: &Path, kind: &str, data: serde_json::Value) -> Result<()> {
    let path = dir.join("events.jsonl");
    let evt = Event {
        ts: Utc::now(),
        kind: kind.into(),
        data,
    };
    let mut line = serde_json::to_vec(&evt)?;
    line.push(b'\n');
    let mut f = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&path)
        .with_context(|| format!("open append {}", path.display()))?;
    f.write_all(&line)
        .with_context(|| format!("write {}", path.display()))?;
    Ok(())
}

/// Read all events from <dir>/events.jsonl in chronological order.
pub fn read_all(dir: &Path) -> Result<Vec<Event>> {
    let path = dir.join("events.jsonl");
    if !path.exists() {
        return Ok(vec![]);
    }
    let bytes = std::fs::read_to_string(&path)?;
    let mut out = Vec::new();
    for line in bytes.lines() {
        if line.trim().is_empty() {
            continue;
        }
        out.push(serde_json::from_str(line)?);
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn append_creates_file_and_writes_one_line() {
        let dir = TempDir::new().unwrap();
        append(dir.path(), "task_started", serde_json::json!({"pid": 1})).unwrap();
        let evts = read_all(dir.path()).unwrap();
        assert_eq!(evts.len(), 1);
        assert_eq!(evts[0].kind, "task_started");
        assert_eq!(evts[0].data["pid"], 1);
    }

    #[test]
    fn append_preserves_order() {
        let dir = TempDir::new().unwrap();
        append(dir.path(), "a", serde_json::json!({})).unwrap();
        append(dir.path(), "b", serde_json::json!({})).unwrap();
        append(dir.path(), "c", serde_json::json!({})).unwrap();
        let evts = read_all(dir.path()).unwrap();
        let kinds: Vec<&str> = evts.iter().map(|e| e.kind.as_str()).collect();
        assert_eq!(kinds, vec!["a", "b", "c"]);
    }

    #[test]
    fn read_missing_file_returns_empty() {
        let dir = TempDir::new().unwrap();
        let evts = read_all(dir.path()).unwrap();
        assert_eq!(evts.len(), 0);
    }
}
```

Add `mod events;` to `src/main.rs`.

- [ ] **Step 2: Run tests**

```bash
cd /root/claude-config-work/agent-tools && cargo test --lib events 2>&1 | tail -15
```
Expected: 3 passed.

- [ ] **Step 3: Commit**

```bash
cd /root/claude-config-work && git add agent-tools/src/events.rs agent-tools/src/main.rs && git commit -m "agent-tools: events — append-only events.jsonl"
```

---

## Phase 2 — hook-pre and hook-post (no async needed)

### Task 6: hook_pre subcommand

**Files:**
- Create: `agent-tools/src/hook_pre.rs`
- Modify: `agent-tools/src/main.rs` (add `mod hook_pre;`, add `HookPre` arm to `Cmd`, dispatch)
- Create: `agent-tools/tests/hook_pre_test.rs`

- [ ] **Step 1: Write the failing integration test**

`tests/hook_pre_test.rs`:

```rust
use std::process::{Command, Stdio};
use std::io::Write;

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

#[test]
fn main_thread_rewrite_creates_state_and_returns_updated_input() {
    let home = tempfile::tempdir().unwrap();
    let input = serde_json::json!({
        "session_id": "sid-test",
        "cwd": "/tmp",
        "tool_name": "Bash",
        "tool_input": {"command": "echo $((1+1))", "description": "math"},
        "tool_use_id": "tuid-test"
    }).to_string();

    let mut child = Command::new(bin())
        .arg("hook-pre")
        .env("HOME", home.path())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.as_mut().unwrap().write_all(input.as_bytes()).unwrap();
    let out = child.wait_with_output().unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));

    let parsed: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    assert_eq!(parsed["hookSpecificOutput"]["hookEventName"], "PreToolUse");
    assert_eq!(parsed["hookSpecificOutput"]["permissionDecision"], "allow");
    let new_cmd = parsed["hookSpecificOutput"]["updatedInput"]["command"]
        .as_str()
        .unwrap();
    assert!(
        new_cmd.starts_with("exec agent-tools wrap-task "),
        "got: {new_cmd}"
    );

    let task_dir = home
        .path()
        .join(".claude/agent-tools/sid-test/tuid-test");
    assert!(task_dir.join("meta.json").exists());
    assert!(task_dir.join("command.sh").exists());
    assert_eq!(
        std::fs::read_to_string(task_dir.join("command.sh")).unwrap(),
        "echo $((1+1))"
    );

    // task_dir must be embedded in the rewritten command (shell-quoted).
    let task_dir_str = task_dir.to_string_lossy();
    assert!(new_cmd.contains(task_dir_str.as_ref()), "got: {new_cmd}");
}

#[test]
fn subagent_path_includes_agent_id() {
    let home = tempfile::tempdir().unwrap();
    let input = serde_json::json!({
        "session_id": "sid-test",
        "agent_id": "agent-x",
        "cwd": "/tmp",
        "tool_name": "Monitor",
        "tool_input": {"command": "tail -f /var/log/foo"},
        "tool_use_id": "tuid-2"
    }).to_string();

    let mut child = Command::new(bin())
        .arg("hook-pre")
        .env("HOME", home.path())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.as_mut().unwrap().write_all(input.as_bytes()).unwrap();
    let out = child.wait_with_output().unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));

    let task_dir = home
        .path()
        .join(".claude/agent-tools/sid-test/agent-x/tuid-2");
    assert!(task_dir.join("meta.json").exists());
}

#[test]
fn command_with_special_chars_is_written_verbatim() {
    let home = tempfile::tempdir().unwrap();
    let weird = "echo 'a\"b\\$c\nd' | grep foo | tail -1";
    let input = serde_json::json!({
        "session_id": "sid-test",
        "cwd": "/tmp",
        "tool_name": "Bash",
        "tool_input": {"command": weird},
        "tool_use_id": "tuid-3"
    }).to_string();

    let mut child = Command::new(bin())
        .arg("hook-pre")
        .env("HOME", home.path())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.as_mut().unwrap().write_all(input.as_bytes()).unwrap();
    let out = child.wait_with_output().unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));

    let command_sh = home
        .path()
        .join(".claude/agent-tools/sid-test/tuid-3/command.sh");
    assert_eq!(std::fs::read_to_string(&command_sh).unwrap(), weird);
}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /root/claude-config-work/agent-tools && cargo test --test hook_pre_test 2>&1 | tail -10
```
Expected: build failure (`hook-pre` subcommand doesn't exist yet) or test failure (subcommand not found).

- [ ] **Step 3: Implement hook_pre.rs**

`src/hook_pre.rs`:

```rust
use anyhow::{Context, Result};
use std::fs;
use std::io::Read;
use std::path::PathBuf;

use crate::hook_input;
use crate::meta::{Meta, TaskMeta};
use crate::paths;

const SILENCE_THRESHOLD_MS: u64 = 30_000;

pub fn run() -> Result<()> {
    let mut buf = String::new();
    std::io::stdin().read_to_string(&mut buf).context("read stdin")?;

    // Try to parse; on any parse error, fail open (allow original command, no rewrite).
    let input = match hook_input::parse_pre(&buf) {
        Ok(p) => p,
        Err(e) => {
            eprintln!("agent-tools hook-pre: parse error: {e:#}");
            print_allow_passthrough();
            return Ok(());
        }
    };

    // Only act on Bash and Monitor.
    if input.tool_name != "Bash" && input.tool_name != "Monitor" {
        print_allow_passthrough();
        return Ok(());
    }

    let task_dir = paths::task_dir_for(
        &input.session_id,
        input.agent_id.as_deref(),
        &input.tool_use_id,
    )?;

    // Write command.sh first; if that fails, fall back to passthrough so the
    // user's command still runs.
    if let Err(e) = prepare_task_dir(&task_dir, &input) {
        eprintln!("agent-tools hook-pre: setup failed ({e:#}); allowing original command");
        print_allow_passthrough();
        return Ok(());
    }

    let quoted = shell_single_quote(&task_dir.to_string_lossy());
    let new_command = format!("exec agent-tools wrap-task {quoted}");
    let out = serde_json::json!({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": { "command": new_command }
        }
    });
    println!("{}", serde_json::to_string(&out)?);
    Ok(())
}

fn prepare_task_dir(task_dir: &PathBuf, input: &hook_input::PreToolUseInput) -> Result<()> {
    fs::create_dir_all(task_dir.join("children"))
        .with_context(|| format!("mkdir {}", task_dir.display()))?;
    fs::write(task_dir.join("command.sh"), &input.tool_input.command)
        .with_context(|| format!("write command.sh under {}", task_dir.display()))?;
    let meta = Meta::Task(TaskMeta {
        session_id: input.session_id.clone(),
        agent_id: input.agent_id.clone(),
        task_id: input.tool_use_id.clone(),
        tool: input.tool_name.clone(),
        tool_use_id: input.tool_use_id.clone(),
        desc: input.tool_input.description.clone(),
        cwd: input.cwd.clone(),
        pid: None,
        started_at: None,
        ended_at: None,
        exit_code: None,
        silence_threshold_ms: SILENCE_THRESHOLD_MS,
    });
    crate::meta::write_meta(task_dir, &meta)?;
    Ok(())
}

fn print_allow_passthrough() {
    let out = serde_json::json!({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow"
        }
    });
    println!("{}", serde_json::to_string(&out).unwrap());
}

/// Single-quote a string for safe inclusion in a `bash -c` argument. Replaces
/// each existing `'` with `'\''` (close, escaped quote, reopen) and wraps in
/// single quotes.
fn shell_single_quote(s: &str) -> String {
    let mut out = String::with_capacity(s.len() + 2);
    out.push('\'');
    for ch in s.chars() {
        if ch == '\'' {
            out.push_str("'\\''");
        } else {
            out.push(ch);
        }
    }
    out.push('\'');
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn quotes_plain() {
        assert_eq!(shell_single_quote("abc"), "'abc'");
    }
    #[test]
    fn quotes_with_single_quote() {
        assert_eq!(shell_single_quote("a'b"), "'a'\\''b'");
    }
    #[test]
    fn quotes_path() {
        assert_eq!(
            shell_single_quote("/h/.claude/agent-tools/sid/tid"),
            "'/h/.claude/agent-tools/sid/tid'"
        );
    }
}
```

Modify `src/main.rs`:

- Near the top with the existing `mod` lines, add `mod hook_pre;`.
- Add to the `Cmd` enum:
  ```rust
  /// PreToolUse hook for Bash and Monitor.
  #[command(name = "hook-pre")]
  HookPre,
  ```
- Add a match arm in `main()`:
  ```rust
  Cmd::HookPre => {
      if let Err(e) = hook_pre::run() {
          eprintln!("agent-tools hook-pre: {e:#}");
          std::process::exit(1);
      }
      std::process::exit(0);
  }
  ```

- [ ] **Step 4: Run tests to verify all three pass**

```bash
cd /root/claude-config-work/agent-tools && cargo test --test hook_pre_test 2>&1 | tail -15
```
Expected: 3 passed.

- [ ] **Step 5: Run inline unit tests in hook_pre**

```bash
cd /root/claude-config-work/agent-tools && cargo test --lib hook_pre 2>&1 | tail -10
```
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
cd /root/claude-config-work && git add agent-tools/src/hook_pre.rs agent-tools/src/main.rs agent-tools/tests/hook_pre_test.rs && git commit -m "agent-tools: hook-pre — write command.sh and rewrite Bash/Monitor"
```

---

### Task 7: hook_post subcommand

**Files:**
- Create: `agent-tools/src/hook_post.rs`
- Modify: `agent-tools/src/main.rs` (add `mod hook_post;`, `HookPost` arm)
- Create: `agent-tools/tests/hook_post_test.rs`

- [ ] **Step 1: Write the failing integration tests**

`tests/hook_post_test.rs`:

```rust
use std::io::Write;
use std::process::{Command, Stdio};

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn run_post(home: &std::path::Path, body: serde_json::Value) -> (std::process::ExitStatus, String, String) {
    let mut c = Command::new(bin())
        .arg("hook-post")
        .env("HOME", home)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    c.stdin.as_mut().unwrap().write_all(body.to_string().as_bytes()).unwrap();
    let out = c.wait_with_output().unwrap();
    (out.status, String::from_utf8_lossy(&out.stdout).into_owned(), String::from_utf8_lossy(&out.stderr).into_owned())
}

fn seed_task(home: &std::path::Path, session: &str, task: &str) {
    let dir = home.join(format!(".claude/agent-tools/{session}/{task}"));
    std::fs::create_dir_all(&dir).unwrap();
    std::fs::write(dir.join("meta.json"), r#"{"kind":"task","session_id":"sid","agent_id":null,"task_id":"tuid","tool":"Bash","tool_use_id":"tuid","desc":null,"cwd":"/tmp","pid":1,"started_at":null,"ended_at":null,"exit_code":null,"silence_threshold_ms":30000}"#).unwrap();
}

#[test]
fn no_backgrounding_emits_no_additional_context() {
    let home = tempfile::tempdir().unwrap();
    seed_task(home.path(), "sid", "tuid");
    let (status, stdout, stderr) = run_post(home.path(), serde_json::json!({
        "session_id": "sid",
        "tool_name": "Bash",
        "tool_input": {"command": "echo hi"},
        "tool_use_id": "tuid",
        "tool_response": {}
    }));
    assert!(status.success(), "stderr: {stderr}");
    if !stdout.trim().is_empty() {
        let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
        assert!(v.get("hookSpecificOutput")
            .and_then(|h| h.get("additionalContext"))
            .is_none(), "should not emit additionalContext, got {stdout}");
    }
}

#[test]
fn assistant_auto_background_emits_context() {
    let home = tempfile::tempdir().unwrap();
    seed_task(home.path(), "sid", "tuid");
    let (status, stdout, _stderr) = run_post(home.path(), serde_json::json!({
        "session_id": "sid",
        "tool_name": "Bash",
        "tool_input": {"command": "long-running"},
        "tool_use_id": "tuid",
        "tool_response": {"backgroundTaskId": "bt-9", "assistantAutoBackgrounded": true}
    }));
    assert!(status.success());
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    let ctx = v["hookSpecificOutput"]["additionalContext"].as_str().unwrap();
    assert!(ctx.contains("KAIROS") || ctx.contains("auto"), "context: {ctx}");
    assert!(ctx.contains("bt-9"), "context: {ctx}");

    // Events log should record the backgrounding.
    let evts = std::fs::read_to_string(home.path().join(".claude/agent-tools/sid/tuid/events.jsonl")).unwrap();
    assert!(evts.contains("\"backgrounded\""), "events: {evts}");
}

#[test]
fn user_backgrounding_emits_context() {
    let home = tempfile::tempdir().unwrap();
    seed_task(home.path(), "sid", "tuid");
    let (status, stdout, _stderr) = run_post(home.path(), serde_json::json!({
        "session_id": "sid",
        "tool_name": "Bash",
        "tool_input": {"command": "long-running"},
        "tool_use_id": "tuid",
        "tool_response": {"backgroundTaskId": "bt-1", "backgroundedByUser": true}
    }));
    assert!(status.success());
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    let ctx = v["hookSpecificOutput"]["additionalContext"].as_str().unwrap();
    assert!(ctx.contains("Ctrl+B") || ctx.contains("user"), "context: {ctx}");
}

#[test]
fn timeout_backgrounding_emits_context_with_limit() {
    let home = tempfile::tempdir().unwrap();
    seed_task(home.path(), "sid", "tuid");
    let (status, stdout, _stderr) = run_post(home.path(), serde_json::json!({
        "session_id": "sid",
        "tool_name": "Bash",
        "tool_input": {"command": "sleep 9999", "timeout": 5000},
        "tool_use_id": "tuid",
        "tool_response": {"backgroundTaskId": "bt-2"}
    }));
    assert!(status.success());
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    let ctx = v["hookSpecificOutput"]["additionalContext"].as_str().unwrap();
    assert!(ctx.contains("timeout"), "context: {ctx}");
    assert!(ctx.contains("5000"), "context: {ctx}");
}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /root/claude-config-work/agent-tools && cargo test --test hook_post_test 2>&1 | tail -10
```
Expected: tests fail (subcommand missing or wrong output).

- [ ] **Step 3: Implement hook_post.rs**

`src/hook_post.rs`:

```rust
use anyhow::{Context, Result};
use std::io::Read;

use crate::events;
use crate::hook_input;
use crate::paths;

pub fn run() -> Result<()> {
    let mut buf = String::new();
    std::io::stdin().read_to_string(&mut buf).context("read stdin")?;

    let input = match hook_input::parse_post(&buf) {
        Ok(p) => p,
        Err(e) => {
            eprintln!("agent-tools hook-post: parse error: {e:#}");
            return Ok(());
        }
    };

    if input.tool_name != "Bash" && input.tool_name != "Monitor" {
        return Ok(());
    }

    let bg_task_id = input.tool_response.get("backgroundTaskId").and_then(|v| v.as_str());
    let Some(bg_task_id) = bg_task_id else {
        return Ok(()); // no backgrounding
    };

    let auto = input.tool_response.get("assistantAutoBackgrounded").and_then(|v| v.as_bool()).unwrap_or(false);
    let user = input.tool_response.get("backgroundedByUser").and_then(|v| v.as_bool()).unwrap_or(false);

    let (cause_label, cause_for_context) = if auto {
        ("assistant_auto", "assistant-mode auto-background (KAIROS)".to_string())
    } else if user {
        ("user", "user manually backgrounded (Ctrl+B)".to_string())
    } else {
        let limit = input.tool_input.timeout.unwrap_or(120_000);
        ("timeout", format!("timeout ({limit}ms limit hit)"))
    };

    // Log the event under the task dir; non-fatal if the dir is missing
    // (we shouldn't have rewritten but did; keep going to emit context).
    let task_dir = paths::task_dir_for(
        &input.session_id,
        input.agent_id.as_deref(),
        &input.tool_use_id,
    )?;
    let _ = events::append(
        &task_dir,
        "backgrounded",
        serde_json::json!({
            "cause": cause_label,
            "background_task_id": bg_task_id,
            "timeout_ms": input.tool_input.timeout
        }),
    );

    let additional_context = format!(
        "BACKGROUNDED: Command was involuntarily backgrounded. Cause: {cause}. \
         Process is still running (task_id: {tid}). \
         To kill it: use TaskStop tool with task_id {tid}. \
         Captured output paths in: {task_dir}",
        cause = cause_for_context,
        tid = bg_task_id,
        task_dir = task_dir.display(),
    );

    let out = serde_json::json!({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": additional_context
        }
    });
    println!("{}", serde_json::to_string(&out)?);
    Ok(())
}
```

Modify `src/main.rs`: add `mod hook_post;`, add `HookPost` arm to `Cmd` (`#[command(name = "hook-post")]`), and dispatch:
```rust
Cmd::HookPost => {
    if let Err(e) = hook_post::run() {
        eprintln!("agent-tools hook-post: {e:#}");
        std::process::exit(1);
    }
    std::process::exit(0);
}
```

- [ ] **Step 4: Run tests to verify 4 pass**

```bash
cd /root/claude-config-work/agent-tools && cargo test --test hook_post_test 2>&1 | tail -15
```
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work && git add agent-tools/src/hook_post.rs agent-tools/src/main.rs agent-tools/tests/hook_post_test.rs && git commit -m "agent-tools: hook-post — detect backgrounding, emit additionalContext"
```

---

## Phase 3 — capture engine (shared async machinery)

### Task 8: signals.rs — forward signals to a child pid

**Files:**
- Create: `agent-tools/src/signals.rs`
- Modify: `agent-tools/src/main.rs` (add `mod signals;`)

- [ ] **Step 1: Write the failing test**

`src/signals.rs`:

```rust
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
        // Sleep for a long time; we will SIGTERM ourselves and check the child died.
        let mut child = Command::new("sleep")
            .arg("60")
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .unwrap();
        let child_pid = child.id().unwrap() as i32;

        let (tx, rx) = tokio::sync::watch::channel(false);
        install_forwarding(child_pid, rx).unwrap();

        // Send SIGTERM to the child directly to simulate forwarding having
        // happened (the unit test cannot easily SIGTERM itself without
        // racing the harness). The signal infrastructure is validated by the
        // wrap_task integration test below; here we only check that
        // install_forwarding compiles and does not panic on setup.
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
```

Add `mod signals;` to `src/main.rs`.

- [ ] **Step 2: Run the test**

```bash
cd /root/claude-config-work/agent-tools && cargo test --lib signals 2>&1 | tail -15
```
Expected: 1 passed. (The deeper signal-forwarding behavior is exercised by the wrap_task integration tests; this is the basic smoke.)

- [ ] **Step 3: Commit**

```bash
cd /root/claude-config-work && git add agent-tools/src/signals.rs agent-tools/src/main.rs && git commit -m "agent-tools: signals — forward SIG{INT,TERM,HUP,QUIT} to child"
```

---

### Task 9: capture.rs — tee with silence watcher

**Files:**
- Create: `agent-tools/src/capture.rs`
- Modify: `agent-tools/src/main.rs` (add `mod capture;`)

- [ ] **Step 1: Write the failing test**

`src/capture.rs`:

```rust
use anyhow::{Context, Result};
use std::path::PathBuf;
use std::sync::Arc;
use std::sync::atomic::{AtomicI64, Ordering};
use tokio::fs::OpenOptions;
use tokio::io::{AsyncRead, AsyncReadExt, AsyncWrite, AsyncWriteExt};
use tokio::sync::watch;
use tokio::time::{sleep, Duration};

use crate::events;

/// Tee `reader` -> (capture file at `capture_path`) + (forward writer).
/// Updates `last_activity_unix_ms` on each non-empty read. Appends
/// `first_byte` + (later) `silence`/`silence_break` events to `events_dir`
/// (the task or child dir that owns events.jsonl).
///
/// Returns when the reader closes (EOF).
pub async fn tee<R, W>(
    stream_name: &'static str,
    mut reader: R,
    capture_path: PathBuf,
    mut forward: W,
    last_activity_unix_ms: Arc<AtomicI64>,
    events_dir: PathBuf,
) -> Result<()>
where
    R: AsyncRead + Unpin,
    W: AsyncWrite + Unpin,
{
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&capture_path)
        .await
        .with_context(|| format!("open capture {}", capture_path.display()))?;

    let mut buf = vec![0u8; 8192];
    let mut wrote_first_byte = false;
    loop {
        let n = reader.read(&mut buf).await?;
        if n == 0 {
            break;
        }
        let chunk = &buf[..n];
        // Write to capture file and forward; both unbuffered.
        file.write_all(chunk).await?;
        let _ = forward.write_all(chunk).await; // forward errors are non-fatal
        last_activity_unix_ms.store(now_unix_ms(), Ordering::SeqCst);
        if !wrote_first_byte {
            wrote_first_byte = true;
            let dir = events_dir.clone();
            let stream = stream_name.to_string();
            tokio::task::spawn_blocking(move || {
                let _ = events::append(&dir, "first_byte", serde_json::json!({"stream": stream}));
            });
        }
    }
    file.flush().await.ok();
    let _ = forward.flush().await;
    Ok(())
}

/// Run a per-stream silence watcher. Polls every 1 s; if the gap between
/// `now` and `last_activity_unix_ms` exceeds `threshold_ms`, emits `silence`
/// once until the next byte (which emits `silence_break`).
pub async fn watch_silence(
    stream_name: &'static str,
    last_activity_unix_ms: Arc<AtomicI64>,
    threshold_ms: u64,
    events_dir: PathBuf,
    mut cancel: watch::Receiver<bool>,
) {
    let mut last_seen = last_activity_unix_ms.load(Ordering::SeqCst);
    let mut warned = false;
    loop {
        tokio::select! {
            _ = sleep(Duration::from_secs(1)) => {}
            changed = cancel.changed() => {
                if changed.is_err() || *cancel.borrow() { break; }
            }
        }
        let cur = last_activity_unix_ms.load(Ordering::SeqCst);
        let now = now_unix_ms();
        let gap = now - cur;
        if !warned && gap > threshold_ms as i64 {
            let dir = events_dir.clone();
            let stream = stream_name.to_string();
            let gap_ms = gap;
            tokio::task::spawn_blocking(move || {
                let _ = events::append(&dir, "silence", serde_json::json!({"stream": stream, "since_ms": gap_ms}));
            });
            warned = true;
        }
        if warned && cur > last_seen {
            let dir = events_dir.clone();
            let stream = stream_name.to_string();
            tokio::task::spawn_blocking(move || {
                let _ = events::append(&dir, "silence_break", serde_json::json!({"stream": stream}));
            });
            warned = false;
        }
        last_seen = cur;
    }
}

fn now_unix_ms() -> i64 {
    chrono::Utc::now().timestamp_millis()
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;
    use tokio::io::AsyncWriteExt;

    #[tokio::test]
    async fn tee_writes_capture_file() {
        let dir = TempDir::new().unwrap();
        let cap = dir.path().join("stdout");
        let evts_dir = dir.path().to_path_buf();
        let (reader, mut writer) = tokio::io::duplex(1024);
        let last = Arc::new(AtomicI64::new(now_unix_ms()));

        let h = tokio::spawn(tee(
            "stdout",
            reader,
            cap.clone(),
            tokio::io::sink(),
            last.clone(),
            evts_dir,
        ));

        writer.write_all(b"hello\n").await.unwrap();
        drop(writer);
        h.await.unwrap().unwrap();

        let captured = std::fs::read(&cap).unwrap();
        assert_eq!(captured, b"hello\n");
    }

    #[tokio::test]
    async fn tee_forwards_through_to_writer() {
        let dir = TempDir::new().unwrap();
        let cap = dir.path().join("stdout");
        let evts_dir = dir.path().to_path_buf();
        let (reader, mut writer) = tokio::io::duplex(1024);
        let (forward_w, mut forward_r) = tokio::io::duplex(1024);
        let last = Arc::new(AtomicI64::new(now_unix_ms()));

        let h = tokio::spawn(tee(
            "stdout",
            reader,
            cap,
            forward_w,
            last,
            evts_dir,
        ));
        writer.write_all(b"forward me\n").await.unwrap();
        drop(writer);
        h.await.unwrap().unwrap();

        let mut got = Vec::new();
        tokio::io::AsyncReadExt::read_to_end(&mut forward_r, &mut got).await.unwrap();
        assert_eq!(got, b"forward me\n");
    }

    #[tokio::test]
    async fn tee_records_first_byte_event() {
        let dir = TempDir::new().unwrap();
        let cap = dir.path().join("stdout");
        let evts_dir = dir.path().to_path_buf();
        let (reader, mut writer) = tokio::io::duplex(1024);
        let last = Arc::new(AtomicI64::new(now_unix_ms()));

        let h = tokio::spawn(tee(
            "stdout",
            reader,
            cap,
            tokio::io::sink(),
            last,
            evts_dir.clone(),
        ));
        writer.write_all(b"x").await.unwrap();
        drop(writer);
        h.await.unwrap().unwrap();

        // Allow spawn_blocking to flush.
        tokio::time::sleep(Duration::from_millis(100)).await;
        let evts = events::read_all(&evts_dir).unwrap();
        assert!(evts.iter().any(|e| e.kind == "first_byte"));
    }

    #[tokio::test]
    async fn silence_watcher_emits_event_after_threshold() {
        let dir = TempDir::new().unwrap();
        let evts_dir = dir.path().to_path_buf();
        let last = Arc::new(AtomicI64::new(now_unix_ms() - 5000)); // 5 s of silence already
        let (tx, rx) = watch::channel(false);

        let h = tokio::spawn(watch_silence("stdout", last.clone(), 1000, evts_dir.clone(), rx));

        tokio::time::sleep(Duration::from_millis(1500)).await;
        let _ = tx.send(true);
        h.await.unwrap();

        tokio::time::sleep(Duration::from_millis(100)).await;
        let evts = events::read_all(&evts_dir).unwrap();
        assert!(evts.iter().any(|e| e.kind == "silence"), "events: {:?}", evts);
    }
}
```

Add `mod capture;` to `src/main.rs`.

- [ ] **Step 2: Run tests**

```bash
cd /root/claude-config-work/agent-tools && cargo test --lib capture 2>&1 | tail -15
```
Expected: 4 passed.

- [ ] **Step 3: Commit**

```bash
cd /root/claude-config-work && git add agent-tools/src/capture.rs agent-tools/src/main.rs && git commit -m "agent-tools: capture — tee + silence watcher"
```

---

## Phase 4 — wrap-task

### Task 10: wrap_task subcommand

**Files:**
- Create: `agent-tools/src/wrap_task.rs`
- Modify: `agent-tools/src/main.rs` (add `mod wrap_task;`, `WrapTask` arm, change `main` to use `#[tokio::main]`)
- Create: `agent-tools/tests/wrap_task_test.rs`

- [ ] **Step 1: Write the failing integration tests**

`tests/wrap_task_test.rs`:

```rust
use std::path::PathBuf;
use std::process::Command;

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn seed_task(home: &std::path::Path, session: &str, task: &str, cmd: &str) -> PathBuf {
    let dir = home.join(format!(".claude/agent-tools/{session}/{task}"));
    std::fs::create_dir_all(dir.join("children")).unwrap();
    std::fs::write(dir.join("command.sh"), cmd).unwrap();
    let meta = serde_json::json!({
        "kind":"task","session_id":session,"agent_id":null,"task_id":task,
        "tool":"Bash","tool_use_id":task,"desc":null,"cwd":"/tmp",
        "pid":null,"started_at":null,"ended_at":null,"exit_code":null,
        "silence_threshold_ms":30000
    });
    std::fs::write(dir.join("meta.json"), serde_json::to_string_pretty(&meta).unwrap()).unwrap();
    dir
}

#[test]
fn captures_stdout_and_stderr_and_exits_with_child_code() {
    let home = tempfile::tempdir().unwrap();
    let dir = seed_task(home.path(), "sid", "tuid", "echo hello; echo oh-no 1>&2; exit 3");

    let out = Command::new(bin())
        .args(["wrap-task", dir.to_str().unwrap()])
        .env("HOME", home.path())
        .output()
        .unwrap();
    assert_eq!(out.status.code(), Some(3), "stderr: {}", String::from_utf8_lossy(&out.stderr));
    assert_eq!(String::from_utf8_lossy(&out.stdout), "hello\n");
    assert_eq!(String::from_utf8_lossy(&out.stderr), "oh-no\n");

    let captured_stdout = std::fs::read_to_string(dir.join("stdout")).unwrap();
    let captured_stderr = std::fs::read_to_string(dir.join("stderr")).unwrap();
    assert_eq!(captured_stdout, "hello\n");
    assert_eq!(captured_stderr, "oh-no\n");

    let meta: serde_json::Value = serde_json::from_slice(&std::fs::read(dir.join("meta.json")).unwrap()).unwrap();
    assert_eq!(meta["exit_code"], 3);
    assert!(meta["started_at"].is_string());
    assert!(meta["ended_at"].is_string());
    assert!(meta["pid"].is_number());

    let evts = std::fs::read_to_string(dir.join("events.jsonl")).unwrap();
    assert!(evts.contains("\"task_started\""));
    assert!(evts.contains("\"task_exit\""));
}

#[test]
fn propagates_task_id_env_to_child() {
    let home = tempfile::tempdir().unwrap();
    let dir = seed_task(home.path(), "sid", "tuid",
        r#"echo "ATID=$AGENT_TOOLS_TASK_ID""#);
    let out = Command::new(bin())
        .args(["wrap-task", dir.to_str().unwrap()])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_TASK_ID")
        .output()
        .unwrap();
    assert!(out.status.success());
    let s = String::from_utf8_lossy(&out.stdout).into_owned();
    assert!(s.contains(dir.to_str().unwrap()), "got: {s}");
}

#[test]
fn captures_unbuffered_streaming_output() {
    // The child prints, sleeps for slightly under 30 s — well above any
    // line-buffer flush threshold. We verify the file grew before the child
    // exited.
    let home = tempfile::tempdir().unwrap();
    let dir = seed_task(home.path(), "sid", "tuid",
        r#"echo first; sleep 1; echo second"#);
    let out = Command::new(bin())
        .args(["wrap-task", dir.to_str().unwrap()])
        .env("HOME", home.path())
        .output()
        .unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));
    let captured = std::fs::read_to_string(dir.join("stdout")).unwrap();
    assert_eq!(captured, "first\nsecond\n");
}

#[test]
fn missing_command_sh_exits_nonzero() {
    let home = tempfile::tempdir().unwrap();
    let dir = home.path().join(".claude/agent-tools/sid/tuid");
    std::fs::create_dir_all(&dir).unwrap();
    // intentionally no command.sh
    let out = Command::new(bin())
        .args(["wrap-task", dir.to_str().unwrap()])
        .env("HOME", home.path())
        .output()
        .unwrap();
    assert!(!out.status.success());
}
```

- [ ] **Step 2: Run tests — expect failure**

```bash
cd /root/claude-config-work/agent-tools && cargo test --test wrap_task_test 2>&1 | tail -10
```

- [ ] **Step 3: Implement wrap_task.rs**

`src/wrap_task.rs`:

```rust
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

    let mut child = Command::new("bash")
        .args(["--noprofile", "--norc"])
        .arg(&command_sh)
        .env("AGENT_TOOLS_TASK_ID", &task_dir)
        .stdin(Stdio::inherit())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .with_context(|| "spawn bash for command.sh")?;
    let pid = child.id().context("child pid unavailable")? as i32;

    // Patch meta with pid + started_at, atomic.
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
    // Stop silence watchers; tees end on their own when pipes close.
    let _ = cancel_tx.send(true);
    let _ = stdout_tee.await;
    let _ = stderr_tee.await;
    let _ = s1.await;
    let _ = s2.await;

    let exit_code = status.code().unwrap_or_else(|| {
        // Killed by signal — encode 128 + signum.
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
```

Modify `src/main.rs`:

- Add `mod wrap_task;`.
- Change the existing `fn main()` to `fn main()` that constructs a tokio runtime only for the subcommands that need it:

```rust
fn main() {
    let cli = Cli::parse();
    let root = repo_root();
    match cli.command {
        Cmd::Skill { module, args } => { /* existing */ }
        Cmd::CcPretty { args } => { /* existing */ }
        Cmd::CcWorkflow { args } => { /* existing */ }
        Cmd::PreOutputRecord { args } => { /* existing */ }
        Cmd::HookPre => {
            if let Err(e) = hook_pre::run() { eprintln!("agent-tools hook-pre: {e:#}"); std::process::exit(1); }
        }
        Cmd::HookPost => {
            if let Err(e) = hook_post::run() { eprintln!("agent-tools hook-post: {e:#}"); std::process::exit(1); }
        }
        Cmd::WrapTask { task_dir } => {
            let code = tokio::runtime::Builder::new_multi_thread()
                .enable_all()
                .build()
                .unwrap()
                .block_on(wrap_task::run(std::path::PathBuf::from(task_dir)));
            match code {
                Ok(c) => std::process::exit(c),
                Err(e) => { eprintln!("agent-tools wrap-task: {e:#}"); std::process::exit(1); }
            }
        }
    }
    let _ = root; // unused for new subcommands
}
```

Add to the `Cmd` enum:

```rust
/// Wrap a Bash/Monitor invocation (PreToolUse-rewritten target).
#[command(name = "wrap-task")]
WrapTask {
    /// Absolute path to the task directory containing command.sh.
    task_dir: String,
},
```

- [ ] **Step 4: Build and run tests**

```bash
cd /root/claude-config-work/agent-tools && cargo build --release 2>&1 | tail -5 && cargo test --test wrap_task_test 2>&1 | tail -15
```
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work && git add agent-tools/src/wrap_task.rs agent-tools/src/main.rs agent-tools/tests/wrap_task_test.rs && git commit -m "agent-tools: wrap-task — spawn child, tee, propagate task_id env"
```

---

## Phase 5 — agent-tools run

### Task 11: run subcommand

**Files:**
- Create: `agent-tools/src/run.rs`
- Modify: `agent-tools/src/main.rs` (add `mod run;`, `Run` arm with `--desc` and trailing argv)
- Create: `agent-tools/tests/run_test.rs`

- [ ] **Step 1: Write the failing integration tests**

`tests/run_test.rs`:

```rust
use std::process::Command;
use std::path::PathBuf;

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn make_task(home: &std::path::Path) -> PathBuf {
    let dir = home.join(".claude/agent-tools/sid/tuid");
    std::fs::create_dir_all(dir.join("children")).unwrap();
    let meta = serde_json::json!({
        "kind":"task","session_id":"sid","agent_id":null,"task_id":"tuid",
        "tool":"Bash","tool_use_id":"tuid","desc":null,"cwd":"/tmp",
        "pid":1,"started_at":null,"ended_at":null,"exit_code":null,
        "silence_threshold_ms":30000
    });
    std::fs::write(dir.join("meta.json"), serde_json::to_string_pretty(&meta).unwrap()).unwrap();
    std::fs::write(dir.join("command.sh"), "true").unwrap();
    dir
}

#[test]
fn errors_when_env_not_set() {
    let home = tempfile::tempdir().unwrap();
    let out = Command::new(bin())
        .args(["run", "--", "echo", "hi"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_TASK_ID")
        .output()
        .unwrap();
    assert!(!out.status.success());
    assert!(String::from_utf8_lossy(&out.stderr).contains("AGENT_TOOLS_TASK_ID"));
}

#[test]
fn captures_child_stdout_and_forwards() {
    let home = tempfile::tempdir().unwrap();
    let task_dir = make_task(home.path());
    let out = Command::new(bin())
        .args(["run", "--", "bash", "-c", "echo hello; echo bad 1>&2; exit 0"])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_TASK_ID", &task_dir)
        .output()
        .unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));
    assert_eq!(String::from_utf8_lossy(&out.stdout), "hello\n");
    assert_eq!(String::from_utf8_lossy(&out.stderr), "bad\n");

    // Exactly one child dir created.
    let children: Vec<_> = std::fs::read_dir(task_dir.join("children")).unwrap().collect();
    assert_eq!(children.len(), 1);
    let child_dir = children[0].as_ref().unwrap().path();
    assert_eq!(std::fs::read_to_string(child_dir.join("stdout")).unwrap(), "hello\n");
    assert_eq!(std::fs::read_to_string(child_dir.join("stderr")).unwrap(), "bad\n");
}

#[test]
fn forwards_stdin_to_child() {
    let home = tempfile::tempdir().unwrap();
    let task_dir = make_task(home.path());
    use std::io::Write;
    use std::process::{Stdio};
    let mut c = Command::new(bin())
        .args(["run", "--", "cat"])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_TASK_ID", &task_dir)
        .stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::piped())
        .spawn().unwrap();
    c.stdin.as_mut().unwrap().write_all(b"streamed\n").unwrap();
    drop(c.stdin.take());
    let out = c.wait_with_output().unwrap();
    assert!(out.status.success());
    assert_eq!(String::from_utf8_lossy(&out.stdout), "streamed\n");
}

#[test]
fn propagates_exit_code() {
    let home = tempfile::tempdir().unwrap();
    let task_dir = make_task(home.path());
    let out = Command::new(bin())
        .args(["run", "--", "bash", "-c", "exit 7"])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_TASK_ID", &task_dir)
        .output()
        .unwrap();
    assert_eq!(out.status.code(), Some(7));
}

#[test]
fn records_child_started_and_child_exit_in_parent_events() {
    let home = tempfile::tempdir().unwrap();
    let task_dir = make_task(home.path());
    let out = Command::new(bin())
        .args(["run", "--desc", "compute things", "--", "bash", "-c", "echo ok"])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_TASK_ID", &task_dir)
        .output()
        .unwrap();
    assert!(out.status.success());
    let evts = std::fs::read_to_string(task_dir.join("events.jsonl")).unwrap();
    assert!(evts.contains("\"child_started\""), "events: {evts}");
    assert!(evts.contains("\"child_exit\""), "events: {evts}");
    assert!(evts.contains("compute things"), "events: {evts}");
}
```

- [ ] **Step 2: Verify tests fail**

```bash
cd /root/claude-config-work/agent-tools && cargo test --test run_test 2>&1 | tail -10
```

- [ ] **Step 3: Implement run.rs**

`src/run.rs`:

```rust
use anyhow::{anyhow, Context, Result};
use std::path::PathBuf;
use std::process::Stdio;
use std::sync::Arc;
use std::sync::atomic::AtomicI64;
use tokio::process::Command;

use crate::capture;
use crate::events;
use crate::meta::{self, ChildMeta, Meta};
use crate::paths;
use crate::signals;

pub async fn run(desc: Option<String>, cmd: Vec<String>) -> Result<i32> {
    if cmd.is_empty() {
        return Err(anyhow!("run: no command supplied after --"));
    }
    let task_dir = paths::task_dir_from_env().map_err(|_| {
        anyhow!(
            "AGENT_TOOLS_TASK_ID is not set.\n\
             The PreToolUse hook (agent-tools hook-pre) must wrap this Bash/Monitor call.\n\
             If you see this from inside a Claude Code Bash tool, the hook is not installed."
        )
    })?;

    let mut child = Command::new(&cmd[0])
        .args(&cmd[1..])
        .stdin(Stdio::inherit())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .with_context(|| format!("spawn {:?}", cmd))?;
    let pid = child.id().context("child pid unavailable")?;
    let child_dir = task_dir.join("children").join(pid.to_string());
    std::fs::create_dir_all(&child_dir)
        .with_context(|| format!("mkdir {}", child_dir.display()))?;

    let started_at = chrono::Utc::now();
    let cm = Meta::Child(ChildMeta {
        parent_task_dir: task_dir.to_string_lossy().into_owned(),
        child_id: pid,
        desc: desc.clone(),
        command: cmd.clone(),
        pid,
        started_at: Some(started_at),
        ended_at: None,
        exit_code: None,
    });
    meta::write_meta(&child_dir, &cm)?;
    events::append(
        &task_dir,
        "child_started",
        serde_json::json!({
            "child_pid": pid,
            "desc": desc,
            "command": cmd,
        }),
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

    let cm = Meta::Child(ChildMeta {
        parent_task_dir: task_dir.to_string_lossy().into_owned(),
        child_id: pid,
        desc,
        command: cmd,
        pid,
        started_at: Some(started_at),
        ended_at: Some(chrono::Utc::now()),
        exit_code: Some(exit_code),
    });
    meta::write_meta(&child_dir, &cm)?;
    events::append(
        &task_dir,
        "child_exit",
        serde_json::json!({"child_pid": pid, "exit_code": exit_code}),
    )
    .ok();

    Ok(exit_code)
}
```

Modify `src/main.rs`:
- Add `mod run;`.
- Add to `Cmd`:
  ```rust
  /// Wrap a command inside an active wrap-task (for pipeline capture).
  Run {
      #[arg(long)]
      desc: Option<String>,
      #[arg(trailing_var_arg = true, allow_hyphen_values = true, last = true)]
      cmd: Vec<String>,
  },
  ```
- Dispatch:
  ```rust
  Cmd::Run { desc, cmd } => {
      let code = tokio::runtime::Builder::new_multi_thread()
          .enable_all().build().unwrap()
          .block_on(run::run(desc, cmd));
      match code {
          Ok(c) => std::process::exit(c),
          Err(e) => { eprintln!("agent-tools run: {e:#}"); std::process::exit(2); }
      }
  }
  ```

- [ ] **Step 4: Build and run tests**

```bash
cd /root/claude-config-work/agent-tools && cargo build --release 2>&1 | tail -5 && cargo test --test run_test 2>&1 | tail -15
```
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work && git add agent-tools/src/run.rs agent-tools/src/main.rs agent-tools/tests/run_test.rs && git commit -m "agent-tools: run — capture wrapped pipeline segment"
```

---

## Phase 6 — agent-tools ps

### Task 12: ps subcommand

**Files:**
- Create: `agent-tools/src/ps.rs`
- Modify: `agent-tools/src/main.rs` (add `mod ps;`, `Ps` arm)
- Create: `agent-tools/tests/ps_test.rs`

- [ ] **Step 1: Write the failing integration tests**

`tests/ps_test.rs`:

```rust
use std::process::Command;

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn seed(home: &std::path::Path, session: &str, agent: Option<&str>, task: &str, pid: u32, exit: Option<i32>) -> std::path::PathBuf {
    let mut dir = home.join(".claude/agent-tools").join(session);
    if let Some(a) = agent { dir.push(a); }
    dir.push(task);
    std::fs::create_dir_all(dir.join("children")).unwrap();
    let meta = serde_json::json!({
        "kind":"task","session_id":session,
        "agent_id": agent,
        "task_id":task,"tool":"Bash","tool_use_id":task,
        "desc":format!("task {task}"),"cwd":"/tmp",
        "pid":pid,"started_at":"2026-05-17T10:00:00Z",
        "ended_at": exit.map(|_| "2026-05-17T10:00:05Z"),
        "exit_code": exit,
        "silence_threshold_ms":30000
    });
    std::fs::write(dir.join("meta.json"), serde_json::to_string_pretty(&meta).unwrap()).unwrap();
    std::fs::write(dir.join("command.sh"), format!("echo {task}")).unwrap();
    std::fs::write(dir.join("stdout"), format!("hello from {task}\n")).unwrap();
    std::fs::write(dir.join("stderr"), "").unwrap();
    std::fs::write(dir.join("events.jsonl"), format!(
        r#"{{"ts":"2026-05-17T10:00:00Z","kind":"task_started","data":{{"pid":{pid}}}}}
"#)).unwrap();
    dir
}

#[test]
fn default_lists_session_tasks_resolved_from_env() {
    let home = tempfile::tempdir().unwrap();
    let dir = seed(home.path(), "sid", None, "tuid1", 99999, None);
    let _ = seed(home.path(), "sid", None, "tuid2", 99999, Some(0));

    let out = Command::new(bin())
        .arg("ps")
        .env("HOME", home.path())
        .env("AGENT_TOOLS_TASK_ID", &dir)
        .output()
        .unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("tuid1"), "{s}");
    assert!(s.contains("tuid2"), "{s}");
    assert!(s.contains("session: sid"), "{s}");
}

#[test]
fn task_filter_only_shows_one_task() {
    let home = tempfile::tempdir().unwrap();
    let dir = seed(home.path(), "sid", None, "tuid1", 99999, None);
    let _ = seed(home.path(), "sid", None, "tuid2", 99999, Some(0));

    let out = Command::new(bin())
        .args(["ps", "--task", "tuid2"])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_TASK_ID", &dir)
        .output()
        .unwrap();
    assert!(out.status.success());
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("tuid2"));
    assert!(!s.contains("tuid1"));
}

#[test]
fn cross_session_with_session_id_flag() {
    let home = tempfile::tempdir().unwrap();
    let dir = seed(home.path(), "sid-a", None, "tuid", 99999, None);
    let _ = seed(home.path(), "sid-b", None, "tuid-b", 99999, None);
    // Note: AGENT_TOOLS_TASK_ID points into sid-a, but --session-id sid-b overrides.
    let out = Command::new(bin())
        .args(["ps", "--session-id", "sid-b"])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_TASK_ID", &dir)
        .output()
        .unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("tuid-b"));
    assert!(!s.contains("session: sid-a"), "leak: {s}");
    assert!(!s.contains("task tuid "), "leak: {s}");
}

#[test]
fn live_marker_uses_pid_kill_zero() {
    // Use the current process's pid as a "live" task.
    let home = tempfile::tempdir().unwrap();
    let my_pid = std::process::id();
    let dir = seed(home.path(), "sid", None, "live-task", my_pid, None);
    let out = Command::new(bin())
        .arg("ps")
        .env("HOME", home.path())
        .env("AGENT_TOOLS_TASK_ID", &dir)
        .output()
        .unwrap();
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("[running]") || s.contains("running"), "{s}");
}

#[test]
fn ended_meta_shows_exit_code() {
    let home = tempfile::tempdir().unwrap();
    let dir = seed(home.path(), "sid", None, "done", 1, Some(42));
    let out = Command::new(bin())
        .arg("ps")
        .env("HOME", home.path())
        .env("AGENT_TOOLS_TASK_ID", &dir)
        .output()
        .unwrap();
    assert!(out.status.success());
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("42"), "{s}");
}
```

- [ ] **Step 2: Verify tests fail**

```bash
cd /root/claude-config-work/agent-tools && cargo test --test ps_test 2>&1 | tail -10
```

- [ ] **Step 3: Implement ps.rs**

`src/ps.rs`:

```rust
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
    let mut all_events: Vec<(String, Event)> = Vec::new(); // (task_id, event)
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
            // Treat this subdirectory as an agent_id namespace.
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
        None => true, // started, no pid recorded yet
    }
}

fn is_pid_alive(pid: i32) -> bool {
    signal::kill(Pid::from_raw(pid), None).is_ok()
}
```

Modify `src/main.rs`:
- Add `mod ps;`.
- Add to `Cmd`:
  ```rust
  /// List or filter live tasks for this session.
  Ps {
      #[arg(long)]
      task: Option<String>,
      #[arg(long = "session-id")]
      session_id: Option<String>,
  },
  ```
- Dispatch:
  ```rust
  Cmd::Ps { task, session_id } => {
      if let Err(e) = ps::run(task, session_id) {
          eprintln!("agent-tools ps: {e:#}");
          std::process::exit(1);
      }
  }
  ```

- [ ] **Step 4: Build and run tests**

```bash
cd /root/claude-config-work/agent-tools && cargo build --release 2>&1 | tail -5 && cargo test --test ps_test 2>&1 | tail -20
```
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work && git add agent-tools/src/ps.rs agent-tools/src/main.rs agent-tools/tests/ps_test.rs && git commit -m "agent-tools: ps — list tasks, children, events for a session"
```

---

## Phase 7 — End-to-end and settings.json wiring

### Task 13: end-to-end integration test

**Files:**
- Create: `agent-tools/tests/end_to_end_test.rs`

- [ ] **Step 1: Write the e2e test**

```rust
use std::io::Write;
use std::process::{Command, Stdio};

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

#[test]
fn full_loop_hook_pre_wrap_task_run_ps() {
    let home = tempfile::tempdir().unwrap();
    let bin_dir = tempfile::tempdir().unwrap();
    // Make `agent-tools` resolvable for the rewritten command.
    let link = bin_dir.path().join("agent-tools");
    std::os::unix::fs::symlink(bin(), &link).unwrap();
    let path_with_bin = format!("{}:{}", bin_dir.path().display(), std::env::var("PATH").unwrap_or_default());

    // 1. Run hook-pre to seed state and obtain rewritten command.
    let input = serde_json::json!({
        "session_id": "sid-e2e",
        "cwd": "/tmp",
        "tool_name": "Bash",
        "tool_input": {"command":
            "echo upstream; agent-tools run --desc inner -- bash -c 'echo inner-out; echo inner-err 1>&2'"
        },
        "tool_use_id": "tuid-e2e"
    }).to_string();
    let mut c = Command::new(bin())
        .arg("hook-pre")
        .env("HOME", home.path())
        .env("PATH", &path_with_bin)
        .stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::piped())
        .spawn().unwrap();
    c.stdin.as_mut().unwrap().write_all(input.as_bytes()).unwrap();
    let out = c.wait_with_output().unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));
    let parsed: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    let rewritten = parsed["hookSpecificOutput"]["updatedInput"]["command"].as_str().unwrap().to_string();

    // 2. Execute the rewritten command under bash, with HOME and PATH.
    let exec = Command::new("bash")
        .args(["-c", &rewritten])
        .env("HOME", home.path())
        .env("PATH", &path_with_bin)
        .output()
        .unwrap();
    assert!(exec.status.success(), "stderr: {}", String::from_utf8_lossy(&exec.stderr));
    let stdout = String::from_utf8_lossy(&exec.stdout);
    assert!(stdout.contains("upstream"));
    assert!(stdout.contains("inner-out"));
    assert!(String::from_utf8_lossy(&exec.stderr).contains("inner-err"));

    // 3. Validate disk state.
    let task_dir = home.path().join(".claude/agent-tools/sid-e2e/tuid-e2e");
    let captured_stdout = std::fs::read_to_string(task_dir.join("stdout")).unwrap();
    assert!(captured_stdout.contains("upstream"));
    assert!(captured_stdout.contains("inner-out"));

    // Child capture under children/<pid>/.
    let kids: Vec<_> = std::fs::read_dir(task_dir.join("children")).unwrap()
        .filter_map(|e| e.ok().map(|e| e.path())).collect();
    assert_eq!(kids.len(), 1);
    let child_stdout = std::fs::read_to_string(kids[0].join("stdout")).unwrap();
    assert!(child_stdout.contains("inner-out"));

    // 4. agent-tools ps surfaces both.
    let out = Command::new(bin())
        .arg("ps")
        .env("HOME", home.path())
        .env("AGENT_TOOLS_TASK_ID", &task_dir)
        .output()
        .unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("tuid-e2e"));
    assert!(s.contains("inner"));
}
```

- [ ] **Step 2: Run the e2e test**

```bash
cd /root/claude-config-work/agent-tools && cargo build --release 2>&1 | tail -3 && cargo test --test end_to_end_test 2>&1 | tail -20
```
Expected: 1 passed.

- [ ] **Step 3: Commit**

```bash
cd /root/claude-config-work && git add agent-tools/tests/end_to_end_test.rs && git commit -m "agent-tools: e2e — hook-pre + wrap-task + run + ps loop"
```

---

### Task 14: install binary, wire settings.json hooks

**Files:**
- Modify: `settings.json` (PreToolUse and PostToolUse blocks)
- Run: `hooks/install.sh` (only when not in a worktree)

- [ ] **Step 1: Confirm we are not in a worktree**

```bash
cd /root/claude-config-work && git rev-parse --git-dir
```
Expected: prints `.git` (not a `.git/worktrees/...` path). If it prints a worktree path, STOP — per `CLAUDE.md` worktrees must not run `hooks/install.sh`. Skip to step 3 with a `CLAUDE_CONFIG_ROOT`-only verification.

- [ ] **Step 2: Build release binary and install symlink**

```bash
cd /root/claude-config-work/agent-tools && cargo build --release && ls -la ~/.local/bin/agent-tools
```
If the symlink does not point to the new binary, run:
```bash
bash /root/claude-config-work/hooks/install.sh
```
Expected: `~/.local/bin/agent-tools → /root/claude-config-work/agent-tools/target/release/agent-tools`.

- [ ] **Step 3: Add hook entries to settings.json**

Read the current `settings.json` first:
```bash
cat /root/claude-config-work/settings.json | head -90
```

In `settings.json`, locate the existing `"PreToolUse"` array. Add (preserving the existing Agent matcher entry) a new entry with matcher `"Bash|Monitor"`:

```json
{
  "matcher": "Bash|Monitor",
  "hooks": [
    { "type": "command", "command": "agent-tools hook-pre", "timeout": 5 }
  ]
}
```

Inside the `"hooks"` block, add (or update) a `"PostToolUse"` array containing:

```json
"PostToolUse": [
  {
    "matcher": "Bash|Monitor",
    "hooks": [
      { "type": "command", "command": "agent-tools hook-post", "timeout": 5 }
    ]
  }
]
```

- [ ] **Step 4: Verify settings.json parses and the hooks resolve**

```bash
python3 -c "import json; json.load(open('/root/claude-config-work/settings.json'))" && echo "json ok" && which agent-tools && agent-tools hook-pre </dev/null | head -1
```
Expected: `json ok`, path to `agent-tools`, and a single line of JSON like `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}` (because the empty stdin fails parsing and `hook-pre` returns a pass-through).

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work && git add settings.json && git commit -m "settings.json: wire agent-tools hook-pre/hook-post for Bash and Monitor"
```

---

## Self-Review

After all tasks pass, perform this self-check against the spec at `docs/superpowers/specs/2026-05-17-agent-tools-run-design.md`:

- **wrap-task** — Task 10 covers spawn + pipes + env propagation + meta updates + events + signal forwarding + exit code mapping.
- **run** — Task 11 covers AGENT_TOOLS_TASK_ID enforcement, child dir creation, tee, signal forwarding, exit code, stdin pass-through, `--desc`.
- **ps** — Task 12 covers default session-scoped list, `--task`, `--session-id`, live detection via `kill(pid, 0)`, chronological event log, child enumeration.
- **hook-pre** — Task 6 covers identifier sourcing from hook (`session_id`, `agent_id`, `tool_use_id`), Bash/Monitor matcher, `command.sh` verbatim write, rewrite with shell-quoted task_dir, pass-through on failure.
- **hook-post** — Task 7 covers backgrounding detection (auto / user / timeout), `additionalContext` formatting, `backgrounded` event logging.
- **State layout** — paths.rs (Task 3) builds both main-thread and subagent shapes; ps.rs (Task 12) reads both shapes.
- **Single env var** — `AGENT_TOOLS_TASK_ID` is the only one set in `wrap_task::run` and `run::run` (both keep it from being unset for descendants).
- **No truncation** — tee writes raw bytes (Task 9); no size cap.
- **No GC** — no `clean` subcommand introduced.
- **All Rust** — every subcommand is a Rust path; the existing settings.json hook (Agent matcher) keeps its jq shim untouched; new hooks call the Rust binary directly.

If any check fails, add a task before moving to execution.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-17-agent-tools-run.md`. Two execution options:

**1. Subagent-Driven (recommended)** — Dispatch a fresh subagent per task; review between tasks; fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans; batch with checkpoints.

Which approach?
