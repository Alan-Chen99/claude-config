# agent-tools — Option B implementation plan

This plan replaces the prior wrap-task-based approach. Drop wrap-task
entirely; the PreToolUse hook becomes a minimal env-injection prefix.
Top-level Bash output is no longer captured. Capture happens only when
the agent invokes `agent-tools run`. PostToolUse lists every such
capture so the agent can `Read` the disk path.

Companion docs:
- `plans/agent-tools-run-spec.md` — updated spec (Option B).
- `plans/wrap-task-bash-state-experiment.md` — historical evidence for
  why wrap-task's `bash <command.sh>` invocation broke shell-state
  invariants ($-, $0, monitor, aliases, post-`cd` cwd capture). Cited
  in Decision #1 below.

---

## Design decisions

| # | Decision | Options considered | Chosen | Reason |
|---|----------|--------------------|--------|--------|
| 1 | Drop wrap-task, fix its spawn, or keep as-is? | (A) keep, `bash <command.sh>`; (B) drop, hook prepends `unset` only; (C) keep, fix spawn to `bash -c "source <snap> && eval …"` | B | A leaves the shell-state divergence broken. C requires per-session snapshot discovery and the on-disk filename `/root/.claude/shell-snapshots/snapshot-bash-<ts>-<rand>.sh` has no clean `session_id`→filename mapping. Empirical reads of wrap-task captures across 7 days of session logs: **0** — the "always-on safety net" of A wasn't being collected on. |
| 2 | Env var name for the parent dir | `AGENT_TOOLS_TASK_ID`, `AGENT_TOOLS_PARENT_DIR`, `CLAUDE_AGENT_TOOLS_PARENT_DIR` | `AGENT_TOOLS_PARENT_DIR` | Reflects new semantics (parent of run captures, not a wrap-task task id). Matches the `AGENT_TOOLS_` prefix already used. `CLAUDE_` prefix is noise; nothing else in this binary uses it. |
| 3 | Directory layout under parent | `<tool_use_id>/children/<pid>/`, `<tool_use_id>/runs/<pid>/`, `<tool_use_id>/<pid>/` | `<tool_use_id>/<pid>/` | No top-level files at `<tool_use_id>/` (no command.sh, no top-level stdout/stderr), so `children/` or `runs/` is a dead nesting layer. Bare `<pid>/` subdirs are unambiguous because the parent dir is dedicated to runs. |
| 4 | When does parent dir get created? | (eager) PreToolUse mkdirs it; (lazy) first `agent-tools run` mkdirs it | lazy | Bash calls without any `agent-tools run` produce zero disk state — matches the spec's "no top-level capture" promise. PostToolUse's existence-check on the dir then doubles as "did anything happen?" |
| 5 | PostToolUse listing format | (a) multi-line via `\n`; (b) single-line `;`-separated | `;`-separated | Same precedent as existing `hook_post.rs:56-64` (Decision #2 in the prior plan). Rendering of `\n` in `additionalContext` is unverified in this codebase. |
| 6 | Per-capture line format | (a) path-only; (b) `<desc> → <dir>/{stdout,stderr}`; (c) `<desc> stdout=<path> stderr=<path>` | b | `{stdout,stderr}` brace notation is shell-readable and halves the printed path length. Desc-first prefix makes the listing greppable by the agent's intent. |
| 7 | Emit listing on success when no run happened? | always-emit "no captures"; silent | silent | Bash tool calls without runs are the common case. Emitting "no captures" on every call costs ~30 tokens × hundreds of calls for zero information. The forgotten-wrap failure mode is handled via the prompt rule, not via paths-block chrome. |
| 8 | Keep `events.jsonl` bg log? | keep (write `backgrounded` event under parent_dir if it exists); drop | drop | No reader exists for bg events; `ps` shows `child_started`/`child_exit` for runs but no top-level lifecycle. Less state to maintain. The agent-facing notice in `additionalContext` is the only record needed. |
| 9 | `agent-tools run` standalone (outside Bash hook) | allow (fallback to `~/.claude/agent-tools/standalone/<uuid>/`); error loudly | error loudly | Same as current `run.rs:17-23`. Standalone capture is out of scope; the agent invokes `run` inside a Bash tool, which always has the env via PreToolUse. |
| 10 | Backwards compatibility for old `AGENT_TOOLS_TASK_ID` env / `task_dir_from_env` | preserve; rename | rename | Per project coding guidelines ("Ignore backwards compatibility unless explicitly told to maintain it"). wrap-task is being deleted; no consumers of the old env var survive. |

---

## Change 1 — Delete `agent-tools/src/wrap_task.rs`

Delete the file. From `agent-tools/src/main.rs`:

- Remove `mod wrap_task;` (line 18).
- Remove the `Cmd::WrapTask { task_dir: String }` variant declaration
  (lines 64-68) and its `#[command(name = "wrap-task")]` attribute.
- Remove the `Cmd::WrapTask { task_dir } => { … wrap_task::run(…) … }`
  dispatch arm (lines 167-177).
- Remove the `Cmd::WrapTask { .. } => unreachable!()` arm (line 270).

---

## Change 2 — `agent-tools/src/hook_pre.rs`

Replace the body of `pub fn run()` with the version below. Drop
`prepare_task_dir` and all of its callers — no `command.sh`, no
`meta.json`, no `mkdir`.

```rust
pub fn run() -> Result<()> {
    let mut buf = String::new();
    std::io::stdin().read_to_string(&mut buf).context("read stdin")?;

    let input = match hook_input::parse_pre(&buf) {
        Ok(p) => p,
        Err(e) => {
            eprintln!("agent-tools hook-pre: parse error: {e:#}");
            print_allow_passthrough();
            return Ok(());
        }
    };

    if input.tool_name != "Bash" && input.tool_name != "Monitor" {
        print_allow_passthrough();
        return Ok(());
    }

    let parent_dir = paths::parent_dir_for(
        &input.session_id,
        input.agent_id.as_deref(),
        &input.tool_use_id,
    )?;
    let quoted_dir = shell_single_quote(&parent_dir.to_string_lossy());
    let new_command = format!(
        "unset HTTPS_PROXY NODE_EXTRA_CA_CERTS NODE_OPTIONS; \
         export AGENT_TOOLS_PARENT_DIR={quoted_dir}; \
         {orig}",
        orig = input.tool_input.command,
    );
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
```

Keep `print_allow_passthrough` and `shell_single_quote` (including its
tests). Remove imports: `crate::meta::{Meta, TaskMeta}`, `std::fs`,
`std::path::PathBuf`, `SILENCE_THRESHOLD_MS`.

**Shell-quoting verification**: the hook returns
`unset …; export AGENT_TOOLS_PARENT_DIR='<path>'; <orig>`. CC's
pipeline wraps user commands in `eval '<…>'` and handles `'` escaping
of embedded single quotes via `'\''`. The result evaluates back to the
intended string. (Verified by inspection against the experiment-notes
capture of CC's `ps -o args` output at
`wrap-task-bash-state-experiment.md:31-36`.)

---

## Change 3 — `agent-tools/src/hook_post.rs`

Replace `pub fn run()`. Adds listing of run captures; preserves bg
detection. Drops the `events::append("backgrounded", …)` write (per
Decision #8).

```rust
use anyhow::{Context, Result};
use std::fs;
use std::io::Read;
use std::path::Path;

use crate::hook_input;
use crate::meta::ChildMeta;
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

    let parent_dir = paths::parent_dir_for(
        &input.session_id,
        input.agent_id.as_deref(),
        &input.tool_use_id,
    )?;

    let captures = list_captures(&parent_dir);
    let bg = bg_notice(&input);

    if captures.is_empty() && bg.is_none() {
        return Ok(());
    }

    let mut parts: Vec<String> = Vec::new();
    if !captures.is_empty() {
        let listing: Vec<String> = captures.iter().map(format_capture).collect();
        parts.push(format!(
            "[agent-tools] captures from this Bash call: {}",
            listing.join("; "),
        ));
    }
    if let Some(b) = bg {
        parts.push(b);
    }

    let out = serde_json::json!({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": parts.join(" ")
        }
    });
    println!("{}", serde_json::to_string(&out)?);
    Ok(())
}

struct Capture {
    dir: std::path::PathBuf,
    desc: Option<String>,
}

fn list_captures(parent_dir: &Path) -> Vec<Capture> {
    if !parent_dir.is_dir() {
        return Vec::new();
    }
    let rd = match fs::read_dir(parent_dir) {
        Ok(r) => r,
        Err(_) => return Vec::new(),
    };
    let mut out = Vec::new();
    for entry in rd.flatten() {
        let p = entry.path();
        if !p.is_dir() {
            continue;
        }
        let desc = fs::read_to_string(p.join("meta.json"))
            .ok()
            .and_then(|s| serde_json::from_str::<ChildMeta>(&s).ok())
            .and_then(|c| c.desc);
        out.push(Capture { dir: p, desc });
    }
    out.sort_by(|a, b| a.dir.cmp(&b.dir));
    out
}

fn format_capture(c: &Capture) -> String {
    match &c.desc {
        Some(d) => format!("{} → {}/{{stdout,stderr}}", d, c.dir.display()),
        None => format!("{}/{{stdout,stderr}}", c.dir.display()),
    }
}

fn bg_notice(input: &hook_input::PostToolUseInput) -> Option<String> {
    let bg_task_id = input.tool_response.get("backgroundTaskId").and_then(|v| v.as_str())?;
    let auto = input.tool_response.get("assistantAutoBackgrounded").and_then(|v| v.as_bool()).unwrap_or(false);
    let user = input.tool_response.get("backgroundedByUser").and_then(|v| v.as_bool()).unwrap_or(false);
    let cause = if auto {
        "assistant-mode auto-background (KAIROS)".to_string()
    } else if user {
        "user manually backgrounded (Ctrl+B)".to_string()
    } else {
        let limit = input.tool_input.timeout.unwrap_or(120_000);
        format!("timeout ({limit}ms limit hit)")
    };
    Some(format!(
        "BACKGROUNDED: Command was involuntarily backgrounded. Cause: {cause}. \
         Process is still running (task_id: {bg_task_id}). \
         To kill it: use TaskStop tool with task_id {bg_task_id}."
    ))
}
```

Drop the `crate::events` import — no events written from this hook anymore.

---

## Change 4 — `agent-tools/src/run.rs`

Replace `paths::task_dir_from_env()` (line 17) with the new
`paths::parent_dir_from_env()` reading `AGENT_TOOLS_PARENT_DIR`. Drop
the `children/` segment from the capture path. Lazily mkdir the parent
dir on first run (Decision #4).

Specifically, replace lines 17-35 with:

```rust
let parent_dir = paths::parent_dir_from_env().map_err(|_| {
    anyhow!(
        "AGENT_TOOLS_PARENT_DIR is not set.\n\
         The PreToolUse hook (agent-tools hook-pre) must run before this command.\n\
         If you see this from inside a Claude Code Bash tool, the hook is not installed."
    )
})?;
std::fs::create_dir_all(&parent_dir)
    .with_context(|| format!("mkdir {}", parent_dir.display()))?;

let mut child = Command::new(&cmd[0])
    .args(&cmd[1..])
    .stdin(Stdio::inherit())
    .stdout(Stdio::piped())
    .stderr(Stdio::piped())
    .spawn()
    .with_context(|| format!("spawn {:?}", cmd))?;
let pid = child.id().context("child pid unavailable")?;
let child_dir = parent_dir.join(pid.to_string());
std::fs::create_dir_all(&child_dir)
    .with_context(|| format!("mkdir {}", child_dir.display()))?;
```

Adjust the two `ChildMeta { … }` constructors (lines 38-46 and lines
115-124) to drop the `parent_task_dir` field (removed in Change 6).

`events::append(&parent_dir, "child_started", …)` and `child_exit` calls
keep their target as `parent_dir/events.jsonl` — semantics unchanged,
only the variable name changes from `task_dir` to `parent_dir`.

The `crate::meta::{self, ChildMeta, Meta}` import simplifies to
`crate::meta::{self, ChildMeta}` (the `Meta` enum is removed in Change
6).

---

## Change 5 — `agent-tools/src/paths.rs`

Rename for new semantics. Update doc comments, error messages, and
tests in this file (lines 51-92):

- `pub fn task_dir_for(...)` → `pub fn parent_dir_for(...)`. Signature
  and body unchanged.
- `pub fn task_dir_from_env() -> Result<PathBuf>` →
  `pub fn parent_dir_from_env() -> Result<PathBuf>`. Read
  `AGENT_TOOLS_PARENT_DIR` instead of `AGENT_TOOLS_TASK_ID`. Update
  the error message accordingly.
- `pub fn parse_task_dir(...)` → `pub fn parse_parent_dir(...)`.
  Signature and body unchanged.

Update the unit tests at lines 56-91 to use the new names.

---

## Change 6 — `agent-tools/src/meta.rs`

Drop the `Meta` enum and `TaskMeta` struct. Expose `ChildMeta` as the
sole serialized type. Drop the `parent_task_dir` field from `ChildMeta`
(unused — the child's dir location is the dir containing the meta.json).

```rust
use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ChildMeta {
    pub child_id: u32,
    pub desc: Option<String>,
    pub command: Vec<String>,
    pub started_at: Option<DateTime<Utc>>,
    pub ended_at: Option<DateTime<Utc>>,
    pub exit_code: Option<i32>,
}

pub fn write_meta(dir: &Path, meta: &ChildMeta) -> Result<()> {
    fs::create_dir_all(dir).with_context(|| format!("mkdir {}", dir.display()))?;
    let final_path = dir.join("meta.json");
    let tmp_path = dir.join("meta.json.tmp");
    let json = serde_json::to_vec_pretty(meta)?;
    fs::write(&tmp_path, &json).with_context(|| format!("write {}", tmp_path.display()))?;
    fs::rename(&tmp_path, &final_path)
        .with_context(|| format!("rename {} -> {}", tmp_path.display(), final_path.display()))?;
    Ok(())
}

pub fn read_meta(dir: &Path) -> Result<ChildMeta> {
    let bytes = fs::read(dir.join("meta.json"))
        .with_context(|| format!("read {}/meta.json", dir.display()))?;
    Ok(serde_json::from_slice(&bytes)?)
}
```

Update the unit tests in this file to use the simplified struct.

Note: existing meta.json files on disk from prior wrap-task runs become
unreadable (they carry the `kind: "task"` or `kind: "child"` tag that
the new format doesn't expect). Acceptable — those files are stale and
the user can `rm -rf ~/.claude/agent-tools/` on landing.

---

## Change 7 — `agent-tools/src/ps.rs`

Rewrite for the new addressing model. There are no top-level tasks;
each session dir contains tool_use_id dirs (optionally nested under a
subagent dir), and each tool_use_id dir contains pid subdirs (the
captures).

Walk:

```
session_dir/
  ├─ <tool_use_id>/<pid>/{stdout,stderr,meta.json}   ← main-thread captures
  └─ <subagent_id>/<tool_use_id>/<pid>/{stdout,stderr,meta.json}   ← subagent captures
```

Detection of subagent vs tool_use_id at the second level: a tool_use_id
dir contains pid-named subdirs (numeric); a subagent dir contains
tool_use_id-named subdirs (non-numeric). Use this to discriminate.

Output structure:

```
session: <sid>
agent: _main
  tool-use <tuid> (2 captures):
    pid 12345 [exited 0]
      desc:    pytest
      cmd:     pytest tests/foo.py
      stdout:  /h/.../<tuid>/12345/stdout  (4521 bytes)
      stderr:  /h/.../<tuid>/12345/stderr  (0 bytes)
    pid 12346 [running]
      ...
agent: <subagent-id>
  tool-use <tuid2> (1 capture):
    ...

events (chronological, all captures):
  HH:MM:SS.mmm  child_started  <tuid>  pid=12345 desc=...
  HH:MM:SS.mmm  child_exit     <tuid>  pid=12345 exit_code=0
```

Liveness uses the existing `is_pid_alive(child_id)` check. Drop all
`TaskMeta`-related code, the `_main` task header heuristic, and the
`cmd (truncated): command.sh` line.

`--task <id>` filter now matches `tool_use_id` (semantically same as
before — current `TaskMeta.task_id` was always set to `tool_use_id` per
`hook_pre.rs:62-64`).

---

## Change 8 — `agent-tools/src/main.rs`

Remove `mod wrap_task;` (line 18), the `Cmd::WrapTask` variant
(lines 64-68), its dispatch arm (lines 167-177), and the
`Cmd::WrapTask { .. } => unreachable!()` arm (line 270).

No other changes. `Cmd::Run`, `HookPre`, `HookPost`, `Ps` dispatches
stay.

---

## Change 9 — Tests

All 5 files under `agent-tools/tests/` reference the old wrap-task model
and need coordinated updates with Changes 1-8. Specifics per file.

### 9.1 `agent-tools/tests/wrap_task_test.rs` — DELETE

Delete the file entirely (123 lines). The `wrap-task` subcommand no
longer exists.

### 9.2 `agent-tools/tests/hook_pre_test.rs` — rewrite

The current file (114 lines) asserts hook_pre writes `command.sh` and
creates the task_dir eagerly. Both behaviors are removed. Replace the
existing tests with:

1. **Bash with simple command**: `updatedInput.command` matches the
   regex
   `^unset HTTPS_PROXY NODE_EXTRA_CA_CERTS NODE_OPTIONS; export AGENT_TOOLS_PARENT_DIR='[^']+'; echo hi$`.
2. **Path encoding**: the `AGENT_TOOLS_PARENT_DIR` value ends with
   `<session>/<tool_use_id>` when `agent_id` is absent.
3. **Subagent**: with `agent_id` set, the exported path ends with
   `<session>/<subagent>/<tool_use_id>`.
4. **Non-Bash, non-Monitor (Read)**: passthrough — `permissionDecision: allow`
   with no `updatedInput`.
5. **No side effects on disk**: the parent dir is NOT created by
   `hook_pre` (lazy creation per Decision #4; first `agent-tools run`
   makes it). Assert `parent_dir.exists() == false` after the hook runs.
6. **Single-quote in original command**: a user command containing `'`
   is preserved byte-for-byte after the `; ` separator (CC's eval will
   handle outer quoting).

Remove all `command.sh`-related assertions (current lines 46-48, 112).

### 9.3 `agent-tools/tests/hook_post_test.rs` — rewrite

Existing tests (102 lines) cover only the bg case. Replace with:

1. **No parent dir on disk, no bg**: no `additionalContext` emitted
   (no `hookSpecificOutput` present in stdout, or empty stdout).
2. **Parent dir exists with two pid subdirs (each with meta.json), no
   bg**: `additionalContext` contains
   `[agent-tools] captures from this Bash call:` followed by both
   subdir paths joined with `; `. Format per capture is
   `<desc> → <dir>/{stdout,stderr}` when meta.json has `desc`, bare
   `<dir>/{stdout,stderr}` otherwise.
3. **`backgroundTaskId` present, no captures**: `additionalContext`
   contains only the `BACKGROUNDED:` notice.
4. **Both captures and `backgroundTaskId`**: `additionalContext`
   contains captures listing followed by a space and the `BACKGROUNDED:`
   notice.
5. **Subagent with captures**: emitted paths contain the subagent id
   segment.
6. **Per-capture format with and without `desc`** (sub-assertions of
   case 2, but verify both branches explicitly).
7. **Non-Bash, non-Monitor (Read)**: no output.

Remove any pre-existing assertion on the
`"Captured output paths in: {task_dir}"` fragment.

### 9.4 `agent-tools/tests/run_test.rs` — update

Current (103 lines) sets `AGENT_TOOLS_TASK_ID` env and writes
`command.sh` to simulate a wrap-task'd environment. Updates:

1. Rename all `AGENT_TOOLS_TASK_ID` → `AGENT_TOOLS_PARENT_DIR` (6
   occurrences).
2. Remove all `command.sh` write calls (1 occurrence) — `agent-tools run`
   only needs the parent dir to exist (or not exist; it mkdirs lazily).
3. The "loud error when env missing" test (current lines 28-32): keep
   the test but update the asserted substring from `AGENT_TOOLS_TASK_ID`
   to `AGENT_TOOLS_PARENT_DIR`.
4. Add a test: `agent-tools run` lazily creates the parent dir when
   `AGENT_TOOLS_PARENT_DIR` points to a non-existent path.
5. Verify the child capture dir is at `<parent>/<pid>/` (no
   `children/` segment in the path).

### 9.5 `agent-tools/tests/ps_test.rs` — rewrite

Current (115 lines) sets up TaskMeta on disk and asserts on the
`agent-tools ps` output structure. `TaskMeta` no longer exists; ps now
enumerates `<tool_use_id>/<pid>/` directly. Replace with:

1. **No state on disk**: `agent-tools ps --session-id <fresh-sid>`
   prints `session: <sid>\n(no state on disk)` and exits 0.
2. **One tool_use_id with two captures (main thread)**: set up
   `<session>/<tool_use_id>/<pid1>/meta.json` and same for `<pid2>`;
   `ps --session-id <sid>` lists both under `agent: _main` showing
   their desc, cmd, stdout, stderr paths and sizes.
3. **Subagent capture**: set up
   `<session>/<subagent>/<tool_use_id>/<pid>/`; ps shows it under
   `agent: <subagent>`.
4. **`--task <tuid>` filter**: limits output to one tool_use_id.
5. **Events chronological merge**: events.jsonl entries from multiple
   captures appear in chronological order in the "events" section.

Drop all `AGENT_TOOLS_TASK_ID` env var usage (5 occurrences); ps now
requires `--session-id` when not invoked inside a Bash tool (and the
test harness isn't a Bash tool). The current `task_dir_from_env`
fallback in `ps.rs:17` is removed in Change 7.

### 9.6 `agent-tools/tests/end_to_end_test.rs` — rewrite

Current single test `full_loop_hook_pre_wrap_task_run_ps` exercises:
PreToolUse hook → wrap-task → run → ps. The wrap-task step is gone.

Replace with a single test `full_loop_hook_pre_run_hook_post_ps` that:

1. Invokes `agent-tools hook-pre` with a synthetic Bash PreToolUse JSON;
   captures the rewritten command from `updatedInput.command`.
2. `bash -c`s the rewritten command, where the user's part is
   `agent-tools run --desc probe -- echo hi`. Verifies stdout is
   `hi\n`.
3. Verifies the capture file at
   `<expected parent>/<pid>/stdout` contains `hi\n`. (The pid is
   discoverable by listing the parent dir.)
4. Invokes `agent-tools hook-post` with a Bash PostToolUse JSON
   (matching session_id, tool_use_id); captures stdout.
5. Asserts the PostToolUse `additionalContext` contains
   `[agent-tools] captures from this Bash call: probe → <expected dir>/{stdout,stderr}`.
6. Invokes `agent-tools ps --session-id <sid>`; asserts the capture
   appears in the listing with `desc: probe`.

### 9.7 Build/test verification

After all changes:

```
cd /root/claude-config-work/agent-tools && cargo build --release && cargo test
```

Expected: clean build, all tests pass. Any failure here points back to a
specific Change above; do not paper over with `#[ignore]` or stub
assertions.

---

## Change 10 — `sys_prompt/alan-default-next.md`

Insert a new `## Bash Output Recovery (agent-tools run)` subsection
between the current end of `## Bash Tool Timeout Behavior` (line 182,
last bullet "if a 3-second test hasn't finished in 120s, it is stuck,
not slow.") and the next heading `# Communication` (line 184). Preserve
the one-blank-line separator above and below to match existing style.

Exact text to insert:

```
## Bash Output Recovery (agent-tools run)

Claude Code may truncate tool results, and pipelines truncate upstream
stages (`| tail`, `| head`, `| grep`, `| wc -l`, `| jq .field`). Top-
level Bash output is NOT automatically captured to disk. To preserve
output that would otherwise be lost, wrap the producing stage with
`agent-tools run --desc <short label> -- <command>`. It tees stdout and
stderr to disk and forwards them transparently to the next pipe stage.
After the Bash call completes, the PostToolUse hook lists every
`agent-tools run` capture from that call in `additionalContext` — Read
the listed paths for the full untruncated output.

Wrap when:

- The command is slow (compile, test suite, model inference).
- The command costs money (paid API call, GPU time).
- The command has side effects you don't want to repeat (apt, gdb,
  schema migration, network mutation).
- A downstream pipe stage will discard the output (truncating filter).
- Tool-result truncation could hide what you need (e.g. `cargo test -v`
  output volume exceeds CC's display cap).

When in doubt, wrap. A disk capture costs nothing; re-running an
expensive producer wastes time and money.

Examples:

    # Top-level — captured under .../<tool_use_id>/<pid>/{stdout,stderr}
    agent-tools run --desc pytest -- pytest tests/foo.py

    # Upstream stages — each wrapped stage gets its own capture
    find . | agent-tools run --desc wc -- xargs wc -l | tail -3

    # Multiple intermediate captures in one pipeline
    find . | agent-tools run --desc found -- xargs wc -l | agent-tools run --desc counts -- sort -n | tail -3

    # Shell features (redirection, glob expansion) — wrap with bash -c
    agent-tools run --desc build -- bash -c 'make 2>&1' | tail -20

The PostToolUse listing is the path to Read for full output. Do not
re-run the producer.
```

---

## Mandatory verification before commit

After applying all changes and rebuilding:

```
cd /root/claude-config-work/agent-tools && cargo build --release
```

In a fresh Claude Code session:

```
echo "hi $(date +%s)" | agent-tools run --desc probe -- cat | head -1
```

Verify:

1. Visible tool result contains `hi <timestamp>`.
2. PostToolUse `additionalContext` contains
   `[agent-tools] captures from this Bash call: probe → /…/<tool_use_id>/<pid>/{stdout,stderr}`.
3. `Read` the listed `<dir>/stdout` → `hi <timestamp>\n` (cat's output;
   proves capture works).
4. Run `bash -c 'echo "$-"; echo "$0"; set -o | grep -E "monitor|onecmd"'`
   from a Bash tool call. Confirm `$-` contains `m` (monitor) and `t`
   (onecmd-like flags per CC's snapshot), `$0` is `bash`, and `monitor`
   is `on`. (Proves Option B closed the I3 gap from
   `wrap-task-bash-state-experiment.md:43-54`.)
5. Run a Bash call with no `agent-tools run` invocation. Confirm
   PostToolUse stays silent (no `additionalContext`) and no dir is
   created under `~/.claude/agent-tools/<session>/<tool_use_id>/`.

If any step diverges, fix the code to match observed behavior before
committing.

---

## Environment requirements

- `agent-tools` binary at `~/.local/bin/agent-tools` (canonical install
  via `install.sh`; do NOT run `install.sh` from a worktree — would
  re-point the symlink at the worktree's build and break other
  sessions).
- PreToolUse + PostToolUse hooks for `Bash|Monitor` wired in
  `settings.json:70-91`. No `settings.json` change.
- Writable `~/.claude/agent-tools/`.
- `cargo` to rebuild after Rust changes.

---

## Known tradeoffs

- **Top-level capture is gone.** If the agent runs `expensive | tail`
  without wrapping, the upstream output is lost. The prompt rule
  (Change 10) is the sole guard. Accepted because:
  - Empirical: **0 reads** of wrap-task disk captures across 7 days of
    session logs (the always-on safety net wasn't being used).
  - The alternative (Option C: fix wrap-task spawn) requires per-
    session snapshot discovery with no clean `session_id`→filename
    mapping.
- **Loud Failure principle**: a forgotten wrap produces silently
  missing output. Mitigation: the prompt rule biases toward "when in
  doubt, wrap." Post-landing, consider instrumenting the hook to log
  capture-per-call frequency to measure the forgotten-wrap rate.
- **`ps` no longer shows top-level Bash calls.** Only Bash calls that
  invoked `agent-tools run` show up. The "all live tasks in this
  session" wording in the spec was always more useful for long-runner
  cases; instant Bash calls left empty entries nobody read.
- **`backgrounded` event log dropped.** The agent-facing notice in
  `additionalContext` is the only record; no `events.jsonl` write from
  hook-post.
- **Stale meta.json files** on disk from prior wrap-task runs become
  unreadable (the new `ChildMeta` format has no `kind` tag). User
  removes them manually with `rm -rf ~/.claude/agent-tools/` on
  landing.

---

## Testing suggestion

Beyond the verification probe above, the test cases in Change 9 cover:

- PreToolUse rewrite shape and quoting.
- Lazy parent-dir creation (run.rs Change 4).
- PostToolUse silent on empty state.
- PostToolUse listing format with and without `desc`.
- PostToolUse BACKGROUNDED supplement, alone and combined with
  captures.
- Subagent namespacing in the parent dir path.
