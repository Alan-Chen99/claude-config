# agent-tools run Process Observability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a wrapped process's status knowable to the agent at every delivery point, so that whether the wrapper was backgrounded is unobservable.

**Architecture:** The wrapper records durable *facts* (spawn, reap, drain) and never a status. A new `status` module derives a status *key* at read time from those facts plus wrapper liveness plus capture-file stat. `hook-post` and a new `hook-prompt` diff that key against a per-scope ledger and report only changes. `ps` renders the same derivation with no ledger.

**Tech Stack:** Rust 2021, tokio, nix, serde/serde_json, chrono, anyhow. Tests are integration tests under `agent-tools/tests/` driving the built binary with a fake `$HOME`, following the existing `hook_post_test.rs` pattern.

**Spec:** `docs/superpowers/specs/2026-08-24-agent-tools-run-observability-design.md`

---

## File Structure

| File | Responsibility | New? |
| --- | --- | --- |
| `agent-tools/src/procstat.rs` | read `/proc/<pid>/stat` start-ticks and state; pid-reuse-safe liveness | create |
| `agent-tools/src/status.rs` | `StatusKey`, quiet buckets, derivation from facts, detail rendering | create |
| `agent-tools/src/ledger.rs` | per-scope last-reported-key map under flock | create |
| `agent-tools/src/hook_prompt.rs` | `UserPromptSubmit` hook subcommand | create |
| `agent-tools/src/meta.rs` | fact record: wrapper identity, spawn error, reap, drain | modify |
| `agent-tools/src/run.rs` | capture dir named by wrapper pid; write facts as learned | modify |
| `agent-tools/src/hook_post.rs` | scan scope, diff keys, report; keep BACKGROUNDED notice | modify |
| `agent-tools/src/ps.rs` | render derived status; drop child-pid liveness | modify |
| `agent-tools/src/main.rs` | register `hook-prompt`; declare new modules | modify |
| `settings.json` | `PostToolUse` matcher `""`; add `UserPromptSubmit` | modify |
| `sys_prompt/alan-default-next.md` | replace the two coupled strings | modify |
| `scripts/check-prompt-coupling.sh` | CI guard the docs already claim exists | create |
| `agent-tools/CLAUDE.md` | coupled-strings table, late-capture section | modify |

Why the split: derivation is pure given `(facts, now, liveness, file stat)` and is the only thing three consumers share, so it gets its own file with table-driven tests. The ledger is the only mutable shared state and is the only place that needs locking, so it is isolated from the reporting logic that uses it.

---

## Task 0: Verify the delivery channels before building on them — COMPLETE (2026-08-24)

> **Result: both channels deliver, and a third is required.** Verified by capturing the
> literal API request bodies, not by grepping transcripts. `PostToolUse` with
> `matcher: ""` delivered for Read, Write, Edit and ToolSearch as well as Bash, including
> in subagent threads. `UserPromptSubmit` delivered on every turn. Task 7 stays in the
> plan.
>
> **Step 3's acceptance criterion below was wrong** and would have produced a false
> negative: the token does not land in the `user` record carrying the tool result. It
> arrives as a separate `role: "system"` message on the wire and as an `attachment`
> record of type `hook_additional_context` in the transcript. In subagent threads no
> attachment record is written at all even though delivery happens, so only wire capture
> is authoritative.
>
> **New requirement discovered:** `PostToolUse` does not fire when a tool result is an
> error; the failure path dispatches `PostToolUseFailure`. Without registering that
> event, every errored tool call is a delivery point with no report — a straight
> violation of the invariant. Registering it was verified to close the hole. Tasks 6 and
> 9 below now cover it.
>
> Do not re-run this task.


The spec's coverage claim depends on `additionalContext` actually reaching the model from a non-Bash tool result and from a user turn. Both are schema-present but delivery is documented only for `Stop`. **If this task fails, stop and narrow the spec's Delivery points section before continuing.**

**Files:**
- Create: `/tmp/at-probe/settings.json` (scratch, not committed)

- [ ] **Step 1: Write the probe settings file**

```bash
mkdir -p /tmp/at-probe
cat > /tmp/at-probe/settings.json <<'JSON'
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "printf '%s' '{\"hookSpecificOutput\":{\"hookEventName\":\"PostToolUse\",\"additionalContext\":\"PROBE_TOKEN_POSTTOOL_9f3a\"}}'",
            "timeout": 5
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "printf '%s' '{\"hookSpecificOutput\":{\"hookEventName\":\"UserPromptSubmit\",\"additionalContext\":\"PROBE_TOKEN_PROMPT_9f3a\"}}'",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
JSON
```

- [ ] **Step 2: Run a headless session that uses a non-Bash tool**

```bash
cd /tmp/at-probe && printf 'hello\n' > target.txt
agent-tools run --desc "channel probe" claude -p 'Use the Grep tool to search for the word hello in /tmp/at-probe/target.txt. Then stop.' --settings /tmp/at-probe/settings.json --permission-mode bypassPermissions
```

- [ ] **Step 3: Check both tokens landed in the session transcript**

```bash
grep -rl "PROBE_TOKEN_POSTTOOL_9f3a" ~/.claude/projects/-tmp-at-probe/ | head -1
grep -rl "PROBE_TOKEN_PROMPT_9f3a" ~/.claude/projects/-tmp-at-probe/ | head -1
```

Expected: both greps print a `.jsonl` path. The token must appear in a record the model received — a `user` role record carrying the tool result (PostToolUse) or the prompt (UserPromptSubmit) — not only in a hook-debug record. Open the file and confirm which record type holds each token.

- [ ] **Step 4: Record the outcome in the spec**

If either channel does not deliver, edit the spec's **Delivery points** table to remove that channel and add one sentence in **Risks** stating what was observed. Commit that edit before any further task. If both deliver, add one line to **Risks** recording the date and the observed record type, and commit.

```bash
git add docs/superpowers/specs/2026-08-24-agent-tools-run-observability-design.md
git commit -m "docs: record delivery-channel verification result"
```

---

## Task 1: procstat — pid-reuse-safe liveness

**Files:**
- Create: `agent-tools/src/procstat.rs`
- Modify: `agent-tools/src/main.rs` (add `mod procstat;`)

- [ ] **Step 1: Write the failing test**

Append to `agent-tools/src/procstat.rs`:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reads_own_start_ticks_and_matches_liveness() {
        let me = std::process::id();
        let ticks = start_ticks(me).expect("own start ticks readable");
        assert!(ticks > 0);
        assert!(is_alive(me, ticks), "self must be alive with its own ticks");
    }

    #[test]
    fn wrong_start_ticks_reads_as_dead() {
        let me = std::process::id();
        let ticks = start_ticks(me).unwrap();
        assert!(
            !is_alive(me, ticks + 1),
            "a recycled pid with different start ticks must read as dead"
        );
    }

    #[test]
    fn comm_containing_spaces_and_parens_parses() {
        // Field 2 is `(comm)` and may itself contain ') ' sequences; parsing
        // must anchor on the LAST ')'.
        let line = "1234 (weird ) name) S 1 1234 1234 0 -1 4194560 100 0 0 0 \
                    1 2 3 4 20 0 1 0 987654 1000 100 0 0 0 0 0 0 0 0 0 0 0 0 0 0";
        assert_eq!(parse_stat(line).unwrap(), (b'S', 987654));
    }

    #[test]
    fn dead_pid_reads_as_dead() {
        // pid 0 never has a /proc entry.
        assert!(!is_alive(0, 1));
    }

    #[test]
    fn a_zombie_is_not_alive() {
        // An exited-but-unreaped child keeps its pid and its start ticks, so
        // ticks alone cannot distinguish it from a live process. It has
        // already released its pipe fds, so it must not count as alive.
        let mut child = std::process::Command::new("true").spawn().unwrap();
        let pid = child.id();
        let ticks = start_ticks(pid).unwrap();
        let deadline = std::time::Instant::now() + std::time::Duration::from_secs(5);
        loop {
            let raw = std::fs::read_to_string(format!("/proc/{pid}/stat")).unwrap();
            if parse_stat(&raw).unwrap().0 == b'Z' {
                break;
            }
            assert!(std::time::Instant::now() < deadline, "child never became a zombie");
            std::thread::sleep(std::time::Duration::from_millis(10));
        }
        assert!(!is_alive(pid, ticks), "a zombie must not count as alive");
        child.wait().unwrap();
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd agent-tools && cargo test --bin agent-tools procstat`
Expected: FAIL — `cannot find function start_ticks`.

- [ ] **Step 3: Write the implementation**

Put above the test module in `agent-tools/src/procstat.rs`:

```rust
use anyhow::{Context, Result};
use std::fs;

/// Parse `/proc/<pid>/stat` into (state, starttime_ticks).
///
/// Field 2 is `comm` wrapped in parentheses and may contain spaces and
/// parentheses, so parsing anchors on the last `)`. In the remainder, index 0
/// is field 3 (state) and index 19 is field 22 (starttime, clock ticks since
/// boot). Verified against /proc/uptime: a freshly started process reports
/// uptime x CLK_TCK.
pub fn parse_stat(line: &str) -> Result<(u8, u64)> {
    let (_, tail) = line.rsplit_once(')').context("no ')' in stat line")?;
    let mut it = tail.split_whitespace();
    let state = it.next().context("stat: no state field")?;
    let starttime = it
        .nth(18)
        .context("stat: line too short for starttime")?
        .parse::<u64>()
        .context("stat: starttime not an integer")?;
    // split_whitespace never yields an empty token, so the first byte exists.
    Ok((state.as_bytes()[0], starttime))
}

pub fn start_ticks(pid: u32) -> Result<u64> {
    let raw = fs::read_to_string(format!("/proc/{pid}/stat"))
        .with_context(|| format!("read /proc/{pid}/stat"))?;
    Ok(parse_stat(&raw)?.1)
}

/// True iff `pid` exists, was started at `expected_ticks`, and is not a zombie.
///
/// The start-ticks comparison rejects a recycled pid. A zombie wrapper has
/// already released its pipe fds, so it must not count as alive.
pub fn is_alive(pid: u32, expected_ticks: u64) -> bool {
    let Ok(raw) = fs::read_to_string(format!("/proc/{pid}/stat")) else {
        return false;
    };
    match parse_stat(&raw) {
        Ok((state, ticks)) => ticks == expected_ticks && state != b'Z',
        Err(_) => false,
    }
}
```

Add `mod procstat;` to `agent-tools/src/main.rs` alongside the existing `mod` lines.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd agent-tools && cargo test --bin agent-tools procstat`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add agent-tools/src/procstat.rs agent-tools/src/main.rs
git commit -m "agent-tools: add procstat for pid-reuse-safe wrapper liveness"
```

---

## Task 2: ChildMeta becomes a fact record, and every consumer keeps compiling

> **Merged with what was Task 3.** `ChildMeta`'s fields are read by `run.rs`,
> `ps.rs`, and `hook_post.rs`. Changing the struct without updating all three
> leaves the crate uncompilable, so Task 2's own tests could not run and the
> TDD loop would be broken from here until Task 8. The struct change, the
> `run.rs` rewrite, and mechanical patches to the other two consumers therefore
> land in one commit. The `ps.rs` and `hook_post.rs` patches here are interim:
> Task 6 deletes the `hook_post.rs` code being patched and Task 8 rewrites the
> `ps.rs` code being patched. Do the minimum to compile — do not improve them.

**Files:**
- Modify: `agent-tools/src/meta.rs:8-15`

- [ ] **Step 1: Write the failing test**

Replace the two existing tests in `agent-tools/src/meta.rs` with:

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    fn sample() -> ChildMeta {
        ChildMeta {
            wrapper_pid: 42,
            wrapper_started_ticks: 987654,
            child_pid: Some(43),
            desc: Some("probe".into()),
            command: vec!["echo".into(), "hi".into()],
            started_at: chrono::Utc::now(),
            spawn_error: None,
            reaped: None,
            drained_at: None,
        }
    }

    #[test]
    fn roundtrip_preserves_facts() {
        let dir = TempDir::new().unwrap();
        write_meta(dir.path(), &sample()).unwrap();
        let back = read_meta(dir.path()).unwrap();
        assert_eq!(back.wrapper_pid, 42);
        assert_eq!(back.wrapper_started_ticks, 987654);
        assert_eq!(back.child_pid, Some(43));
        assert!(back.reaped.is_none());
    }

    #[test]
    fn reap_carries_time_and_status_together() {
        let dir = TempDir::new().unwrap();
        let mut m = sample();
        m.reaped = Some(Reaped { at: chrono::Utc::now(), status: 3 });
        write_meta(dir.path(), &m).unwrap();
        assert_eq!(read_meta(dir.path()).unwrap().reaped.unwrap().status, 3);
    }

    #[test]
    fn spawn_failure_needs_no_child_pid() {
        let dir = TempDir::new().unwrap();
        let mut m = sample();
        m.child_pid = None;
        m.spawn_error = Some("No such file or directory".into());
        write_meta(dir.path(), &m).unwrap();
        assert_eq!(read_meta(dir.path()).unwrap().child_pid, None);
    }

    #[test]
    fn atomic_write_leaves_no_tmp() {
        let dir = TempDir::new().unwrap();
        write_meta(dir.path(), &sample()).unwrap();
        assert!(dir.path().join("meta.json").exists());
        assert!(!dir.path().join("meta.json.tmp").exists());
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd agent-tools && cargo test --bin agent-tools meta`
Expected: FAIL — `struct ChildMeta has no field named wrapper_pid`.

- [ ] **Step 3: Write the implementation**

Replace `agent-tools/src/meta.rs:8-15` with:

```rust
/// Reap facts, written as one unit so time and status can never disagree.
#[derive(Debug, Serialize, Deserialize, Clone, Copy)]
pub struct Reaped {
    pub at: DateTime<Utc>,
    pub status: i32,
}

/// Durable facts about one `agent-tools run` invocation. Never a status:
/// status is derived at read time (see `status.rs`).
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ChildMeta {
    pub wrapper_pid: u32,
    pub wrapper_started_ticks: u64,
    /// None when the command could not be exec'd.
    pub child_pid: Option<u32>,
    pub desc: Option<String>,
    pub command: Vec<String>,
    pub started_at: DateTime<Utc>,
    pub spawn_error: Option<String>,
    pub reaped: Option<Reaped>,
    pub drained_at: Option<DateTime<Utc>>,
}

impl ChildMeta {
    /// Name for reports and `ps`: the `--desc` string, else the command.
    /// A report must never render an empty name.
    pub fn display_name(&self) -> String {
        match &self.desc {
            Some(d) if !d.trim().is_empty() => d.clone(),
            _ => self.command.join(" "),
        }
    }
}
```

`started_at` is no longer `Option`: it is known the moment the directory exists.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd agent-tools && cargo test --bin agent-tools meta`
Expected: 4 passed once Parts 2 and 3 are in place. Until then the crate does not compile.


---

### Part 2: run.rs records facts as it learns them

The load-bearing change: `reaped` is written the instant the child is reaped, **before** joining the tee tasks. Today both fields are written after (`run.rs:137-151`), which is why a detached descendant hides the exit status.

**Files:**
- Modify: `agent-tools/src/run.rs:46-153`
- Test: `agent-tools/tests/run_facts_test.rs` (create)

- [ ] **Step 1: Write the failing test**

Create `agent-tools/tests/run_facts_test.rs`:

```rust
use std::path::PathBuf;
use std::process::Command;

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).parent().unwrap().to_path_buf()
}

/// Read the single capture dir's meta.json, if the wrapper has written it yet.
/// `run` creates the parent dir before the capture dir, so a poll can land in
/// the window where the parent exists and nothing is inside it; that is a
/// "not yet", not a failure.
fn read_meta(parent: &std::path::Path) -> Option<serde_json::Value> {
    let dir = std::fs::read_dir(parent)
        .ok()?
        .flatten()
        .map(|e| e.path())
        .find(|p| p.is_dir())?;
    serde_json::from_slice(&std::fs::read(dir.join("meta.json")).ok()?).ok()
}

/// Kills the wrapper and the detached daemon however the test exits, including
/// on panic. `std::process::Child`'s own Drop does not kill the process, so an
/// assertion failure would otherwise leave both running.
struct Cleanup {
    wrapper: std::process::Child,
    daemon_pid_file: std::path::PathBuf,
}

impl Drop for Cleanup {
    fn drop(&mut self) {
        let _ = self.wrapper.kill();
        let _ = self.wrapper.wait();
        if let Ok(s) = std::fs::read_to_string(&self.daemon_pid_file) {
            if let Ok(pid) = s.trim().parse::<u32>() {
                let _ = std::process::Command::new("kill").arg(pid.to_string()).status();
            }
        }
    }
}

#[test]
fn reap_is_recorded_before_the_pipes_drain() {
    // The child exits immediately but leaves a descendant holding the
    // inherited stdout/stderr, so the wrapper cannot drain. The reap facts
    // must be on disk anyway.
    let home = tempfile::tempdir().unwrap();
    let parent = home.path().join("parent");
    let pid_file = home.path().join("daemon.pid");
    let wrapper = Command::new(bin())
        .args([
            "run", "--desc", "leaky", "bash", "-c",
            &format!("sleep 30 & echo $! > {}; echo done", pid_file.display()),
        ])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("AGENT_TOOLS_PARENT_DIR", &parent)
        .spawn()
        .unwrap();
    let _cleanup = Cleanup { wrapper, daemon_pid_file: pid_file };

    // Poll for the reap facts rather than waiting on the wrapper, which is
    // blocked on the descendant.
    let deadline = std::time::Instant::now() + std::time::Duration::from_secs(10);
    let meta = loop {
        assert!(std::time::Instant::now() < deadline, "reap never recorded");
        std::thread::sleep(std::time::Duration::from_millis(50));
        if let Some(m) = read_meta(&parent) {
            if !m["reaped"].is_null() {
                break m;
            }
        }
    };

    assert_eq!(meta["reaped"]["status"].as_i64(), Some(0));
    assert!(meta["drained_at"].is_null(), "must not claim drained while a writer holds the pipes");
    assert!(meta["wrapper_pid"].as_u64().is_some());
}

#[test]
fn clean_run_records_reap_and_drain() {
    let home = tempfile::tempdir().unwrap();
    let parent = home.path().join("parent");
    let out = Command::new(bin())
        .args(["run", "--desc", "clean", "bash", "-c", "echo hi; exit 7"])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("AGENT_TOOLS_PARENT_DIR", &parent)
        .output()
        .unwrap();
    assert_eq!(out.status.code(), Some(7), "exit code must pass through");
    let meta = read_meta(&parent).expect("meta.json written");
    assert_eq!(meta["reaped"]["status"].as_i64(), Some(7));
    assert!(!meta["drained_at"].is_null());
}

#[test]
fn spawn_failure_is_recorded() {
    let home = tempfile::tempdir().unwrap();
    let parent = home.path().join("parent");
    let out = Command::new(bin())
        .args(["run", "--desc", "nope", "definitely-not-a-real-binary-xyz"])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("AGENT_TOOLS_PARENT_DIR", &parent)
        .output()
        .unwrap();
    assert_ne!(out.status.code(), Some(0));
    let meta = read_meta(&parent).expect("meta.json written");
    assert!(meta["spawn_error"].as_str().is_some());
    assert!(meta["child_pid"].is_null());
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd agent-tools && cargo test --test run_facts_test`
Expected: FAIL — no capture dir exists for the spawn-failure case, and `reaped` is absent while the descendant holds the pipes.

- [ ] **Step 3: Write the implementation**

Rewrite the body of `run()` in `agent-tools/src/run.rs` from the spawn onward:

```rust
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
```

Keep the existing tee/silence/signal setup unchanged, then replace the shutdown sequence (`run.rs:119-151`) with:

```rust
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd agent-tools && cargo test --test run_facts_test`
Expected: 3 passed. `reap_is_recorded_before_the_pipes_drain` is the regression guard for the defect this whole plan exists to fix.


### Part 3: keep `ps.rs` and `hook_post.rs` compiling

- [ ] **Step 1: Patch the nine call sites**

`agent-tools/src/ps.rs`:

```rust
// :57-59  started_at is no longer Option
            .then_with(|| a.meta.started_at.cmp(&b.meta.started_at))
// :61     the capture dir is keyed by wrapper pid now
            .then_with(|| a.meta.wrapper_pid.cmp(&b.meta.wrapper_pid))
// :255
    let live = m.reaped.is_none()
        && m.child_pid.map(|p| is_pid_alive(p as i32)).unwrap_or(false);
// :261
            m.reaped
                .map(|r| r.status.to_string())
                .unwrap_or_else(|| "?".into())
// :266
    writeln!(buf, "    pid {} {}", m.wrapper_pid, status)?;
```

`agent-tools/src/hook_post.rs`:

```rust
// :154
        match m.reaped.map(|r| r.status) {
// :157
                if let Some(end) = m.reaped.map(|r| r.at) {
                    let secs = (end - m.started_at).num_seconds();
// :164   started_at is no longer Option; use it directly
                let secs = (chrono::Utc::now() - m.started_at).num_seconds();
```

- [ ] **Step 2: Confirm the whole crate compiles and every test runs**

Run: `cd agent-tools && cargo test`
Expected: the full suite runs. Pre-existing tests that assert the old
`meta.json` shape will fail — that is expected and they are rewritten in Tasks 6
and 8. Record which ones fail so the later tasks can be checked against the
list. Nothing may fail to *compile*.

- [ ] **Step 3: Commit the whole thing as one change**

```bash
git add agent-tools/src/meta.rs agent-tools/src/run.rs agent-tools/src/ps.rs \
        agent-tools/src/hook_post.rs agent-tools/tests/run_facts_test.rs
git commit -m "agent-tools: ChildMeta records facts, run.rs records reap before drain"
```

---

## Task 4: status derivation

**Files:**
- Create: `agent-tools/src/status.rs`
- Modify: `agent-tools/src/main.rs` (add `mod status;`)

- [ ] **Step 1: Write the failing test**

Append to `agent-tools/src/status.rs`:

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use crate::meta::{ChildMeta, Reaped};
    use chrono::{Duration, Utc};
    use tempfile::TempDir;

    fn base() -> ChildMeta {
        ChildMeta {
            wrapper_pid: std::process::id(),
            wrapper_started_ticks: crate::procstat::start_ticks(std::process::id()).unwrap(),
            child_pid: Some(999_999),
            desc: Some("t".into()),
            command: vec!["true".into()],
            started_at: Utc::now(),
            spawn_error: None,
            reaped: None,
            drained_at: None,
        }
    }

    fn dead() -> ChildMeta {
        // pid 0 has no /proc entry, so liveness is false.
        ChildMeta { wrapper_pid: 0, wrapper_started_ticks: 1, ..base() }
    }

    fn write(dir: &TempDir, m: &ChildMeta) {
        crate::meta::write_meta(dir.path(), m).unwrap();
    }

    #[test]
    fn spawn_failure_wins_over_everything() {
        let d = TempDir::new().unwrap();
        let mut m = base();
        m.spawn_error = Some("boom".into());
        m.reaped = Some(Reaped { at: Utc::now(), status: 0 });
        write(&d, &m);
        assert!(matches!(derive(d.path(), Utc::now()).key, StatusKey::SpawnFailed(_)));
    }

    #[test]
    fn drained_is_final() {
        let d = TempDir::new().unwrap();
        let mut m = base();
        m.reaped = Some(Reaped { at: Utc::now(), status: 3 });
        m.drained_at = Some(Utc::now());
        write(&d, &m);
        assert_eq!(derive(d.path(), Utc::now()).key, StatusKey::Final(3));
    }

    #[test]
    fn reaped_with_live_wrapper_is_exited() {
        let d = TempDir::new().unwrap();
        let mut m = base();
        m.reaped = Some(Reaped { at: Utc::now(), status: 0 });
        write(&d, &m);
        assert_eq!(derive(d.path(), Utc::now()).key, StatusKey::Exited(0));
    }

    #[test]
    fn reaped_with_dead_wrapper_is_final() {
        let d = TempDir::new().unwrap();
        let mut m = dead();
        m.reaped = Some(Reaped { at: Utc::now(), status: 5 });
        write(&d, &m);
        assert_eq!(derive(d.path(), Utc::now()).key, StatusKey::Final(5));
    }

    #[test]
    fn unreaped_with_dead_wrapper_is_abandoned() {
        let d = TempDir::new().unwrap();
        write(&d, &dead());
        assert_eq!(derive(d.path(), Utc::now()).key, StatusKey::Abandoned);
    }

    #[test]
    fn unreadable_meta_is_abandoned() {
        let d = TempDir::new().unwrap();
        assert_eq!(derive(d.path(), Utc::now()).key, StatusKey::Abandoned);
    }

    #[test]
    fn recent_output_is_producing() {
        let d = TempDir::new().unwrap();
        write(&d, &base());
        std::fs::write(d.path().join("stdout"), b"hi").unwrap();
        assert_eq!(derive(d.path(), Utc::now()).key, StatusKey::Producing);
    }

    #[test]
    fn quiet_picks_the_largest_crossed_bucket() {
        let d = TempDir::new().unwrap();
        let mut m = base();
        m.started_at = Utc::now() - Duration::seconds(4000);
        write(&d, &m);
        // No capture files at all: measured from started_at, 4000s ago.
        assert_eq!(derive(d.path(), Utc::now()).key, StatusKey::Quiet("30m"));
    }

    #[test]
    fn bucket_boundaries_are_inclusive() {
        // An anchor exactly on a boundary is quiet, never producing.
        let d = TempDir::new().unwrap();
        let mut m = base();
        m.started_at = Utc::now() - Duration::seconds(30);
        write(&d, &m);
        assert_eq!(derive(d.path(), Utc::now()).key, StatusKey::Quiet("30s"));
    }

    #[test]
    fn drained_without_a_reap_never_invents_a_status() {
        let d = TempDir::new().unwrap();
        let mut m = dead();
        m.drained_at = Some(Utc::now());
        m.reaped = None;
        write(&d, &m);
        assert_eq!(derive(d.path(), Utc::now()).key, StatusKey::Abandoned);
    }

    #[test]
    fn render_says_no_output_when_nothing_was_written() {
        // The capture file exists from the moment the tee opens it, so its mtime
        // predates any byte. A line claiming a "last byte" next to out=0B is a
        // contradiction the reader has to resolve.
        let d = TempDir::new().unwrap();
        write(&d, &base());
        std::fs::write(d.path().join("stdout"), b"").unwrap();
        let now = Utc::now();
        let line = render(d.path(), &derive(d.path(), now), now);
        assert!(line.contains("no output"), "line: {line}");
        assert!(!line.contains("last byte"), "line: {line}");
    }

    #[test]
    fn render_names_the_child_its_key_and_its_bytes() {
        let d = TempDir::new().unwrap();
        write(&d, &base());
        std::fs::write(d.path().join("stdout"), b"hello").unwrap();
        let now = Utc::now();
        let line = render(d.path(), &derive(d.path(), now), now);
        assert!(line.contains("[producing]"), "line: {line}");
        assert!(line.contains("out=5B"), "line: {line}");
        assert!(line.contains("last byte"), "line: {line}");
    }

    #[test]
    fn a_stat_failure_is_reported_not_read_as_no_output() {
        // A path component that is a regular file yields ENOTDIR, which is not
        // NotFound and must not be collapsed into "this child wrote nothing".
        let d = TempDir::new().unwrap();
        let not_a_dir = d.path().join("regular_file");
        std::fs::write(&not_a_dir, b"x").unwrap();
        let now = Utc::now();
        let s = derive(&not_a_dir, now);
        assert!(!s.stat_errors.is_empty(), "a non-NotFound stat error must survive");
        assert!(render(&not_a_dir, &s, now).contains("stat failed"));
    }

    #[test]
    fn key_strings_are_stable_ledger_identities() {
        assert_eq!(StatusKey::Producing.to_string(), "producing");
        assert_eq!(StatusKey::Quiet("5m").to_string(), "quiet(5m)");
        assert_eq!(StatusKey::Exited(2).to_string(), "exited(2)");
        assert_eq!(StatusKey::Final(0).to_string(), "final(0)");
        assert_eq!(StatusKey::Abandoned.to_string(), "abandoned");
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd agent-tools && cargo test --bin agent-tools status`
Expected: FAIL — `cannot find function derive`.

- [ ] **Step 3: Write the implementation**

Put above the test module in `agent-tools/src/status.rs`:

```rust
use chrono::{DateTime, Utc};
use std::fmt;
use std::path::Path;

use crate::meta::{self, ChildMeta};
use crate::procstat;

/// Quiet thresholds, ascending. Configuration, not contract.
pub const QUIET_BUCKETS: &[(i64, &str)] = &[(30, "30s"), (300, "5m"), (1800, "30m"), (7200, "2h")];

/// A child's status. The rendered form is both the ledger identity that decides
/// whether something is reported twice and text quoted in the system prompt.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum StatusKey {
    SpawnFailed(String),
    Producing,
    Quiet(&'static str),
    Exited(i32),
    Final(i32),
    Abandoned,
}

impl fmt::Display for StatusKey {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            StatusKey::SpawnFailed(e) => write!(f, "spawn-failed({e})"),
            StatusKey::Producing => write!(f, "producing"),
            StatusKey::Quiet(b) => write!(f, "quiet({b})"),
            StatusKey::Exited(c) => write!(f, "exited({c})"),
            StatusKey::Final(c) => write!(f, "final({c})"),
            StatusKey::Abandoned => write!(f, "abandoned"),
        }
    }
}

/// A child's current status: the key that decides reporting, plus the detail
/// rendered alongside it.
pub struct Status {
    pub key: StatusKey,
    pub meta: Option<ChildMeta>,
    pub last_byte_at: Option<DateTime<Utc>>,
    pub out_bytes: u64,
    pub err_bytes: u64,
    /// Stat failures that are not "file not created yet". Surfaced in the
    /// rendered line so a filesystem problem cannot pass for an idle child.
    pub stat_errors: Vec<String>,
}

/// Returns (bytes, mtime, stat failure other than "not created yet").
///
/// A missing capture file is ordinary: the parent directory exists before the
/// tee opens either stream. Any other stat failure is a real filesystem problem,
/// and reading it as "no output" would understate a child that is in fact busy.
fn file_facts(dir: &Path, name: &str) -> (u64, Option<DateTime<Utc>>, Option<String>) {
    match std::fs::metadata(dir.join(name)) {
        Ok(md) => (md.len(), md.modified().ok().map(DateTime::<Utc>::from), None),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => (0, None, None),
        Err(e) => (0, None, Some(format!("{name}: {e}"))),
    }
}

fn largest_bucket(age_secs: i64) -> Option<&'static str> {
    QUIET_BUCKETS
        .iter()
        .rev()
        .find(|(secs, _)| age_secs >= *secs)
        .map(|(_, label)| *label)
}

/// Derive the current status of one capture directory. Total: every input
/// combination yields exactly one key. Rows are evaluated in order.
pub fn derive(dir: &Path, now: DateTime<Utc>) -> Status {
    let (out_bytes, out_mtime, out_err) = file_facts(dir, "stdout");
    let (err_bytes, err_mtime, err_err) = file_facts(dir, "stderr");
    let last_byte_at = out_mtime.max(err_mtime);
    let stat_errors: Vec<String> = [out_err, err_err].into_iter().flatten().collect();

    let Ok(m) = meta::read_meta(dir) else {
        // A capture that cannot be described is never silently dropped.
        return Status {
            key: StatusKey::Abandoned,
            meta: None,
            last_byte_at,
            out_bytes,
            err_bytes,
            stat_errors,
        };
    };

    let key = if let Some(e) = m.spawn_error.clone() {
        StatusKey::SpawnFailed(e)
    } else {
        let alive = procstat::is_alive(m.wrapper_pid, m.wrapper_started_ticks);
        match (m.drained_at.is_some(), m.reaped, alive) {
            (true, Some(r), _) => StatusKey::Final(r.status),
            (_, Some(r), true) => StatusKey::Exited(r.status),
            (_, Some(r), false) => StatusKey::Final(r.status),
            // Drained without a reap cannot be produced by run.rs; treat the
            // corrupt record the same as a wrapper that vanished.
            (_, None, false) => StatusKey::Abandoned,
            (_, None, true) => {
                let anchor = last_byte_at.unwrap_or(m.started_at);
                let age = (now - anchor).num_seconds().max(0);
                match largest_bucket(age) {
                    Some(b) => StatusKey::Quiet(b),
                    None => StatusKey::Producing,
                }
            }
        }
    };

    Status { key, meta: Some(m), last_byte_at, out_bytes, err_bytes, stat_errors }
}

/// One rendered line: name, key, detail, capture paths.
pub fn render(dir: &Path, s: &Status, now: DateTime<Utc>) -> String {
    let name = s.meta.as_ref().map(|m| m.display_name()).unwrap_or_else(|| dir.display().to_string());
    // The capture files are created when the tee opens them, so an mtime exists
    // before any byte does. Byte counts, not mtime, decide whether output happened.
    let age = match s.last_byte_at {
        Some(t) if s.out_bytes + s.err_bytes > 0 => {
            format!("last byte {}s ago", (now - t).num_seconds().max(0))
        }
        _ => "no output".to_string(),
    };
    let problems = if s.stat_errors.is_empty() {
        String::new()
    } else {
        format!(" [stat failed: {}]", s.stat_errors.join("; "))
    };
    let pid = s
        .meta
        .as_ref()
        .and_then(|m| m.child_pid)
        .map(|p| p.to_string())
        .unwrap_or_else(|| "-".into());
    format!(
        "{name} [{}] pid {pid}, {age}, out={}B err={}B{problems} -> {}/{{stdout,stderr}}",
        s.key,
        s.out_bytes,
        s.err_bytes,
        dir.display()
    )
}
```

Add `mod status;` to `agent-tools/src/main.rs`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd agent-tools && cargo test --bin agent-tools status`
Expected: 14 passed (plus one incidental `meta::` match on the `status` filter).

- [ ] **Step 5: Commit**

```bash
git add agent-tools/src/status.rs agent-tools/src/main.rs
git commit -m "agent-tools: derive child status from facts at read time"
```

---

## Task 5: the report ledger

**Files:**
- Create: `agent-tools/src/ledger.rs`
- Modify: `agent-tools/src/main.rs` (add `mod ledger;`)

- [ ] **Step 1: Write the failing test**

Append to `agent-tools/src/ledger.rs`:

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn first_sight_of_a_key_is_a_change() {
        let scope = TempDir::new().unwrap();
        let mut l = Ledger::open(scope.path()).unwrap();
        assert!(l.changed("toolu_a/12", "producing"));
        l.record("toolu_a/12", "producing");
        l.commit().unwrap();
    }

    #[test]
    fn same_key_twice_is_not_a_change() {
        let scope = TempDir::new().unwrap();
        {
            let mut l = Ledger::open(scope.path()).unwrap();
            l.record("toolu_a/12", "producing");
            l.commit().unwrap();
        }
        let l = Ledger::open(scope.path()).unwrap();
        assert!(!l.changed("toolu_a/12", "producing"));
    }

    #[test]
    fn a_new_key_for_a_known_child_is_a_change() {
        let scope = TempDir::new().unwrap();
        {
            let mut l = Ledger::open(scope.path()).unwrap();
            l.record("toolu_a/12", "exited(0)");
            l.commit().unwrap();
        }
        let l = Ledger::open(scope.path()).unwrap();
        assert!(l.changed("toolu_a/12", "final(0)"));
    }

    #[test]
    fn children_are_tracked_independently() {
        let scope = TempDir::new().unwrap();
        let mut l = Ledger::open(scope.path()).unwrap();
        assert!(l.changed("toolu_a/12", "producing"));
        l.record("toolu_a/12", "producing");
        assert!(l.changed("toolu_b/99", "producing"));
    }

    #[test]
    fn a_second_open_in_this_process_fails_fast_instead_of_hanging() {
        let scope = TempDir::new().unwrap();
        let _first = Ledger::open(scope.path()).unwrap();
        let err = Ledger::open(scope.path()).unwrap_err().to_string();
        assert!(err.contains("already open in this process"), "err: {err}");
    }

    #[test]
    fn a_corrupt_ledger_announces_itself_rather_than_resetting_quietly() {
        let scope = TempDir::new().unwrap();
        {
            let mut l = Ledger::open(scope.path()).unwrap();
            l.record("toolu_a/12", "producing");
            l.commit().unwrap();
        }
        std::fs::write(scope.path().join(".reported.json"), b"{not json").unwrap();
        let l = Ledger::open(scope.path()).unwrap();
        assert!(l.reset_reason.is_some(), "a corrupt ledger must say so");
        assert!(
            l.changed("toolu_a/12", "producing"),
            "the record really is gone, so the child reports again"
        );
    }

    #[test]
    fn a_key_that_was_never_recorded_stays_pending() {
        // A caller that drops a line for size must not have it counted as told,
        // or that child's change is lost from the push channel permanently.
        let scope = TempDir::new().unwrap();
        {
            let l = Ledger::open(scope.path()).unwrap();
            assert!(l.changed("toolu_a/12", "producing"));
            l.commit().unwrap();
        }
        let l = Ledger::open(scope.path()).unwrap();
        assert!(
            l.changed("toolu_a/12", "producing"),
            "an unreported key must not count as told"
        );
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd agent-tools && cargo test --bin agent-tools ledger`
Expected: FAIL — `cannot find type Ledger`.

- [ ] **Step 3: Write the implementation**

Put above the test module in `agent-tools/src/ledger.rs`:

```rust
use anyhow::{bail, Context, Result};
use nix::fcntl::{Flock, FlockArg};
use std::collections::{BTreeMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::{Mutex, OnceLock};

/// Scopes with a live `Ledger` in this process.
///
/// `flock` keys off the open file description, not the process, so a second
/// `open` on a scope this process already holds blocks forever waiting on its
/// own lock — with no diagnostic, and nothing able to release it. The set turns
/// that hang into an error.
fn open_scopes() -> &'static Mutex<HashSet<PathBuf>> {
    static SCOPES: OnceLock<Mutex<HashSet<PathBuf>>> = OnceLock::new();
    SCOPES.get_or_init(|| Mutex::new(HashSet::new()))
}

/// The stored map, plus the reason it could not be read.
///
/// A missing file is ordinary: nothing has been reported in this scope yet.
/// Anything else means the record of what the agent was already told is gone.
/// The agent has to hear about that, because the consequence is every child
/// being reported to it a second time.
fn load(path: &Path) -> (BTreeMap<String, String>, Option<String>) {
    let bytes = match fs::read(path) {
        Ok(b) => b,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => return (BTreeMap::new(), None),
        Err(e) => {
            return (
                BTreeMap::new(),
                Some(format!("{} could not be read ({e})", path.display())),
            )
        }
    };
    match serde_json::from_slice(&bytes) {
        Ok(m) => (m, None),
        Err(e) => (
            BTreeMap::new(),
            Some(format!("{} is unreadable ({e})", path.display())),
        ),
    }
}

/// Per-scope map of child identity -> last reported status key.
///
/// Child identity is the capture directory's path relative to the scope:
/// `<tool_use_id>/<wrapper_pid>`. The exclusive flock is held for the lifetime
/// of the value, so a scan-and-report cycle is atomic against parallel hooks.
pub struct Ledger {
    scope: PathBuf,
    path: PathBuf,
    map: BTreeMap<String, String>,
    /// Set when the stored ledger could not be read. Everything in this scope
    /// will look new, so the report says why rather than letting the agent see
    /// unexplained repeats.
    pub reset_reason: Option<String>,
    _lock: Flock<fs::File>,
}

impl Drop for Ledger {
    fn drop(&mut self) {
        open_scopes().lock().unwrap().remove(&self.scope);
    }
}

impl Ledger {
    pub fn open(scope: &Path) -> Result<Self> {
        fs::create_dir_all(scope)
            .with_context(|| format!("create scope dir {}", scope.display()))?;
        let scope = fs::canonicalize(scope)
            .with_context(|| format!("canonicalize {}", scope.display()))?;
        if !open_scopes().lock().unwrap().insert(scope.clone()) {
            bail!(
                "a Ledger for {} is already open in this process; a second one would \
                 block forever waiting on this process's own flock",
                scope.display()
            );
        }
        match Self::acquire(scope.clone()) {
            Ok(l) => Ok(l),
            Err(e) => {
                open_scopes().lock().unwrap().remove(&scope);
                Err(e)
            }
        }
    }

    fn acquire(scope: PathBuf) -> Result<Self> {
        let lock_path = scope.join(".reported.lock");
        let file = fs::OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .truncate(false)
            .open(&lock_path)
            .with_context(|| format!("open lock {}", lock_path.display()))?;
        let lock = Flock::lock(file, FlockArg::LockExclusive)
            .map_err(|(_, e)| anyhow::anyhow!("flock {}: {e}", lock_path.display()))?;
        let path = scope.join(".reported.json");
        let (map, reset_reason) = load(&path);
        Ok(Ledger { scope, path, map, reset_reason, _lock: lock })
    }

    /// True when `key` differs from the last key reported for `id`.
    ///
    /// A pure query. Nothing is recorded until `record` is called, so a line the
    /// caller ends up dropping stays pending rather than being marked as told.
    pub fn changed(&self, id: &str, key: &str) -> bool {
        self.map.get(id).map(|prev| prev != key).unwrap_or(true)
    }

    /// Record `key` as the last key reported for `id`. Call this only for lines
    /// that actually reach the agent.
    pub fn record(&mut self, id: &str, key: &str) {
        self.map.insert(id.to_string(), key.to_string());
    }

    /// Takes `&mut self` so two threads sharing one open `Ledger` cannot race
    /// the fixed temp filename. The flock excludes other processes; it does
    /// nothing to serialize callers already holding this file description.
    pub fn commit(&mut self) -> Result<()> {
        let tmp = self.path.with_extension("json.tmp");
        fs::write(&tmp, serde_json::to_vec_pretty(&self.map)?)
            .with_context(|| format!("write {}", tmp.display()))?;
        fs::rename(&tmp, &self.path)
            .with_context(|| format!("rename into {}", self.path.display()))?;
        Ok(())
    }
}
```

Add `mod ledger;` to `agent-tools/src/main.rs`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd agent-tools && cargo test --bin agent-tools ledger`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add agent-tools/src/ledger.rs agent-tools/src/main.rs
git commit -m "agent-tools: per-scope ledger of last reported status key"
```

---

## Task 6: hook-post reports status changes

**Files:**
- Modify: `agent-tools/src/hook_post.rs` (replace capture listing and late-capture scan; keep the BACKGROUNDED notice; delete `UNFINALIZED_STALE_SECS`)
- Test: `agent-tools/tests/hook_post_test.rs` (replace the capture/late-capture tests; keep the backgrounding-cause tests)

- [ ] **Step 1: Write the failing test**

Add to `agent-tools/tests/hook_post_test.rs`, reusing its existing `run_post` and `parent_dir` helpers:

```rust
/// Write a capture dir with the given facts and return its identity string.
fn seed(home: &std::path::Path, tuid: &str, wrapper_pid: u32, reaped: Option<i32>) -> String {
    let parent = parent_dir(home, "sid", None, tuid);
    let dir = parent.join(wrapper_pid.to_string());
    std::fs::create_dir_all(&dir).unwrap();
    let reaped_json = match reaped {
        Some(s) => format!(r#"{{"at":"{}","status":{s}}}"#, chrono::Utc::now().to_rfc3339()),
        None => "null".to_string(),
    };
    let meta = format!(
        r#"{{"wrapper_pid":{wrapper_pid},"wrapper_started_ticks":1,"child_pid":4242,
            "desc":"seeded","command":["true"],"started_at":"{}",
            "spawn_error":null,"reaped":{reaped_json},"drained_at":null}}"#,
        chrono::Utc::now().to_rfc3339()
    );
    std::fs::write(dir.join("meta.json"), meta).unwrap();
    format!("{tuid}/{wrapper_pid}")
}

fn post_body(tool: &str, tuid: &str) -> serde_json::Value {
    serde_json::json!({
        "session_id": "sid",
        "tool_name": tool,
        "tool_input": {},
        "tool_use_id": tuid,
        "tool_response": {}
    })
}

#[test]
fn abandoned_child_is_reported_without_any_five_minute_wait() {
    // wrapper_pid 0 has no /proc entry, so the wrapper is dead. The child was
    // seeded seconds ago; the old implementation would have waited 300s.
    let home = tempfile::tempdir().unwrap();
    seed(home.path(), "toolu_prior", 0, None);
    let (_, stdout, _) = run_post(home.path(), post_body("Grep", "toolu_now"));
    assert!(stdout.contains("[agent-tools] run status:"), "stdout: {stdout}");
    assert!(stdout.contains("abandoned"), "stdout: {stdout}");
}

#[test]
fn the_same_key_is_never_reported_twice() {
    let home = tempfile::tempdir().unwrap();
    seed(home.path(), "toolu_prior", 0, None);
    let (_, first, _) = run_post(home.path(), post_body("Grep", "toolu_a"));
    assert!(first.contains("abandoned"));
    let (_, second, _) = run_post(home.path(), post_body("Grep", "toolu_b"));
    assert!(!second.contains("abandoned"), "second report was redundant: {second}");
}

#[test]
fn a_new_key_for_a_known_child_is_reported_again() {
    let home = tempfile::tempdir().unwrap();
    seed(home.path(), "toolu_prior", 0, Some(0));
    let (_, first, _) = run_post(home.path(), post_body("Grep", "toolu_a"));
    assert!(first.contains("final(0)"), "stdout: {first}");
    // Same child, now unreadable meta -> abandoned, a different key.
    std::fs::remove_file(
        parent_dir(home.path(), "sid", None, "toolu_prior").join("0").join("meta.json"),
    )
    .unwrap();
    let (_, second, _) = run_post(home.path(), post_body("Grep", "toolu_b"));
    assert!(second.contains("abandoned"), "stdout: {second}");
}

#[test]
fn a_subagents_children_are_not_reported_to_the_main_thread() {
    let home = tempfile::tempdir().unwrap();
    let parent = parent_dir(home.path(), "sid", Some("agent-1"), "toolu_sub");
    let dir = parent.join("7");
    std::fs::create_dir_all(&dir).unwrap();
    std::fs::write(
        dir.join("meta.json"),
        format!(
            r#"{{"wrapper_pid":0,"wrapper_started_ticks":1,"child_pid":1,"desc":"subagent child",
                "command":["true"],"started_at":"{}","spawn_error":null,"reaped":null,"drained_at":null}}"#,
            chrono::Utc::now().to_rfc3339()
        ),
    )
    .unwrap();
    let (_, stdout, _) = run_post(home.path(), post_body("Grep", "toolu_main"));
    assert!(!stdout.contains("subagent child"), "scope leak: {stdout}");
}

#[test]
fn a_failed_status_report_does_not_discard_the_backgrounded_notice() {
    // A directory where the lock file belongs makes Ledger::open fail. The
    // notice is computed from the tool response and owes nothing to the ledger,
    // so it must survive — and the failure must be visible, not swallowed.
    let home = tempfile::tempdir().unwrap();
    seed(home.path(), "toolu_prior", 0, None);
    let scope = home.path().join(".claude/agent-tools/sid");
    std::fs::create_dir_all(scope.join(".reported.lock")).unwrap();

    let (_, stdout, _) = run_post(
        home.path(),
        serde_json::json!({
            "session_id": "sid",
            "tool_name": "Bash",
            "tool_input": {"command": "x", "run_in_background": true},
            "tool_use_id": "toolu_now",
            "tool_response": {"backgroundTaskId": "bg_1"}
        }),
    );
    assert!(stdout.contains("BACKGROUNDED:"), "notice was lost: {stdout}");
    assert!(
        stdout.contains("run status: unavailable"),
        "the reporting failure was swallowed: {stdout}"
    );
}

/// This process's own start ticks, so a fixture can name a wrapper that is
/// genuinely alive. `seed`'s hardcoded ticks never match a real process, which
/// is why every other fixture derives `abandoned`.
fn own_start_ticks() -> u64 {
    let raw = std::fs::read_to_string("/proc/self/stat").unwrap();
    let tail = raw.rsplit_once(')').unwrap().1;
    tail.split_whitespace().nth(19).unwrap().parse().unwrap()
}

/// Seed a child whose wrapper is this live test process, so it derives
/// `producing` rather than `abandoned`.
fn seed_live(home: &std::path::Path, tuid: &str) -> String {
    let pid = std::process::id();
    let parent = parent_dir(home, "sid", None, tuid);
    let dir = parent.join(pid.to_string());
    std::fs::create_dir_all(&dir).unwrap();
    let meta = format!(
        r#"{{"wrapper_pid":{pid},"wrapper_started_ticks":{},"child_pid":4242,
            "desc":"live child","command":["true"],"started_at":"{}",
            "spawn_error":null,"reaped":null,"drained_at":null}}"#,
        own_start_ticks(),
        chrono::Utc::now().to_rfc3339()
    );
    std::fs::write(dir.join("meta.json"), meta).unwrap();
    format!("{tuid}/{pid}")
}

#[test]
fn a_still_running_child_is_reported_after_finished_ones() {
    // Identity order alone would put the running child first. Only `rank`
    // overrides that, so an inverted or absent rank fails this test.
    let home = tempfile::tempdir().unwrap();
    seed(home.path(), "toolu_zzz_done", 7, Some(0));
    seed_live(home.path(), "toolu_aaa_running");

    let (_, stdout, _) = run_post(home.path(), post_body("Grep", "toolu_now"));
    let done = stdout.find("toolu_zzz_done").expect("finished child reported");
    let running = stdout.find("toolu_aaa_running").expect("running child reported");
    assert!(
        done < running,
        "a finished child must reach the agent before a still-running one: {stdout}"
    );
}

#[test]
fn report_order_is_reproducible_rather_than_filesystem_order() {
    // Seeded in reverse so creation order cannot be mistaken for sorted order.
    let home = tempfile::tempdir().unwrap();
    for i in (1..=5u32).rev() {
        seed(home.path(), &format!("toolu_{i}"), i, None);
    }
    let (_, stdout, _) = run_post(home.path(), post_body("Grep", "toolu_now"));
    let order: Vec<usize> = (1..=5u32)
        .map(|i| stdout.find(&format!("toolu_{i}/{i}")).expect("every child reported"))
        .collect();
    let mut sorted = order.clone();
    sorted.sort_unstable();
    assert_eq!(order, sorted, "children must appear in identity order: {stdout}");
}

#[test]
fn parallel_hooks_report_each_child_exactly_once() {
    // The reason this uses a lock file at all is that concurrent tool calls must
    // not both report the same change, nor lose one another's ledger writes.
    // Only real processes exercise an flock; threads in one process cannot.
    let home = tempfile::tempdir().unwrap();
    for i in 1..=8u32 {
        seed(home.path(), &format!("toolu_prior_{i}"), i, None);
    }

    let mut kids = Vec::new();
    for i in 0..8 {
        let mut c = Command::new(bin())
            .arg("hook-post")
            .env("HOME", home.path())
            .env("CLAUDE_CONFIG_ROOT", worktree_root())
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .spawn()
            .unwrap();
        // Close stdin immediately so all eight run at once rather than each
        // waiting for the collect loop to reach it.
        let mut si = c.stdin.take().unwrap();
        si.write_all(post_body("Grep", &format!("toolu_call_{i}")).to_string().as_bytes())
            .unwrap();
        drop(si);
        kids.push(c);
    }

    let combined = kids
        .into_iter()
        .map(|c| String::from_utf8_lossy(&c.wait_with_output().unwrap().stdout).into_owned())
        .collect::<Vec<_>>()
        .join("\n");

    for i in 1..=8u32 {
        let needle = format!("toolu_prior_{i}/{i}");
        assert_eq!(
            combined.matches(&needle).count(),
            1,
            "child {needle} must be reported exactly once across all hooks; combined:\n{combined}"
        );
    }
}
```

Delete the tests that assert the removed strings: `stale_in_flight_child_surfaces_with_unfinalized_annotation` and every test asserting `"captures from this Bash call"` or `"Late captures from prior backgrounded call"`. Keep every test asserting `BACKGROUNDED:` behavior unchanged.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd agent-tools && cargo test --test hook_post_test`
Expected: FAIL — output still contains the old capture-listing strings and no `run status:` header.

- [ ] **Step 3: Write the implementation**

In `agent-tools/src/hook_post.rs`: delete `UNFINALIZED_STALE_SECS`, `LATE_CAPTURES_HEADER_PREFIX`, `list_captures`, `format_capture`, `format_details`, and `update_ledger_and_scan`. Keep the backgrounding-cause detection and its notice verbatim. Replace the report path with:

```rust
/// Scan every capture dir in this agent's scope, derive each status, and
/// return one line per child whose key changed since it was last reported.
fn report_changes(session_id: &str, agent_id: Option<&str>) -> Result<Vec<String>> {
    let scope = scope_dir(session_id, agent_id)?;
    if !scope.is_dir() {
        return Ok(Vec::new());
    }
    let now = chrono::Utc::now();
    let mut ledger = crate::ledger::Ledger::open(&scope)?;
    let mut pending: Vec<(String, String, String)> = Vec::new();
    let mut notes: Vec<String> = Vec::new();

    for tuid_entry in fs::read_dir(&scope)?.flatten() {
        let tuid_dir = tuid_entry.path();
        if !tuid_dir.is_dir() {
            continue;
        }
        let Some(tuid) = tuid_dir.file_name().and_then(|n| n.to_str()) else {
            continue;
        };
        let Ok(cap_entries) = fs::read_dir(&tuid_dir) else {
            // The surrounding scan skips what it cannot use; aborting the whole
            // report over one directory would hide every other child's change.
            notes.push(format!(
                "  note: {} could not be listed; its captures are missing from this report",
                tuid_dir.display()
            ));
            continue;
        };
        for cap_entry in cap_entries.flatten() {
            let cap_dir = cap_entry.path();
            let Some(name) = cap_dir.file_name().and_then(|n| n.to_str()) else {
                continue;
            };
            if !cap_dir.is_dir() || name.parse::<u32>().is_err() {
                continue;
            }
            let st = crate::status::derive(&cap_dir, now);
            let id = format!("{tuid}/{name}");
            let key = st.key.to_string();
            if ledger.changed(&id, &key) {
                pending.push((id, key, format!("  {}", crate::status::render(&cap_dir, &st, now))));
            }
        }
    }
    // Terminal keys first when the budget forces a choice: "this finished" matters
    // more to an agent than "this is still running". Identity breaks ties, so a
    // report is reproducible instead of in whatever order read_dir happened to
    // yield — which would also make the dropped set arbitrary.
    pending.sort_by(|a, b| rank(&a.1).cmp(&rank(&b.1)).then_with(|| a.0.cmp(&b.0)));
    let mut lines = bound(&mut ledger, pending);
    // A reset ledger makes every child look new. Say why, or the agent sees a
    // burst of repeats with no explanation.
    if let Some(reason) = ledger.reset_reason.clone() {
        notes.insert(
            0,
            format!("  note: report history lost — {reason}; each child below is reported again once"),
        );
    }
    for note in notes.into_iter().rev() {
        lines.insert(0, note);
    }
    ledger.commit()?;
    Ok(lines)
}
```

and in `run()`, after the backgrounding notice is pushed:

```rust
    // The backgrounding notice is independent of status reporting and is the one
    // message this hook must not lose. A `?` here would discard an
    // already-computed notice because something unrelated failed.
    match report_changes(&input.session_id, input.agent_id.as_deref()) {
        Ok(changes) if !changes.is_empty() => {
            parts.push(format!("[agent-tools] run status:\n{}", changes.join("\n")));
        }
        Ok(_) => {}
        Err(e) => {
            eprintln!("agent-tools hook-post: status report failed: {e:#}");
            parts.push(format!(
                "[agent-tools] run status: unavailable this time ({e}); \
                 run `agent-tools ps` for the current state"
            ));
        }
    }
```

with the size bound, because `additionalContext` is capped at 10,000 characters and the
runtime silently replaces anything longer with a 2,000-character stub — which would read
as "nothing else changed":

```rust
/// Keep the report lines that fit under the additionalContext cap, and record in
/// the ledger only the ones actually kept.
///
/// Recording a line the agent never saw would retire that child's change
/// permanently: its key would match next time and never be reported again. A
/// dropped line stays pending instead, and lands at the next delivery point.
/// The count of dropped lines is stated, because a silently truncated report is
/// indistinguishable from a report of no change.
const REPORT_BUDGET: usize = 9_000;

/// Ordering weight: 0 for keys that say a child is done, 1 for keys that say it
/// is still going.
fn rank(key: &str) -> u8 {
    if key.starts_with("producing") || key.starts_with("quiet(") {
        1
    } else {
        0
    }
}

fn bound(
    ledger: &mut crate::ledger::Ledger,
    pending: Vec<(String, String, String)>,
) -> Vec<String> {
    let mut used = 0;
    let mut kept: Vec<String> = Vec::new();
    let mut dropped = 0;
    for (id, key, line) in pending {
        // `continue`, not `break`: a short line after a long one still fits.
        if used + line.len() + 1 > REPORT_BUDGET {
            dropped += 1;
            continue;
        }
        used += line.len() + 1;
        ledger.record(&id, &key);
        kept.push(line);
    }
    if dropped > 0 {
        kept.push(format!(
            "  ... {dropped} more changed, omitted for size; they are reported at the \
             next delivery point, or run `agent-tools ps` now"
        ));
    }
    kept
}
```

**Echo the incoming event name.** The same binary now answers both `PostToolUse` and
`PostToolUseFailure`, and the response must name the event it is answering.
`PostToolUseInput` does not currently capture it. In `agent-tools/src/hook_input.rs`, add
to `PostToolUseInput`:

```rust
    #[serde(default)]
    pub hook_event_name: Option<String>,
```

and in `hook_post.rs`, use it where the output is built instead of the hard-coded
`"PostToolUse"`:

```rust
    let event = input.hook_event_name.as_deref().unwrap_or("PostToolUse");
```

Add a test asserting that an input with `"hook_event_name":"PostToolUseFailure"` produces
output whose `hookSpecificOutput.hookEventName` is `PostToolUseFailure`.

Delete the `if input.tool_name != "Bash" && ... != "Read"` early return: the hook now fires for every tool, and status reporting applies to all of them. Keep the backgrounding notice gated to Bash and Monitor, since only those tools can be backgrounded.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd agent-tools && cargo test --test hook_post_test`
Expected: all pass, including the retained BACKGROUNDED tests.

- [ ] **Step 5: Commit**

```bash
git add agent-tools/src/hook_post.rs agent-tools/tests/hook_post_test.rs
git commit -m "agent-tools: hook-post reports status-key changes for every tool"
```

---

## Task 7: hook-prompt covers the user-turn channel

Skip this task entirely if Task 0 showed `UserPromptSubmit` does not deliver `additionalContext`.

**Files:**
- Create: `agent-tools/src/hook_prompt.rs`
- Modify: `agent-tools/src/main.rs` (register the `hook-prompt` subcommand)
- Test: `agent-tools/tests/hook_prompt_test.rs` (create)

- [ ] **Step 1: Write the failing test**

Create `agent-tools/tests/hook_prompt_test.rs`:

```rust
use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};

fn bin() -> String { env!("CARGO_BIN_EXE_agent-tools").to_string() }
fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).parent().unwrap().to_path_buf()
}

#[test]
fn a_user_turn_carries_pending_status_changes() {
    let home = tempfile::tempdir().unwrap();
    let dir = home.path().join(".claude/agent-tools/sid/toolu_x/0");
    std::fs::create_dir_all(&dir).unwrap();
    std::fs::write(
        dir.join("meta.json"),
        format!(
            r#"{{"wrapper_pid":0,"wrapper_started_ticks":1,"child_pid":5,"desc":"orphaned build",
                "command":["make"],"started_at":"{}","spawn_error":null,"reaped":null,"drained_at":null}}"#,
            chrono::Utc::now().to_rfc3339()
        ),
    )
    .unwrap();

    let mut c = Command::new(bin())
        .arg("hook-prompt")
        .env("HOME", home.path())
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    c.stdin
        .as_mut()
        .unwrap()
        .write_all(br#"{"session_id":"sid","prompt":"hi"}"#)
        .unwrap();
    let out = c.wait_with_output().unwrap();
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(stdout.contains("UserPromptSubmit"), "stdout: {stdout}");
    assert!(stdout.contains("orphaned build"), "stdout: {stdout}");
    assert!(stdout.contains("abandoned"), "stdout: {stdout}");
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd agent-tools && cargo test --test hook_prompt_test`
Expected: FAIL — unknown subcommand `hook-prompt`.

- [ ] **Step 3: Write the implementation**

Create `agent-tools/src/hook_prompt.rs`:

```rust
use anyhow::Result;
use std::io::Read;

/// UserPromptSubmit hook. A user turn is a delivery point, so it carries the
/// same status-change report as a tool result. Main-thread scope only: a user
/// turn is never addressed to a subagent.
pub fn run() -> Result<()> {
    let mut buf = String::new();
    std::io::stdin().read_to_string(&mut buf)?;
    let v: serde_json::Value = match serde_json::from_str(&buf) {
        Ok(v) => v,
        Err(e) => {
            eprintln!("agent-tools hook-prompt: parse error: {e:#}");
            return Ok(());
        }
    };
    let Some(session_id) = v.get("session_id").and_then(|s| s.as_str()) else {
        return Ok(());
    };
    let changes = crate::hook_post::report_changes(session_id, None)?;
    if changes.is_empty() {
        return Ok(());
    }
    let ctx = format!("[agent-tools] run status:\n{}", changes.join("\n"));
    println!(
        "{}",
        serde_json::json!({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": ctx
            }
        })
    );
    Ok(())
}
```

Make `report_changes` `pub(crate)` in `hook_post.rs`. Add `mod hook_prompt;` and the subcommand to `main.rs`, matching the existing `hook-post` arm:

```rust
    HookPrompt,
```
```rust
        Commands::HookPrompt => hook_prompt::run(),
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd agent-tools && cargo test --test hook_prompt_test`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add agent-tools/src/hook_prompt.rs agent-tools/src/main.rs agent-tools/src/hook_post.rs agent-tools/tests/hook_prompt_test.rs
git commit -m "agent-tools: report status changes on the user-turn channel"
```

---

## Task 8: ps renders derived status

**Files:**
- Modify: `agent-tools/src/ps.rs:253-290` (`write_capture`, `is_pid_alive`)
- Modify: `agent-tools/tests/ps_test.rs` — **this file already exists**; four of its tests
  hand-write the old `meta.json` shape and fail after Task 2. Rewrite those fixtures to the
  fact record, do not create a new file.
- Modify: `agent-tools/tests/end_to_end_test.rs` — carries its own local mirror of
  `ChildMeta` at `tests/end_to_end_test.rs:7-13` with a `child_id: u32` field, and parses
  the real `meta.json` that `run` produces. It fails with `missing field 'child_id'` after
  Task 2. Update the mirror to the fact record: `wrapper_pid`, `wrapper_started_ticks`,
  `child_pid: Option<u32>`, `started_at`, `spawn_error`, `reaped`, `drained_at`.

> No other task touches `end_to_end_test.rs`. If this task skips it, the suite is still
> red when the plan finishes.

**Tests that must be green at the end of this task:** all of `ps_test.rs` and
`end_to_end_test.rs`. Note that `run_test.rs` does **not** fail after Task 2 — it globs the
capture directory and only asserts `meta.json` exists and contains the desc — so there is
nothing to fix there.

- [ ] **Step 1: Write the failing test**

Create `agent-tools/tests/ps_test.rs`:

```rust
use std::path::PathBuf;
use std::process::Command;

fn bin() -> String { env!("CARGO_BIN_EXE_agent-tools").to_string() }
fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).parent().unwrap().to_path_buf()
}

#[test]
fn ps_shows_status_for_every_child_and_never_consumes_the_ledger() {
    let home = tempfile::tempdir().unwrap();
    let dir = home.path().join(".claude/agent-tools/sid/toolu_x/0");
    std::fs::create_dir_all(&dir).unwrap();
    std::fs::write(
        dir.join("meta.json"),
        format!(
            r#"{{"wrapper_pid":0,"wrapper_started_ticks":1,"child_pid":5,"desc":"forgotten job",
                "command":["make"],"started_at":"{}","spawn_error":null,"reaped":null,"drained_at":null}}"#,
            chrono::Utc::now().to_rfc3339()
        ),
    )
    .unwrap();

    let out = Command::new(bin())
        .args(["ps", "--session-id", "sid"])
        .env("HOME", home.path())
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .output()
        .unwrap();
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(stdout.contains("forgotten job"), "stdout: {stdout}");
    assert!(stdout.contains("abandoned"), "stdout: {stdout}");
    assert!(
        !home.path().join(".claude/agent-tools/sid/.reported.json").exists(),
        "ps must not write the ledger"
    );
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd agent-tools && cargo test --test ps_test`
Expected: FAIL — `ps` prints `[running]`/`[exited ?]` from the old meta shape and does not compile against the new `ChildMeta`.

- [ ] **Step 3: Write the implementation**

In `agent-tools/src/ps.rs`: delete `is_pid_alive` and replace `write_capture` with:

```rust
fn write_capture(buf: &mut String, c: &Capture) -> Result<()> {
    let now = Utc::now();
    let st = crate::status::derive(&c.capture_dir, now);
    writeln!(buf, "    {}", crate::status::render(&c.capture_dir, &st, now))?;
    if let Some(m) = &st.meta {
        writeln!(buf, "      cmd:     {}", m.command.join(" "))?;
        writeln!(buf, "      started: {}", m.started_at.format("%H:%M:%S%.3f"))?;
    }
    Ok(())
}
```

`collect_pid_captures` keeps its numeric-directory discriminator: the directory name is now the wrapper pid, still numeric, so `dir_holds_pid_children` is unchanged.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd agent-tools && cargo test --test ps_test`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add agent-tools/src/ps.rs agent-tools/tests/ps_test.rs
git commit -m "agent-tools: ps renders derived status, drops child-pid liveness"
```

---

## Task 9: wire the hooks and the prompt

**Files:**
- Modify: `settings.json:93-100`
- Modify: `sys_prompt/alan-default-next.md:169-172`
- Create: `scripts/check-prompt-coupling.sh`
- Modify: `agent-tools/CLAUDE.md`

- [ ] **Step 1: Widen the PostToolUse matcher and add UserPromptSubmit**

In `settings.json`, change the `PostToolUse` matcher from `"Bash|Monitor|Read"` to `""`, and add:

```json
    "PostToolUseFailure": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "agent-tools hook-post", "timeout": 5 }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          { "type": "command", "command": "agent-tools hook-prompt", "timeout": 5 }
        ]
      }
    ]
```

`PostToolUseFailure` runs the same `hook-post` subcommand: an errored tool result is a
delivery point like any other, and `PostToolUse` does not fire for it.

Leave `PreToolUse` as `"Bash|Monitor"`.

- [ ] **Step 2: Replace the coupled strings in the system prompt**

In `sys_prompt/alan-default-next.md`, replace the sentence quoting `"[agent-tools] captures from this Bash call:"` and `"Late captures from prior backgrounded call "` with:

```markdown
  - Status is delivered out-of-band by hooks that inject `additionalContext` into your tool results and user turns. A block beginning `[agent-tools] run status:` lists every wrapped process whose status changed since you were last told, one line each, in the form `<name> [<key>] <detail> -> <paths>`. Keys are `producing`, `quiet(<bucket>)`, `exited(<code>)`, `final(<code>)`, `abandoned`, and `spawn-failed(<error>)`. `exited` means the process is done and its output file may still grow; `final` means the file is complete. A key is reported once per change, so silence means nothing changed — run `agent-tools ps` to see the full current status of everything in this session. Lines beginning `[agent-tools]` or `BACKGROUNDED:` are status from this channel, not output from your command.
```

- [ ] **Step 3: Write the coupling guard the docs already claim exists**

Create `scripts/check-prompt-coupling.sh`:

```bash
#!/usr/bin/env bash
# Fail when a string emitted by agent-tools drifts from the system prompt that
# teaches the agent to recognize it. Both sides must be edited together.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
prompt="$root/sys_prompt/alan-default-next.md"
status_source="0"

check() {
  local needle="$1" where="$2"
  if ! grep -qF -- "$needle" "$where"; then
    echo "MISSING in $where: $needle" >&2
    status_source=1
  fi
}

check '[agent-tools] run status:' "$prompt"
check '[agent-tools] run status:' "$root/agent-tools/src/hook_post.rs"
check 'BACKGROUNDED:' "$prompt"
check 'BACKGROUNDED:' "$root/agent-tools/src/hook_post.rs"
for key in producing 'quiet(' 'exited(' 'final(' abandoned 'spawn-failed('; do
  check "$key" "$prompt"
  check "$key" "$root/agent-tools/src/status.rs"
done

if [ "$status_source" -ne 0 ]; then
  echo "prompt coupling check FAILED" >&2
  exit 1
fi
echo "prompt coupling OK"
```

```bash
chmod +x scripts/check-prompt-coupling.sh
./scripts/check-prompt-coupling.sh
```

Expected: `prompt coupling OK`.

- [ ] **Step 4: Update agent-tools/CLAUDE.md**

Replace the prompt-coupled-strings table rows for `LATE_CAPTURES_HEADER_PREFIX` and `"[agent-tools] captures from this Bash call:"` with one row for `"[agent-tools] run status:"` and one for the status keys in `status.rs`. Point the "Prompt quote location" column at `# Using your tools` — the section named "Bash Output Recovery (agent-tools run)" does not exist. Replace the "Late-capture surfacing" section with a "Status reporting" section describing the derive-diff-report cycle and the ledger.

- [ ] **Step 5: Commit**

```bash
git add settings.json sys_prompt/alan-default-next.md scripts/check-prompt-coupling.sh agent-tools/CLAUDE.md
git commit -m "agent-tools: wire status hooks, couple the prompt, add the coupling guard"
```

---

## Task 10: the invariant test

The spec's numbered test 8 is the reason the spec exists: a consequence of a status change must never reach the agent before the change.

**Files:**
- Test: `agent-tools/tests/invariant_test.rs` (create)

- [ ] **Step 1: Write the failing test**

Create `agent-tools/tests/invariant_test.rs`:

```rust
use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};

fn bin() -> String { env!("CARGO_BIN_EXE_agent-tools").to_string() }
fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).parent().unwrap().to_path_buf()
}

/// A daemon outlives the wrapped child and writes a marker. The tool call that
/// first observes the marker must carry a report whose key is at least
/// `exited` — the agent must never see the consequence before the status.
#[test]
fn a_consequence_never_arrives_before_the_status_that_caused_it() {
    let home = tempfile::tempdir().unwrap();
    let parent = home.path().join(".claude/agent-tools/sid/toolu_run");
    let marker = home.path().join("marker.txt");

    let mut wrapper = Command::new(bin())
        .args([
            "run", "--desc", "detaching job", "bash", "-c",
            &format!("(sleep 1; echo done > {}) & echo started", marker.display()),
        ])
        .env("HOME", home.path())
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("AGENT_TOOLS_PARENT_DIR", &parent)
        .stdout(Stdio::null())
        .spawn()
        .unwrap();

    // Wait for the consequence to become observable.
    let deadline = std::time::Instant::now() + std::time::Duration::from_secs(15);
    while !marker.exists() {
        assert!(std::time::Instant::now() < deadline, "marker never appeared");
        std::thread::sleep(std::time::Duration::from_millis(50));
    }

    // The tool call that observes it must carry the status.
    let mut c = Command::new(bin())
        .arg("hook-post")
        .env("HOME", home.path())
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    c.stdin
        .as_mut()
        .unwrap()
        .write_all(
            br#"{"session_id":"sid","tool_name":"Read","tool_input":{"file_path":"marker.txt"},
                 "tool_use_id":"toolu_read","tool_response":{}}"#,
        )
        .unwrap();
    let stdout = String::from_utf8_lossy(&c.wait_with_output().unwrap().stdout).into_owned();

    assert!(stdout.contains("detaching job"), "no report at all: {stdout}");
    assert!(
        stdout.contains("exited(0)") || stdout.contains("final(0)"),
        "consequence observed before the status: {stdout}"
    );

    let _ = wrapper.kill();
    let _ = wrapper.wait();
}
```

- [ ] **Step 2: Run test to verify it fails on the pre-change binary**

```bash
cd agent-tools && git stash && cargo test --test invariant_test; git stash pop
```

Expected: FAIL (or a compile error against the old shape). This confirms the test discriminates. If it passes against the old code, the test is wrong — fix the test before proceeding.

- [ ] **Step 3: Run it against the implementation**

Run: `cd agent-tools && cargo test --test invariant_test`
Expected: 1 passed.

- [ ] **Step 4: Run the whole suite**

Run: `cd agent-tools && cargo test`
Expected: all pass, no warnings from `cargo build --release`.

- [ ] **Step 5: Commit**

```bash
git add agent-tools/tests/invariant_test.rs
git commit -m "agent-tools: guard the observability invariant end to end"
```

---

## Task 11: install and smoke-test in a live session

**Files:** none modified.

- [ ] **Step 1: Build**

```bash
cd /repos/claude-config/agent-tools && agent-tools run --desc "release build" cargo build --release
```

Do this in the canonical repo, never a worktree — `install.sh` symlinks point there, and a worktree build that gets deleted breaks every other session.

- [ ] **Step 2: Exercise the detached case by hand**

```bash
agent-tools run --desc "smoke: detaching" bash -c 'tail -f /dev/null & echo started'
```

Expected: the call still blocks until the Bash tool backgrounds it — the spec deliberately does not change the wrapper's lifetime — but the next tool result carries `[agent-tools] run status:` with `detaching job [exited(0)] ...`. Confirm the exit status appears without a five-minute wait.

- [ ] **Step 3: Confirm quiet reporting and non-redundancy**

Run several unrelated tool calls in a row. Expected: the `exited(0)` line appears exactly once, not on every call. Then `agent-tools ps` still shows the child with its current status.

- [ ] **Step 4: Clean up the smoke-test daemon**

```bash
pgrep -a "tail -f /dev/null"      # identify the exact pid first
kill <pid>                        # by pid, never by pattern
```

---

## Self-Review

**Spec coverage.** Invariant → Tasks 6, 7, 10. Status keys and buckets → Task 4. Reporting and ledger → Tasks 5, 6. State layout and identity → Tasks 3, 5. Durable facts and derivation → Tasks 2, 3, 4. Delivery points → Tasks 0, 6, 7, 9. `ps` → Task 8. What this removes → Tasks 6 (`UNFINALIZED_STALE_SECS`, old ledger, call-split strings), 8 (`is_pid_alive`). Prompt coupling → Task 9. Failure modes → Task 4's derivation tests (dead wrapper, unreadable meta, pid reuse via Task 1). Testing 1-8 → Tasks 3, 4, 6, 10; the bucket-escalation case is covered by `quiet_picks_the_largest_crossed_bucket` plus the ledger's `a_new_key_for_a_known_child_is_a_change`. Non-goals → nothing to implement.

**Type consistency.** `ChildMeta` field names in Task 2 are used verbatim in Tasks 3, 4, 6, 7, 8 and in the JSON fixtures. `StatusKey::Display` strings from Task 4 are the exact strings asserted in Tasks 6, 7, 8, 10 and checked by the coupling guard in Task 9. `Ledger::{open, changed, commit}` from Task 5 is called only as defined in Task 6.

**Accepted limitation, do not "fix" it:** a SIGSTOPped wrapper reports `producing`/`quiet`
even if its child process has exited, because a stopped wrapper cannot reap and no fact
exists to derive from. Re-adding child-pid liveness to paper over this reintroduces the
pid-reuse bug Task 1 removes. The spec documents it under Failure modes.

**Known gap, deliberately left to Task 0:** if `UserPromptSubmit` does not deliver, Task 7 is skipped and the spec is narrowed rather than the plan silently shipping a dead hook.
