# `agent-tools run` Passthrough Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `agent-tools run` substitutable for the bare command it wraps, closing findings F1, F2 and F3 from `notes/agent-tools-run-stress-findings.md`.

**Architecture:** The process machinery (spawn, tee, wait, drain, exit code) moves out of `run.rs` into a new `core.rs` that knows nothing about scopes, ledgers or hooks. A second subcommand, `run-core`, drives that same code with nothing but a capture directory, so every passthrough property can be tested by differencing it against the bare command. `run` keeps its observability wiring and calls the same core through two callbacks (`on_spawn`, `on_reap`) that preserve today's ordering guarantees.

**Tech Stack:** Rust 2021, tokio (multi-thread runtime; this plan adds the `net` feature for `tokio::net::unix::pipe::Receiver`), nix 0.29 (`fstat`, `fcntl`, `pipe`), anyhow, tempfile for tests. No new crates.

**Spec:** `docs/superpowers/specs/2026-08-26-agent-tools-run-design.md` — the Passthrough section and the merge rule. Read it before Task 3.

---

## Before you start

Build and test baseline:

```bash
cd /root/claude-config-work/agent-tools
cargo build --release
cargo test --no-fail-fast
```

`--no-fail-fast` is required: plain `cargo test` stops at the first failing test binary, so
every suite after it silently never runs and any total you read is truncated.

**Expected:** exactly one failure,
`opencode_test.rs::opencode_loads_prefixed_langfuse_env_and_forwards_args`, and no other.
Judge yourself on the named tests in each task rather than on a total, which grows as the
tasks add tests.

That failure is **pre-existing and unrelated to this plan**. It happens because the test
uses the real worktree root, so `agent-tools opencode` reads the repository's own `.env`,
whose `OPENCODE_LANGFUSE_*` values take precedence (`src/opencode.rs:23`) over the process
environment the test sets. Do not fix it here and do not let it block you. Every "expected:
PASS" below refers to the named test, not to the whole suite.

Run per-suite while working — it is faster and skips the known failure:

```bash
cargo test --test core_test
cargo test --bin agent-tools core::
```

`agent-tools` is a binary-only crate with no `[lib]` target, so `cargo test --lib` fails
outright rather than running anything. Inline `#[cfg(test)]` tests live in the bin target;
reach them with `--bin agent-tools`, and integration tests with `--test <file_stem>`.

## File structure

| File | New? | Responsibility |
| --- | --- | --- |
| `agent-tools/src/core.rs` | create | The process core: merge decision, spawn, tee, wait, bounded drain, outcome facts. No scope, ledger, hook or `AGENT_TOOLS_PARENT_DIR` knowledge. |
| `agent-tools/src/capture.rs` | modify | `tee` gains forward-close detection, capture-failure isolation, and a drain bound. Returns what happened instead of discarding it. |
| `agent-tools/src/run.rs` | modify | Keeps meta and events wiring; delegates process handling, and signal forwarding with it, to `core`. Persists the outcome facts. |
| `agent-tools/src/meta.rs` | modify | `ChildMeta` carries the facts that explain a difference from bare. |
| `agent-tools/src/status.rs` | modify | `render()` shows those facts beside the key. |
| `agent-tools/src/main.rs` | modify | `Cmd::RunCore` variant + dispatch arm. |
| `agent-tools/Cargo.toml` | modify | tokio `net` feature. |
| `agent-tools/tests/core_test.rs` | create | Differential tests: `run-core` vs bare. |

---

## Task 1: Extract the process core behind a second entry point

The spec's "A second entry point": every passthrough property is a property of processes, so
a test must drive a real binary — but `run` demands a scope it does not need. This task adds
that entry point and changes no behaviour.

**Files:**
- Create: `agent-tools/src/core.rs`
- Create: `agent-tools/tests/core_test.rs`
- Modify: `agent-tools/src/main.rs` (`enum Cmd` around :118, dispatch around :384)
- Modify: `agent-tools/src/run.rs:46-179`

- [ ] **Step 1: Write the failing test**

Create `agent-tools/tests/core_test.rs`:

```rust
use std::path::PathBuf;
use std::process::Command;

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .to_path_buf()
}

fn agent_tools() -> Command {
    let mut c = Command::new(bin());
    c.env("CLAUDE_CONFIG_ROOT", worktree_root());
    c
}

#[test]
fn run_core_forwards_both_streams_and_exit_code() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");

    let out = agent_tools()
        .args(["run-core", "--capture-dir"])
        .arg(&cap)
        .args(["--", "bash", "-c", "echo to-out; echo to-err >&2; exit 7"])
        .output()
        .unwrap();

    assert_eq!(out.status.code(), Some(7), "exit code must be the child's");
    assert_eq!(String::from_utf8_lossy(&out.stdout), "to-out\n");
    assert_eq!(String::from_utf8_lossy(&out.stderr), "to-err\n");
    assert_eq!(std::fs::read_to_string(cap.join("stdout")).unwrap(), "to-out\n");
    assert_eq!(std::fs::read_to_string(cap.join("stderr")).unwrap(), "to-err\n");
}

#[test]
fn run_core_needs_no_parent_dir_env() {
    let tmp = tempfile::tempdir().unwrap();
    let out = agent_tools()
        .args(["run-core", "--capture-dir"])
        .arg(tmp.path().join("cap"))
        .args(["--", "echo", "hi"])
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();

    assert_eq!(out.status.code(), Some(0));
    assert_eq!(String::from_utf8_lossy(&out.stdout), "hi\n");
}

#[test]
fn run_core_inherits_stdin() {
    use std::io::Write;
    use std::process::Stdio;
    let tmp = tempfile::tempdir().unwrap();
    let mut child = agent_tools()
        .args(["run-core", "--capture-dir"])
        .arg(tmp.path().join("cap"))
        .args(["--", "cat"])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.take().unwrap().write_all(b"piped\n").unwrap();
    let out = child.wait_with_output().unwrap();
    assert_eq!(String::from_utf8_lossy(&out.stdout), "piped\n");
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cargo test --test core_test`
Expected: FAIL — clap errors with `unrecognized subcommand 'run-core'`.

- [ ] **Step 3: Create the core module**

Create `agent-tools/src/core.rs`:

```rust
use anyhow::Result;
use std::path::{Path, PathBuf};
use std::process::Stdio;
use std::sync::atomic::AtomicI64;
use std::sync::Arc;
use tokio::process::Command;

use crate::capture;

/// Why the child's two streams did or did not share one destination.
#[derive(Debug, Clone, PartialEq)]
pub enum Merge {
    /// One destination. The reason names the condition that made it sound.
    Merged(&'static str),
    /// Two destinations. The reason names what disqualified merging.
    Split(&'static str),
}

/// What the core observed. Everything here explains a difference from bare.
#[derive(Debug, Clone)]
pub struct Outcome {
    pub exit_code: i32,
    pub merge: Merge,
}

/// Spawn failed, or something else did. Kept distinct so `run` can record the
/// spawn error string exactly as the OS reported it.
#[derive(Debug)]
pub enum CoreError {
    Spawn(std::io::Error),
    Other(anyhow::Error),
}

impl std::fmt::Display for CoreError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CoreError::Spawn(e) => write!(f, "{e}"),
            CoreError::Other(e) => write!(f, "{e:#}"),
        }
    }
}

impl From<anyhow::Error> for CoreError {
    fn from(e: anyhow::Error) -> Self {
        CoreError::Other(e)
    }
}

/// Run `cmd`, capturing both streams under `capture_dir` and forwarding them to
/// this process's own stdout/stderr.
///
/// `on_spawn` receives the child pid the moment it exists; `on_reap` receives the
/// exit code the moment the child is reaped, before any draining. `run` uses those
/// to persist facts in the order the invariant requires; `run-core` ignores them.
pub async fn run_core<S, R>(
    cmd: &[String],
    capture_dir: &Path,
    on_spawn: S,
    on_reap: R,
) -> Result<Outcome, CoreError>
where
    S: FnOnce(u32),
    R: FnOnce(i32),
{
    std::fs::create_dir_all(capture_dir)
        .map_err(|e| CoreError::Other(anyhow::anyhow!("mkdir {}: {e}", capture_dir.display())))?;

    let mut child = Command::new(&cmd[0])
        .args(&cmd[1..])
        .stdin(Stdio::inherit())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(CoreError::Spawn)?;

    let pid = child
        .id()
        .ok_or_else(|| CoreError::Other(anyhow::anyhow!("child pid unavailable")))?;
    on_spawn(pid);

    let stdout_pipe = child
        .stdout
        .take()
        .ok_or_else(|| CoreError::Other(anyhow::anyhow!("no stdout pipe")))?;
    let stderr_pipe = child
        .stderr
        .take()
        .ok_or_else(|| CoreError::Other(anyhow::anyhow!("no stderr pipe")))?;

    let (cancel_tx, cancel_rx) = tokio::sync::watch::channel(false);
    crate::signals::install_forwarding(pid as i32, cancel_rx.clone()).ok();

    let last_stdout = Arc::new(AtomicI64::new(chrono::Utc::now().timestamp_millis()));
    let last_stderr = Arc::new(AtomicI64::new(chrono::Utc::now().timestamp_millis()));

    let dir: PathBuf = capture_dir.to_path_buf();
    let stdout_tee = tokio::spawn(capture::tee(
        "stdout",
        stdout_pipe,
        dir.join("stdout"),
        tokio::io::stdout(),
        last_stdout.clone(),
        dir.clone(),
    ));
    let stderr_tee = tokio::spawn(capture::tee(
        "stderr",
        stderr_pipe,
        dir.join("stderr"),
        tokio::io::stderr(),
        last_stderr.clone(),
        dir.clone(),
    ));
    let s1 = tokio::spawn(capture::watch_silence(
        "stdout",
        last_stdout,
        30_000,
        dir.clone(),
        cancel_rx.clone(),
    ));
    let s2 = tokio::spawn(capture::watch_silence(
        "stderr",
        last_stderr,
        30_000,
        dir.clone(),
        cancel_rx,
    ));

    let status = child
        .wait()
        .await
        .map_err(|e| CoreError::Other(anyhow::anyhow!("wait: {e}")))?;
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
    on_reap(exit_code);

    let _ = cancel_tx.send(true);
    let _ = stdout_tee.await;
    let _ = stderr_tee.await;
    let _ = s1.await;
    let _ = s2.await;

    Ok(Outcome {
        exit_code,
        merge: Merge::Split("not yet decided"),
    })
}
```

- [ ] **Step 4: Register the module and the subcommand**

In `agent-tools/src/main.rs`, add to the module list (the `mod` block at :56-72):

```rust
mod core;
```

Add to `enum Cmd` (after the `Run` variant around :118):

```rust
    /// Run a command through the passthrough core with no scope, ledger or hooks.
    /// Exists so passthrough behaviour can be differenced against the bare command.
    /// Not taught by the system prompt: use `run` for anything that needs reporting.
    #[command(name = "run-core")]
    RunCore {
        #[arg(long)]
        capture_dir: std::path::PathBuf,
        // No `last = true`: clap asserts at runtime that it cannot be combined with
        // `trailing_var_arg`, and the assert is debug-only, so a release build would
        // accept it and only `cargo test` would fail. This matches `Cmd::Run`.
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        cmd: Vec<String>,
    },
```

Add a dispatch arm next to `Cmd::Run` (around :384):

```rust
        Cmd::RunCore { capture_dir, cmd } => {
            if cmd.is_empty() {
                eprintln!("agent-tools run-core: no command supplied after --");
                std::process::exit(2);
            }
            let outcome = tokio::runtime::Builder::new_multi_thread()
                .enable_all()
                .build()
                .unwrap()
                .block_on(core::run_core(&cmd, &capture_dir, |_| {}, |_| {}));
            match outcome {
                Ok(o) => std::process::exit(o.exit_code),
                Err(e) => {
                    eprintln!("agent-tools run-core: {e}");
                    std::process::exit(2);
                }
            }
        }
```

The inner `cmd => match cmd` block (around :522) requires an `unreachable!()` line for every
variant handled early, or the build fails. Add:

```rust
        Cmd::RunCore { .. } => unreachable!(),
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cargo test --test core_test`
Expected: PASS, 3 tests.

- [ ] **Step 6: Make `run` use the core**

Replace `agent-tools/src/run.rs:69-179` (from `let spawned = Command::new(...)` to the end of
the function) with a call through the core. The callbacks preserve today's ordering: meta and
`child_started` at spawn, the reap recorded *before* draining.

`ChildMeta` is shared with the callbacks, so wrap it once and let each callback write at the
instant its fact becomes true:

```rust
    use std::sync::Mutex;

    let cm = Arc::new(Mutex::new(cm));

    let on_spawn = {
        let cm = cm.clone();
        let dir = child_dir.clone();
        let parent = parent_dir.clone();
        let desc = desc.clone();
        let cmdv = cmd.clone();
        move |pid: u32| {
            let mut m = cm.lock().unwrap();
            m.child_pid = Some(pid);
            let _ = meta::write_meta(&dir, &m);
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
            let mut m = cm.lock().unwrap();
            m.reaped = Some(meta::Reaped { at: chrono::Utc::now(), status: code });
            let _ = meta::write_meta(&dir, &m);
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
            let mut m = cm.lock().unwrap();
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
        let mut m = cm.lock().unwrap();
        m.drained_at = Some(chrono::Utc::now());
        meta::write_meta(&child_dir, &m)?;
    }
    events::append(&parent_dir, "drained", serde_json::json!({"wrapper_pid": wrapper_pid}))
        .ok();

    Ok(outcome.exit_code)
```

`&m` is a `MutexGuard<ChildMeta>`; deref coercion gives `write_meta` the `&ChildMeta` it wants,
so no `Clone` derive is needed.

**No `meta.json` write may decide the caller's exit code.** Bookkeeping is the wrapper's
job, and the spec guarantees the caller receives the child's exit code; a capture that cannot
be written "is the wrapper's failure, not the child's", and a meta write is no different.
Every `write_meta` after the child exists therefore records a `meta_write_failed` event and
continues, rather than propagating. This is not silent — it is stated in the event stream —
and it is not lossy in the way it looks: with `reaped: Some` and the wrapper gone,
`status::derive` yields `final(status)` even if `drained_at` never lands, so a lost write
costs the `exited`→`final` transition, not the child's fate.

Never `eprintln!` from inside a callback. `on_reap` can run while the stderr tee is still
forwarding child output to fd 2, and the two writers are not synchronized, so a diagnostic
can interleave with the child's own stderr and break the "unmodified and in order" guarantee.

The one real cost is per fact. A lost `reaped` write leaves a reader seeing `reaped: None`
with the wrapper alive, deriving `producing` for a child that has already exited. A lost
`drained_at` costs only the `exited`→`final` transition. A lost `child_pid` shows `pid -` in
`ps` and in the pushed report for the child's whole lifetime, because `status::render` reads
that field from disk rather than from the in-memory struct.

**Why no `eprintln!` for these, when Tasks 5-7 do print to stderr.** Not because the wrapper
never adds bytes to stderr — those tasks add exactly that, and the spec requires it for
stream and capture failures. The reason is narrower: the "stated on stderr and in the status"
clause is scoped to the Guaranteed tier's forwarded-stream and capture failures, and says
nothing about bookkeeping. A meta write is not a passthrough failure. On top of that, at
`on_spawn`/`on_reap` the tee is provably still live on fd 2, so a diagnostic there would race
the child's own output. Do not carry the substitutability argument into Tasks 5-7; it does not
hold there.

Know the limit of "and in the status": the pushed report is built from `status::derive`
alone and never reads `events.jsonl`, so a `meta_write_failed` event changes nothing the agent
is shown automatically. It surfaces only through `agent-tools ps`. The state machine still
self-heals — a transient failure resolves to `final`, a permanent one to `abandoned` — so what
is missing is the reason, not a correct status.

Later tasks adding facts to `ChildMeta` inherit this whole policy.

Three supporting edits: add `use crate::core;` to the imports at `run.rs:7-11`; delete the now
unused `use std::process::Stdio;` (`run.rs:2`) and `use tokio::process::Command;` (`run.rs:5`),
since the core owns spawning; and delete the `signals::install_forwarding` call at `run.rs:105`
along with its `use crate::signals;` import, because the core installs it now.

- [ ] **Step 7: Verify `run` still behaves and facts stay ordered**

Run: `cargo test --test run_test --test run_facts_test --test end_to_end_test --test invariant_test`
Expected: PASS — 8 + 3 + 1 + 1 tests. `run_facts_test::reap_recorded_before_drain` is the one
that proves the callback ordering survived the extraction.

- [ ] **Step 8: Commit**

```bash
cd /root/claude-config-work
git add agent-tools/src/core.rs agent-tools/src/main.rs agent-tools/src/run.rs agent-tools/src/meta.rs agent-tools/tests/core_test.rs
git commit -m "agent-tools: the passthrough core could only be driven through a scope"
```

---

## Task 2: A differential harness

The spec makes `run-core` and bare interchangeable claims; a helper that runs both and
compares is what turns each later task into a one-line assertion.

**Files:**
- Modify: `agent-tools/tests/core_test.rs`

- [ ] **Step 1: Write the failing test**

Append to `agent-tools/tests/core_test.rs`:

```rust
struct Run {
    stdout: Vec<u8>,
    stderr: Vec<u8>,
    code: Option<i32>,
}

/// Run `script` bare, and again through `run-core`, and return both.
fn differential(script: &str) -> (Run, Run) {
    // Both sides get the same environment: the only difference between them must
    // be the wrapper itself.
    let bare = Command::new("bash")
        .args(["-c", script])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .output()
        .unwrap();
    let tmp = tempfile::tempdir().unwrap();
    let wrapped = agent_tools()
        .args(["run-core", "--capture-dir"])
        .arg(tmp.path().join("cap"))
        .args(["--", "bash", "-c", script])
        .output()
        .unwrap();
    (
        Run { stdout: bare.stdout, stderr: bare.stderr, code: bare.status.code() },
        Run { stdout: wrapped.stdout, stderr: wrapped.stderr, code: wrapped.status.code() },
    )
}

/// Where the two streams part, in bytes. The renderings cannot always show it —
/// the invalid-UTF-8 case renders identically on both sides, which is the whole
/// reason the comparison moved off the rendering.
fn first_difference(bare: &[u8], wrapped: &[u8]) -> String {
    match bare.iter().zip(wrapped).position(|(a, b)| a != b) {
        Some(i) => format!(
            "first difference at byte {i}: bare {:#04x}, wrapped {:#04x}",
            bare[i], wrapped[i]
        ),
        None => format!("equal for {} bytes, then one side ends", bare.len().min(wrapped.len())),
    }
}

/// Compare on bytes, report as text. The guarantee under test is "unmodified and
/// in order", and `from_utf8_lossy` maps every invalid sequence onto the same
/// replacement character — so comparing rendered strings would accept a wrapper
/// that reordered bytes inside invalid UTF-8. Tasks 3 and 4 are about byte order
/// specifically, so that blind spot would sit directly under what they change.
fn assert_same(script: &str) {
    let (bare, wrapped) = differential(script);
    assert_eq!(bare.code, wrapped.code, "exit code differs for {script:?}");
    assert_stream_same("stdout", script, &bare.stdout, &wrapped.stdout);
    assert_stream_same("stderr", script, &bare.stderr, &wrapped.stderr);
}

fn assert_stream_same(stream: &str, script: &str, bare: &[u8], wrapped: &[u8]) {
    assert!(
        bare == wrapped,
        "{stream} differs for {script:?}\n  {}\n  bare    ({} bytes): {}\n  wrapped ({} bytes): {}",
        first_difference(bare, wrapped),
        bare.len(),
        preview(bare),
        wrapped.len(),
        preview(wrapped)
    );
}

/// Render a stream for a failure message, capped. A mismatch on the 100 KB case
/// would otherwise put 200 KB into the panic, burying every other failure in the
/// run. The offset and the two lengths above already carry the answer, so the
/// rendering only has to be recognizable.
fn preview(bytes: &[u8]) -> String {
    const MAX: usize = 200;
    if bytes.len() <= MAX {
        return format!("{:?}", String::from_utf8_lossy(bytes));
    }
    format!(
        "{:?}… ({} more bytes)",
        String::from_utf8_lossy(&bytes[..MAX]),
        bytes.len() - MAX
    )
}

#[test]
fn core_agrees_with_bare_on_content_and_exit_code() {
    assert_same("echo plain");
    assert_same("echo out; echo err >&2");
    assert_same("exit 3");
    assert_same("printf 'no trailing newline'");
    assert_same("for i in $(seq 1 500); do echo line-$i; done");
    assert_same("head -c 100000 /dev/zero | tr '\\0' 'x'");
    // Invalid UTF-8: bytes the lossy rendering cannot tell apart.
    assert_same("printf '\\xff\\xfe\\xfd'");
}

#[test]
fn a_pipeline_inside_a_wrapped_command_still_dies_of_sigpipe() {
    // The wrapper ignores SIGPIPE for its own writes; the child must not inherit
    // that, or an inner pipeline behaves differently than it does bare. Measured
    // before this plan: bare and wrapped both exit 141 here.
    let tmp = tempfile::tempdir().unwrap();
    let out = agent_tools()
        .args(["run-core", "--capture-dir"])
        .arg(tmp.path().join("cap"))
        .args(["--", "bash", "-c", "yes | head -2; exit ${PIPESTATUS[0]}"])
        .output()
        .unwrap();
    assert_eq!(String::from_utf8_lossy(&out.stdout), "y\ny\n");
    assert_eq!(
        out.status.code(),
        Some(141),
        "the inner `yes` must die of SIGPIPE, as it does bare"
    );
}

#[test]
fn core_agrees_with_bare_on_signalled_death_status() {
    let (bare, wrapped) = differential("kill -TERM $$");
    assert_eq!(bare.code, None, "bare: killed by a signal reports no code");
    assert_eq!(
        wrapped.code,
        Some(143),
        "wrapped: the spec promises 128+signum as the wrapper's own exit code"
    );
}
```

The second test states a difference the spec's "Not achievable" tier accepts: a wrapper cannot
die of its child's signal, so it reports `128 + signum` instead. Pinning it stops the
difference from being rediscovered as a bug.

- [ ] **Step 2: Run the tests**

Run: `cargo test --test core_test`
Expected: PASS, 6 tests.

- [ ] **Step 3: Commit**

```bash
git add agent-tools/tests/core_test.rs
git commit -m "agent-tools: passthrough claims had no way to be differenced against bare"
```

---

## Task 3: Decide the merge from the caller's own descriptors

Spec, the merge rule: the child's two streams share one destination **exactly when** the
caller's own two descriptors provably reach one destination that cannot disagree about where
the next byte goes — same file, both writable, both pipes or both appending.

This truth table was measured before this plan was written:

| Caller's fd 1 and 2 | Decision |
| --- | --- |
| both to one appending regular file (`>>f 2>&1`, and the Claude Code Bash tool) | merge |
| both to one pipe (`\| cat` with `2>&1`) | merge |
| same file, opened separately without append (`>f 2>f`) | split — offsets can disagree |
| different files | split |

**Files:**
- Modify: `agent-tools/src/core.rs`
- Modify: `agent-tools/Cargo.toml`

- [ ] **Step 1: Write the failing test**

Append to `agent-tools/src/core.rs`:

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use std::os::fd::AsRawFd;

    #[test]
    fn two_pipes_to_one_destination_merge() {
        let (r, w) = nix::unistd::pipe().unwrap();
        let w2 = w.try_clone().unwrap();
        assert_eq!(
            decide_merge(w.as_raw_fd(), w2.as_raw_fd()),
            Merge::Merged("both pipes, same destination")
        );
        drop(r);
    }

    #[test]
    fn one_appending_file_under_two_descriptors_merges() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("both");
        let a = std::fs::OpenOptions::new().create(true).append(true).open(&path).unwrap();
        let b = std::fs::OpenOptions::new().create(true).append(true).open(&path).unwrap();
        assert_eq!(
            decide_merge(a.as_raw_fd(), b.as_raw_fd()),
            Merge::Merged("both appending, same file")
        );
    }

    #[test]
    fn same_file_without_append_splits() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("both");
        let a = std::fs::File::create(&path).unwrap();
        let b = std::fs::OpenOptions::new().write(true).open(&path).unwrap();
        assert_eq!(
            decide_merge(a.as_raw_fd(), b.as_raw_fd()),
            Merge::Split("same file, but not both appending")
        );
    }

    #[test]
    fn different_files_split() {
        let dir = tempfile::tempdir().unwrap();
        let a = std::fs::File::create(dir.path().join("a")).unwrap();
        let b = std::fs::File::create(dir.path().join("b")).unwrap();
        assert_eq!(
            decide_merge(a.as_raw_fd(), b.as_raw_fd()),
            Merge::Split("different destinations")
        );
    }

    #[test]
    fn a_read_only_descriptor_splits() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("f");
        std::fs::write(&path, b"x").unwrap();
        let a = std::fs::File::open(&path).unwrap();
        let b = std::fs::File::open(&path).unwrap();
        assert_eq!(
            decide_merge(a.as_raw_fd(), b.as_raw_fd()),
            Merge::Split("not both writable")
        );
    }
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cargo test --bin agent-tools core::`
Expected: FAIL — `cannot find function 'decide_merge' in this scope`.

- [ ] **Step 3: Implement the decision**

Add to `agent-tools/src/core.rs`:

```rust
/// Decide whether the child's two streams may share one destination.
///
/// Whether two descriptors share an open file description is not decidable from
/// userspace, so this does not try. It admits only destinations that have no
/// offset to disagree about — a pipe, or a file both descriptors append to —
/// which makes the question irrelevant. Everything else splits. Declining costs
/// interleaving; guessing wrong misroutes the caller's data.
pub fn decide_merge(fd_out: i32, fd_err: i32) -> Merge {
    use nix::fcntl::{fcntl, FcntlArg, OFlag};
    use nix::sys::stat::{fstat, SFlag};

    let (s_out, s_err) = match (fstat(fd_out), fstat(fd_err)) {
        (Ok(a), Ok(b)) => (a, b),
        _ => return Merge::Split("descriptor could not be inspected"),
    };
    if s_out.st_dev != s_err.st_dev || s_out.st_ino != s_err.st_ino {
        return Merge::Split("different destinations");
    }

    let (f_out, f_err) = match (
        fcntl(fd_out, FcntlArg::F_GETFL),
        fcntl(fd_err, FcntlArg::F_GETFL),
    ) {
        (Ok(a), Ok(b)) => (
            OFlag::from_bits_truncate(a),
            OFlag::from_bits_truncate(b),
        ),
        _ => return Merge::Split("descriptor flags could not be read"),
    };
    let writable = |f: OFlag| {
        let m = f & OFlag::O_ACCMODE;
        m == OFlag::O_WRONLY || m == OFlag::O_RDWR
    };
    if !writable(f_out) || !writable(f_err) {
        return Merge::Split("not both writable");
    }

    let is_fifo = |s: &nix::sys::stat::FileStat| {
        SFlag::from_bits_truncate(s.st_mode).contains(SFlag::S_IFIFO)
    };
    if is_fifo(&s_out) && is_fifo(&s_err) {
        return Merge::Merged("both pipes, same destination");
    }
    if f_out.contains(OFlag::O_APPEND) && f_err.contains(OFlag::O_APPEND) {
        return Merge::Merged("both appending, same file");
    }
    Merge::Split("same file, but not both appending")
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cargo test --bin agent-tools core::`
Expected: PASS, 5 tests.

- [ ] **Step 5: Commit**

```bash
git add agent-tools/src/core.rs
git commit -m "agent-tools: the merge decision had no way to read the caller's descriptors"
```

---

## Task 4: Honour the decision — one pipe, one capture file

Spec: "The capture follows the decision — merged, one file; split, two, the faithful record
since the caller's streams already carry that split", and "A merged capture holds one file;
the other is absent, not empty — an empty stderr file would read as 'no diagnostics'".

**Files:**
- Modify: `agent-tools/Cargo.toml`
- Modify: `agent-tools/src/core.rs`
- Modify: `agent-tools/tests/core_test.rs`

- [ ] **Step 1: Write the failing test**

Append to `agent-tools/tests/core_test.rs`:

```rust
use std::process::Stdio;

/// Run `run-core` with both of its own descriptors on one appending file, which
/// is the shape the merge rule admits and the shape the Claude Code Bash tool has.
fn run_core_to_one_appending_file(script: &str) -> (String, tempfile::TempDir) {
    let tmp = tempfile::tempdir().unwrap();
    let sink = tmp.path().join("caller.log");
    let cap = tmp.path().join("cap");
    let f = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&sink)
        .unwrap();
    let f2 = f.try_clone().unwrap();
    let status = agent_tools()
        .args(["run-core", "--capture-dir"])
        .arg(&cap)
        .args(["--", "bash", "-c", script])
        .stdout(Stdio::from(f))
        .stderr(Stdio::from(f2))
        .status()
        .unwrap();
    assert!(status.code().is_some());
    let text = std::fs::read_to_string(&sink).unwrap();
    // The TempDir is returned so the capture outlives this call.
    (text, tmp)
}

#[test]
fn merged_streams_keep_their_relative_order() {
    let script = "for i in $(seq 1 200); do echo out-$i; echo err-$i >&2; done";
    let (text, _tmp) = run_core_to_one_appending_file(script);
    let lines: Vec<&str> = text.lines().collect();
    assert_eq!(lines.len(), 400, "every line arrives exactly once");
    for i in 0..200 {
        assert_eq!(lines[i * 2], format!("out-{}", i + 1));
        assert_eq!(lines[i * 2 + 1], format!("err-{}", i + 1));
    }
}

#[test]
fn merged_capture_holds_one_file_and_no_empty_stderr() {
    let (_text, tmp) = run_core_to_one_appending_file("echo a; echo b >&2");
    let cap = tmp.path().join("cap");
    let merged = std::fs::read_to_string(cap.join("output")).unwrap();
    assert_eq!(merged, "a\nb\n");
    assert!(
        !cap.join("stderr").exists(),
        "an empty stderr file would read as 'no diagnostics'"
    );
    assert!(!cap.join("stdout").exists());
}

#[test]
fn split_capture_holds_two_files() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");
    agent_tools()
        .args(["run-core", "--capture-dir"])
        .arg(&cap)
        .args(["--", "bash", "-c", "echo a; echo b >&2"])
        .output()
        .unwrap();
    assert_eq!(std::fs::read_to_string(cap.join("stdout")).unwrap(), "a\n");
    assert_eq!(std::fs::read_to_string(cap.join("stderr")).unwrap(), "b\n");
    assert!(!cap.join("output").exists());
}

#[test]
fn long_lines_survive_the_merge_uncorrupted() {
    let script = "for i in $(seq 1 40); do printf 'O%.0s' $(seq 1 9000); echo; \
                  printf 'E%.0s' $(seq 1 9000) >&2; echo >&2; done";
    let (text, _tmp) = run_core_to_one_appending_file(script);
    for line in text.lines() {
        assert_eq!(line.len(), 9000, "a spliced line means the merge failed");
        let first = line.as_bytes()[0];
        assert!(
            line.bytes().all(|b| b == first),
            "a line mixing O and E is two writes spliced together"
        );
    }
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cargo test --test core_test merged`
Expected: FAIL — `cap/output` does not exist; both streams still go to two pipes, and
`merged_streams_keep_their_relative_order` fails on interleaving.

- [ ] **Step 3: Add the tokio `net` feature**

`tokio::net::unix::pipe::Receiver` is what reads a raw pipe fd asynchronously, and it is
behind the `net` feature. In `agent-tools/Cargo.toml`, change the tokio line to:

```toml
tokio = { version = "1", features = ["rt-multi-thread","macros","io-util","io-std","process","signal","time","fs","sync","net"] }
```

- [ ] **Step 4: Spawn one pipe when the decision says merge**

In `agent-tools/src/core.rs`, replace the spawn and tee section of `run_core` with a branch on
the decision. Take the decision from this process's own fds 1 and 2 before spawning:

```rust
    let merge = decide_merge(1, 2);

    let mut command = Command::new(&cmd[0]);
    command.args(&cmd[1..]).stdin(Stdio::inherit());

    let merged_reader = if let Merge::Merged(_) = merge {
        let (r, w) = nix::unistd::pipe()
            .map_err(|e| CoreError::Other(anyhow::anyhow!("pipe: {e}")))?;
        let w2 = w
            .try_clone()
            .map_err(|e| CoreError::Other(anyhow::anyhow!("dup: {e}")))?;
        command.stdout(Stdio::from(w)).stderr(Stdio::from(w2));
        Some(r)
    } else {
        command.stdout(Stdio::piped()).stderr(Stdio::piped());
        None
    };

    let mut child = command.spawn().map_err(CoreError::Spawn)?;
```

Then, after `on_spawn(pid)` and the signal wiring, replace the two `tokio::spawn(capture::tee(
...))` calls with:

```rust
    let (tee_a, tee_b) = match merged_reader {
        Some(r) => {
            let rx = tokio::net::unix::pipe::Receiver::from_owned_fd(r)
                .map_err(|e| CoreError::Other(anyhow::anyhow!("async pipe: {e}")))?;
            let a = tokio::spawn(capture::tee(
                "output",
                rx,
                dir.join("output"),
                tokio::io::stdout(),
                last_stdout.clone(),
                dir.clone(),
            ));
            (a, None)
        }
        None => {
            let stdout_pipe = child
                .stdout
                .take()
                .ok_or_else(|| CoreError::Other(anyhow::anyhow!("no stdout pipe")))?;
            let stderr_pipe = child
                .stderr
                .take()
                .ok_or_else(|| CoreError::Other(anyhow::anyhow!("no stderr pipe")))?;
            let a = tokio::spawn(capture::tee(
                "stdout",
                stdout_pipe,
                dir.join("stdout"),
                tokio::io::stdout(),
                last_stdout.clone(),
                dir.clone(),
            ));
            let b = tokio::spawn(capture::tee(
                "stderr",
                stderr_pipe,
                dir.join("stderr"),
                tokio::io::stderr(),
                last_stderr.clone(),
                dir.clone(),
            ));
            (a, Some(b))
        }
    };
```

Await `tee_a`, and `tee_b` only when present. Return `merge` in the `Outcome` instead of the
`Merge::Split("not yet decided")` placeholder from Task 1.

A merged run writes only `output`; the `stdout`/`stderr` paths are never opened, so they are
absent rather than empty, which is what the spec requires.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cargo test --test core_test`
Expected: PASS, 9 tests. `long_lines_survive_the_merge_uncorrupted` is the direct regression
guard for F3's splice mechanism.

- [ ] **Step 6: Verify `run` inherits the fix and nothing else regressed**

Run: `cargo test`
Expected: every suite passes except the known `opencode_test` failure from "Before you start".

Any `run_test`/`end_to_end_test` assertion that reads `<capture>/stdout` will now fail when
the test harness happens to give the wrapper one appending destination. Where that happens,
change the assertion to read whichever of `output` or `stdout` exists, rather than forcing a
split — the split was never the contract.

- [ ] **Step 7: Commit**

```bash
git add agent-tools/Cargo.toml agent-tools/src/core.rs agent-tools/tests/core_test.rs
git commit -m "agent-tools: two pipes reordered every wrapped command's output"
```

---

## Task 5: A closed downstream stops forwarding, not the child

F1: `capture.rs:46` discards the forward error, so a downstream that quit goes unnoticed and
the tee runs to completion feeding a reader that no longer exists. Spec, Guaranteed:
"Completeness, or a loud failure. A forwarded stream is never silently short … either failure
is stated on stderr and in the status."

**Files:**
- Modify: `agent-tools/src/capture.rs:18-60`
- Modify: `agent-tools/src/core.rs`
- Modify: `agent-tools/tests/core_test.rs`

- [ ] **Step 1: Write the failing test**

Append to `agent-tools/tests/core_test.rs`:

```rust
#[test]
fn downstream_quitting_neither_kills_the_child_nor_the_call() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");
    // `head -3` exits after three lines; bare, the producer would die of SIGPIPE.
    let script = format!(
        "{} run-core --capture-dir {} -- bash -c 'for i in $(seq 1 5000); do echo line-$i; done; echo done >&2' | head -3",
        bin(),
        cap.display()
    );
    let out = Command::new("bash")
        .args(["-c", &script])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .output()
        .unwrap();

    assert_eq!(
        String::from_utf8_lossy(&out.stdout),
        "line-1\nline-2\nline-3\n",
        "the caller still sees exactly what it asked for"
    );
    let captured = std::fs::read_to_string(cap.join("stdout"))
        .or_else(|_| std::fs::read_to_string(cap.join("output")))
        .unwrap();
    assert!(
        captured.contains("line-5000"),
        "the whole result still lands on disk; got {} bytes",
        captured.len()
    );
    assert_ne!(
        out.status.code(),
        Some(141),
        "nothing died of SIGPIPE: the producer's own status is reported"
    );
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cargo test --test core_test downstream`
Expected: FAIL. Today the forward error is discarded, so the tee keeps writing into a dead
pipe for all 5000 lines. The assertion that fails first depends on timing; the point is that
nothing observes the close.

- [ ] **Step 3: Detect and report the forward close**

In `agent-tools/src/capture.rs`, give `tee` a return value that says what happened, and stop
forwarding once the downstream is gone:

```rust
/// What a tee observed. Every field explains a difference from the bare command.
#[derive(Debug, Default, Clone)]
pub struct TeeOutcome {
    /// The downstream stopped accepting writes; forwarding stopped here.
    pub forward_closed: bool,
    /// Bytes captured after the downstream closed.
    pub post_close_bytes: u64,
}
```

Change the signature to `-> Result<TeeOutcome>` and the loop body:

```rust
    let mut outcome = TeeOutcome::default();
    loop {
        let n = reader.read(&mut buf).await?;
        if n == 0 {
            break;
        }
        let chunk = &buf[..n];
        file.write_all(chunk).await?;

        if outcome.forward_closed {
            outcome.post_close_bytes += n as u64;
        } else if let Err(e) = forward.write_all(chunk).await {
            // A caller that went away is expected — capturing on is the point —
            // but it is a difference from bare and is never inferred silently.
            outcome.forward_closed = true;
            outcome.post_close_bytes += n as u64;
            eprintln!(
                "agent-tools: {stream_name} downstream closed ({e}); still capturing to {}",
                capture_path.display()
            );
        }
        // ... unchanged: last_activity store and first_byte event
    }
    file.flush().await.ok();
    let _ = forward.flush().await;
    Ok(outcome)
```

- [ ] **Step 4: Carry the outcome out of the core**

In `core.rs`, add to `Outcome`:

```rust
    pub forward_closed: bool,
    pub post_close_bytes: u64,
```

and populate them from the awaited tee handles instead of discarding them:

```rust
    let a = tee_a.await.ok().and_then(|r| r.ok()).unwrap_or_default();
    let b = match tee_b {
        Some(h) => h.await.ok().and_then(|r| r.ok()).unwrap_or_default(),
        None => capture::TeeOutcome::default(),
    };
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cargo test --test core_test`
Expected: PASS, 10 tests.

- [ ] **Step 6: Commit**

```bash
git add agent-tools/src/capture.rs agent-tools/src/core.rs agent-tools/tests/core_test.rs
git commit -m "agent-tools: a closed downstream went unnoticed and the tee fed a dead pipe"
```

---

## Task 6: Bound the post-close drain

Spec: "The post-close drain is bounded, and reaching the bound is recorded, or a runaway
producer fills the disk and a capped capture passes for complete. At the bound the read end
closes, so the child sees `SIGPIPE` as bare would; normal operation is uncapped."

F1's measured rate is 400 MB/s, so an unbounded drain is a disk-filling mechanism.

**Files:**
- Modify: `agent-tools/src/capture.rs`
- Modify: `agent-tools/src/core.rs`
- Modify: `agent-tools/tests/core_test.rs`

- [ ] **Step 1: Write the failing test**

Append to `agent-tools/tests/core_test.rs`:

```rust
#[test]
fn post_close_drain_is_bounded_and_the_bound_is_recorded() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");
    // 64 KiB bound, and a producer that will not stop on its own.
    let script = format!(
        "{} run-core --drain-cap-bytes 65536 --capture-dir {} -- bash -c 'yes yes-line' | head -1",
        bin(),
        cap.display()
    );
    let out = Command::new("bash")
        .args(["-c", &script])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .output()
        .unwrap();

    assert_eq!(String::from_utf8_lossy(&out.stdout), "yes-line\n");
    let captured = std::fs::metadata(cap.join("stdout"))
        .or_else(|_| std::fs::metadata(cap.join("output")))
        .unwrap()
        .len();
    assert!(
        captured < 1_000_000,
        "the drain must stop at the bound, not fill the disk; captured {captured} bytes"
    );
    let err = String::from_utf8_lossy(&out.stderr);
    assert!(
        err.contains("drain bound"),
        "reaching the bound is recorded, never silent; stderr was {err:?}"
    );
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cargo test --test core_test post_close`
Expected: FAIL — `unexpected argument '--drain-cap-bytes'`.

- [ ] **Step 3: Add the bound**

In `capture.rs`, add a `drain_cap_bytes: u64` parameter to `tee` (0 meaning uncapped) and a
`drain_capped: bool` to `TeeOutcome`. In the post-close branch:

```rust
        if outcome.forward_closed {
            outcome.post_close_bytes += n as u64;
            if drain_cap_bytes > 0 && outcome.post_close_bytes >= drain_cap_bytes {
                outcome.drain_capped = true;
                eprintln!(
                    "agent-tools: {stream_name} drain bound of {drain_cap_bytes} bytes reached; \
                     dropping the read end so the child sees SIGPIPE as it would bare"
                );
                break;
            }
        }
```

Breaking out of the loop drops `reader`, which closes the read end of the child's pipe. The
child's next write then gets `EPIPE`/`SIGPIPE`, exactly as it would have without the wrapper.

- [ ] **Step 4: Wire the flag**

In `main.rs`, add to the `RunCore` variant:

```rust
        #[arg(long, default_value_t = 0)]
        drain_cap_bytes: u64,
```

Thread it into `core::run_core` as a parameter and on to both `tee` calls. Adding a parameter
to `tee` breaks every call site, so update all of them: the two (or one, when merged) in
`core.rs`, the `run-core` dispatch arm in `main.rs`, the `core::run_core` call in `run.rs`, and
the four inline tokio tests in `capture.rs:113-217`, which pass `0` for uncapped.

`run.rs`'s call becomes:

```rust
    let outcome = match core::run_core(
        &cmd,
        &child_dir,
        core::DEFAULT_DRAIN_CAP_BYTES,
        on_spawn,
        on_reap,
    )
    .await
    {
``` `run` passes the
production default, which is uncapped during normal operation and bounded only after the
downstream has closed — define it in `core.rs`:

```rust
/// Bytes captured after the downstream closed before the read end is dropped.
/// Normal operation never reaches it: it only applies once forwarding has failed.
pub const DEFAULT_DRAIN_CAP_BYTES: u64 = 256 * 1024 * 1024;
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cargo test --test core_test`
Expected: PASS, 11 tests.

- [ ] **Step 6: Commit**

```bash
git add agent-tools/src/capture.rs agent-tools/src/core.rs agent-tools/src/main.rs agent-tools/tests/core_test.rs
git commit -m "agent-tools: an unbounded post-close drain was a disk-filling mechanism"
```

---

## Task 7: A capture that cannot be written never kills the child

F2: `capture.rs:45` propagates the capture-write error out of `tee`; the task dies, nothing
drains the pipe, and the child is killed by `SIGPIPE` — reported as `final(141)`, a plausible
and wrong story. Spec, Guaranteed: "Capture failure never kills the child; forward failure
never stops the capture … a capture that cannot be written is the wrapper's failure, not the
child's."

**Decide one inherited question while you are here.** `run.rs`'s spawn-error `write_meta`
still uses `?`, on the reasoning that a failed spawn has no child exit code to preserve. But
if that write itself fails, the `?` returns the write error and the original spawn failure is
never reported — neither the `anyhow!("spawn ...")` nor the `spawn_failed` event, both of
which sit after it. Two faults at once, and astronomically rare. This task generalizes
"the wrapper's failure, not the child's", so settle it deliberately rather than by omission:
either record-and-continue like the other three sites, or state in a comment why "no child
status to preserve" ends the analysis.

**Files:**
- Modify: `agent-tools/src/capture.rs`
- Modify: `agent-tools/src/core.rs`
- Modify: `agent-tools/src/run.rs`
- Modify: `agent-tools/tests/core_test.rs`

- [ ] **Step 1: Write the failing test**

Append to `agent-tools/tests/core_test.rs`:

```rust
#[test]
fn capture_failure_never_kills_the_child() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");
    std::fs::create_dir_all(&cap).unwrap();
    // Make the capture unwritable: a directory where the capture file must go.
    // Any write to it fails, standing in for the realistic trigger, a full disk.
    std::fs::create_dir_all(cap.join("stdout")).unwrap();
    std::fs::create_dir_all(cap.join("output")).unwrap();

    let out = agent_tools()
        .args(["run-core", "--capture-dir"])
        .arg(&cap)
        .args(["--", "bash", "-c", "for i in $(seq 1 2000); do echo line-$i; done; exit 5"])
        .output()
        .unwrap();

    assert_eq!(
        out.status.code(),
        Some(5),
        "the child's own status is reported, not one the wrapper inflicted"
    );
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(stdout.contains("line-1\n"), "forwarding continues");
    assert!(
        stdout.contains("line-2000\n"),
        "the caller's stream is never cut short by the wrapper's own failure"
    );
    assert!(
        String::from_utf8_lossy(&out.stderr).contains("capture"),
        "the failure is stated on stderr rather than inferred from a wrong exit code"
    );
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cargo test --test core_test capture_failure`
Expected: FAIL — exit code is 141 (`SIGPIPE`), and stdout is cut mid-stream.

- [ ] **Step 3: Isolate the capture from the child**

In `capture.rs`, add `capture_error: Option<String>` to `TeeOutcome`, and replace the
propagating `file.write_all(chunk).await?` with:

```rust
        if outcome.capture_error.is_none() {
            if let Err(e) = file.write_all(chunk).await {
                // The child is not at fault for the wrapper's disk. Stop capturing,
                // keep forwarding, and say so — a silent stop would let `final(0)`
                // sit beside a capture that stopped growing an hour ago.
                outcome.capture_error = Some(e.to_string());
                eprintln!(
                    "agent-tools: capture to {} failed ({e}); forwarding continues, \
                     the capture is incomplete from here",
                    capture_path.display()
                );
            }
        }
```

Opening the capture file must not abort the run either. Replace the `?` on `OpenOptions::open`
with a branch that records the error into the outcome and continues with capture disabled.

Because the loop no longer exits on a capture error, the pipe keeps draining and the child
never sees `SIGPIPE`.

- [ ] **Step 4: Carry the error out of the core**

Add `capture_error: Option<String>` to `core::Outcome`, populated from either tee outcome
(prefer the first non-`None`).

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cargo test --test core_test`
Expected: PASS, 12 tests.

- [ ] **Step 6: Commit**

```bash
git add agent-tools/src/capture.rs agent-tools/src/core.rs agent-tools/tests/core_test.rs
git commit -m "agent-tools: the wrapper's own capture failure killed the child and blamed it"
```

---

## Task 8: Render every difference from bare beside the key

Spec, The record: "Whatever explains a difference from bare is readable beside the key —
downstream closed, drain capped, capture failed, streams merged and on which condition — so
`final(0)` never sits beside a stalled capture."

Until this task the facts exist only inside the core; the agent never sees them.

**Files:**
- Modify: `agent-tools/src/meta.rs:16-28`
- Modify: `agent-tools/src/run.rs`
- Modify: `agent-tools/src/status.rs` (`render`, around :131)
- Modify: `agent-tools/tests/run_facts_test.rs`

- [ ] **Step 1: Write the failing test**

Append to `agent-tools/tests/run_facts_test.rs`:

```rust
#[test]
fn a_capture_failure_is_rendered_beside_the_key() {
    let home = tempfile::tempdir().unwrap();
    let parent = home.path().join("parent");
    std::fs::create_dir_all(&parent).unwrap();

    let out = std::process::Command::new(bin())
        .args(["run", "--desc", "probe", "--", "bash", "-c", "echo hi"])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("AGENT_TOOLS_PARENT_DIR", &parent)
        .env("HOME", home.path())
        .output()
        .unwrap();
    assert_eq!(out.status.code(), Some(0));

    let meta = read_meta(&parent).expect("meta.json written");
    assert!(
        meta.get("merge").is_some(),
        "the merge decision is recorded per capture: {meta}"
    );
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cargo test --test run_facts_test a_capture_failure`
Expected: FAIL — `meta.json` has no `merge` field.

- [ ] **Step 3: Record the facts**

Add to `ChildMeta` in `meta.rs` (all optional so old captures still parse):

```rust
    /// Why the child's streams did or did not share one destination.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub merge: Option<String>,
    /// The downstream stopped accepting writes; forwarding stopped there.
    #[serde(default, skip_serializing_if = "std::ops::Not::not")]
    pub forward_closed: bool,
    /// The post-close drain hit its bound; the capture is short by design.
    #[serde(default, skip_serializing_if = "std::ops::Not::not")]
    pub drain_capped: bool,
    /// The capture could not be written; it is incomplete from that point.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub capture_error: Option<String>,
```

In `run.rs`, copy them off the `Outcome` before the final `write_meta`.

- [ ] **Step 4: Render them**

In `status.rs::render`, append the facts after the existing byte counts, each only when it
applies:

```rust
    if let Some(m) = meta.and_then(|m| m.merge.as_deref()) {
        parts.push(format!("merge={m}"));
    }
    if meta.map(|m| m.forward_closed).unwrap_or(false) {
        parts.push("downstream closed".to_string());
    }
    if meta.map(|m| m.drain_capped).unwrap_or(false) {
        parts.push("drain capped".to_string());
    }
    if let Some(e) = meta.and_then(|m| m.capture_error.as_deref()) {
        parts.push(format!("capture failed: {e}"));
    }
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cargo test --test run_facts_test && cargo test --bin agent-tools status::`
Expected: PASS.

- [ ] **Step 6: Check the prompt coupling**

`status.rs` is prompt-coupled: `scripts/check-prompt-coupling.sh` pins the emitted status
strings against `sys_prompt/alan-default-next.md`. This task adds detail text, not new keys,
so the guard should still pass. Confirm rather than assume:

Run: `bash /root/claude-config-work/scripts/check-prompt-coupling.sh`
Expected: exit 0.

If it fails, the prompt quotes a rendered line whose shape changed. Update the prompt's quoted
line to match the emitter — replacing the stale quote, not adding a second one beside it.

- [ ] **Step 7: Full suite**

Run: `cargo test`
Expected: every suite passes except the known `opencode_test` failure.

- [ ] **Step 8: Commit**

```bash
git add agent-tools/src/meta.rs agent-tools/src/run.rs agent-tools/src/status.rs agent-tools/tests/run_facts_test.rs
git commit -m "agent-tools: final(0) could sit beside a capture that stopped growing"
```

---

## Closing out

- [ ] Update `notes/agent-tools-run-stress-findings.md`: mark F1, F2 and F3 fixed, naming the
      commit that closed each. Leave the reproductions in place — they are the regression
      record.
- [ ] Update the spec's deviations table in
      `docs/superpowers/specs/2026-08-26-agent-tools-run-design.md`: remove the F1, F2 and F3
      rows. Re-check the token budget with
      `agent-tools count-tokens --file docs/superpowers/specs/2026-08-26-agent-tools-run-design.md`
      (it must stay under 4000; it was 3719 when this plan was written).
- [ ] Update `agent-tools/CLAUDE.md` with a short section on the merge rule: that the decision
      is read from the caller's own descriptors, that a merged capture is one `output` file,
      and that `run-core` exists for differential testing and is deliberately not taught by
      the system prompt.
- [ ] Do **not** run `install.sh`, and do not expect a build here to reach live sessions.
      `~/.local/bin/agent-tools` symlinks to the canonical checkout's
      `target/release/agent-tools`, which is a different file from this worktree's. Building
      here cannot break a running session, and cannot fix one either: live sessions pick the
      change up only after this branch merges and the canonical checkout is rebuilt.

## Not in this plan

F4, F5, F6, F7, F8, F10, F11, F13, F14 and F15 are untouched here. They belong to the status,
reporting and pull-path groups and get their own plans. F9 and F12 are accepted differences.
