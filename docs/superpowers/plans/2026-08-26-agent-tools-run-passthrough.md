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

**Do not paste that test's output anywhere.** Its assertion message is `"stdout: {stdout}"`
over a stdout carrying the repository's live `sk-lf-…` Langfuse secret, so a raw `cargo test`
transcript contains a working credential. Filter it if you need to look:
`cargo test --no-fail-fast 2>&1 | sed -E 's/(sk-lf|pk-lf)-[A-Za-z0-9-]+/\1-<REDACTED>/g'`.
The full analysis is in `notes/agent-tools-run-stress-findings.md`, under "Outside the wrapper".

## Mutation testing, and how to restore afterwards

Every task here says to check that its test can fail. Three tests on this branch passed
against the very bug they were written to catch, and a fourth was caught in review before it
shipped — all four with the same shape: the setup never reached the regime the defect lives
in. Reading the test is not evidence. Removing the fix and watching it fail is.

Run the mutation ten times, not once, wherever the regime depends on a timing window, a
buffer boundary or a race. A test that fails 9 times in 10 is telling you the setup sits near
the edge of the regime rather than inside it; move the setup, do not add a retry.

**`git checkout -- <path>` restores to HEAD, which is the state *before* an uncommitted fix.**
Used to undo a mutation while the fix is still uncommitted, it deletes the fix and leaves the
mutation's effect looking like the fix's. Save a copy of the file before mutating and restore
from that, and confirm every restore with `git diff --stat` — an exit status only says the
command ran.

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
/// The `run-core` invocation, in one place. `argv` is the command after `--`;
/// stdio stays the caller's to wire, since where the caller's own two
/// descriptors point is itself under test.
fn run_core_cmd(capture_dir: &Path, argv: &[&str]) -> Command {
    let mut c = agent_tools();
    c.args(["run-core", "--capture-dir"])
        .arg(capture_dir)
        .arg("--")
        .args(argv);
    c
}
```

Task 1's three tests each build that invocation by hand; change them to call `run_core_cmd`
too, so the shape exists in one place rather than four.

Then append the harness:

```rust
/// One side of a differential run: the bytes that reached the caller's own two
/// streams, and the exit status the caller saw. The capture on disk is separate,
/// and outlives the call under the `capture_dir` its caller owns.
struct Captured {
    stdout: Vec<u8>,
    stderr: Vec<u8>,
    code: Option<i32>,
}

/// Run `script` bare, and again through `run-core` capturing under `capture_dir`,
/// and return both. `capture_dir` belongs to the caller, so what landed on disk
/// can be compared against what was forwarded.
fn differential(script: &str, capture_dir: &Path) -> (Captured, Captured) {
    // Both sides get the same environment: the only difference between them must
    // be the wrapper itself.
    let bare = Command::new("bash")
        .args(["-c", script])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .output()
        .unwrap();
    let wrapped = run_core_cmd(capture_dir, &["bash", "-c", script])
        .output()
        .unwrap();
    (
        Captured { stdout: bare.stdout, stderr: bare.stderr, code: bare.status.code() },
        Captured { stdout: wrapped.stdout, stderr: wrapped.stderr, code: wrapped.status.code() },
    )
}

/// Compare on bytes, report as text. The guarantee under test is "unmodified and
/// in order", and `from_utf8_lossy` maps every invalid sequence onto the same
/// replacement character — so comparing rendered strings would accept a wrapper
/// that reordered bytes inside invalid UTF-8.
fn assert_same(script: &str) {
    let tmp = tempfile::tempdir().unwrap();
    let (bare, wrapped) = differential(script, &tmp.path().join("cap"));
    assert_eq!(bare.code, wrapped.code, "exit code differs for {script:?}");
    assert_stream_same("stdout", script, &bare.stdout, &wrapped.stdout);
    assert_stream_same("stderr", script, &bare.stderr, &wrapped.stderr);
}

/// Where the two streams part, in bytes. The renderings cannot always show it:
/// bytes no `String` can hold render the same on both sides.
fn first_difference(bare: &[u8], wrapped: &[u8]) -> String {
    match bare.iter().zip(wrapped).position(|(a, b)| a != b) {
        Some(i) => format!(
            "first difference at byte {i}: bare {:#04x}, wrapped {:#04x}",
            bare[i], wrapped[i]
        ),
        None => format!("equal for {} bytes, then one side ends", bare.len().min(wrapped.len())),
    }
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
    // that, or an inner pipeline behaves differently than it does bare. `head`
    // closes the pipe after two lines and `yes` dies of SIGPIPE, so
    // `PIPESTATUS[0]` is 128 + 13 on both sides.
    assert_same("yes | head -2; exit ${PIPESTATUS[0]}");
}

#[test]
fn core_agrees_with_bare_on_signalled_death_status() {
    let tmp = tempfile::tempdir().unwrap();
    let (bare, wrapped) = differential("kill -TERM $$", &tmp.path().join("cap"));
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

- [ ] **Step 1: Write the failing test**

`core.rs` already has a `#[cfg(test)] mod tests` from Task 1, so a second one is
`E0428: the name 'tests' is defined multiple times`. Add these cases **into** that module,
and add `use std::os::fd::AsRawFd;` to its imports:

```rust
// inside the existing `#[cfg(test)] mod tests`

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
Expected: PASS — the five cases below, plus Task 1's `empty_command_is_an_error_not_a_panic`
already in that module, so `cargo test --bin agent-tools core::` reports 6.

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

`run_core_cmd` already exists from Task 2 and builds the `run-core` invocation; wire the
stdio onto it rather than assembling the argv again. Append to
`agent-tools/tests/core_test.rs`:

```rust
use std::process::Stdio;

/// Run `run-core` with both of its own descriptors on one appending file, which
/// is the shape the merge rule admits and the shape the Claude Code Bash tool has.
/// Run `script` with both of the caller's own descriptors on one appending file:
/// the shape the merge rule admits, and the shape the Claude Code Bash tool has.
/// The returned `TempDir` keeps `cap/` alive so the capture can be inspected.
fn run_core_to_one_appending_file(script: &str) -> (String, tempfile::TempDir) {
    let tmp = tempfile::tempdir().unwrap();
    let sink = tmp.path().join("caller.log");
    let f = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&sink)
        .unwrap();
    let f2 = f.try_clone().unwrap();
    let status = run_core_cmd(&tmp.path().join("cap"), &["bash", "-c", script])
        .stdout(Stdio::from(f))
        .stderr(Stdio::from(f2))
        .status()
        .unwrap();
    assert!(status.code().is_some());
    (std::fs::read_to_string(&sink).unwrap(), tmp)
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
    run_core_cmd(&cap, &["bash", "-c", "echo a; echo b >&2"])
        .output()
        .unwrap();
    assert_eq!(std::fs::read_to_string(cap.join("stdout")).unwrap(), "a\n");
    assert_eq!(std::fs::read_to_string(cap.join("stderr")).unwrap(), "b\n");
    assert!(!cap.join("output").exists());
}

#[test]
fn long_lines_survive_the_merge_uncorrupted() {
    // The splice has to be forced. A long line crosses several of the tee's
    // 8192-byte reads, and the other stream has to land a write between two of
    // them, which only happens while the gap between the child's own two writes
    // stays under roughly 50 us. One command substitution inside the loop is
    // twenty times that by itself, so the long line is built once and the loop
    // runs on builtins alone.
    let script = "long=$(printf 'O%.0s' $(seq 1 12000)); i=0; \
                  while ((i<200)); do echo \"$long\"; echo E >&2; ((i++)); done";
    let (text, _tmp) = run_core_to_one_appending_file(script);
    let (mut long_lines, mut short_lines) = (0, 0);
    for line in text.lines() {
        let first = *line
            .as_bytes()
            .first()
            .expect("an empty line means one write was split in two");
        assert!(
            line.bytes().all(|b| b == first),
            "a line mixing O and E is two writes spliced together"
        );
        if first == b'O' {
            assert_eq!(line.len(), 12000, "a spliced line means the merge failed");
            long_lines += 1;
        } else {
            assert_eq!(line, "E", "a spliced line means the merge failed");
            short_lines += 1;
        }
    }
    assert_eq!((long_lines, short_lines), (200, 200), "every line arrives whole, exactly once");
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cargo test --test core_test merged`
Expected: FAIL — `cap/output` does not exist; both streams still go to two pipes, and
`merged_streams_keep_their_relative_order` fails on interleaving.

This task retires two of the crate's three dead-code warnings: consulting `decide_merge`
gives it a caller and constructs `Merge::Merged`. The third, `field 'merge' is never read`,
survives — writing `Outcome { merge }` is not a read — and retires in Task 8, which carries
the facts into `ChildMeta`. Do not silence any of them with `#[allow]`; a suppression would
hide whether the wiring worked.

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
    // The wrapper's own descriptors: what the caller sees, and so what the
    // decision must be about.
    let merge = decide_merge(libc::STDOUT_FILENO, libc::STDERR_FILENO);

    let mut command = Command::new(&cmd[0]);
    command.args(&cmd[1..]).stdin(Stdio::inherit());

    let merged_reader = if let Merge::Merged(_) = merge {
        // O_CLOEXEC, as `Stdio::piped()` does for the split branch: the child
        // gets fd 1 and fd 2 by `dup2`, which clears the flag, and the copies
        // these came from close on exec. Left inheritable, a descendant of a
        // child that closed its own stdout and stderr would still hold a write
        // end, and the tee would wait on a pipe bare would already have closed.
        let (r, w) = nix::unistd::pipe2(nix::fcntl::OFlag::O_CLOEXEC)
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
    // `command` still owns the write ends it was handed, and the child now has
    // its own. A pipe reports EOF only once the last write end closes, so
    // keeping these would leave the merged tee reading a pipe nobody will ever
    // write to or close — a child that has already exited, and a wrapper that
    // never returns.
    drop(command);
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
Expected: PASS, 10 tests. `long_lines_survive_the_merge_uncorrupted` is the direct regression
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
git add agent-tools/Cargo.toml agent-tools/Cargo.lock agent-tools/src/core.rs agent-tools/tests/core_test.rs
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
/// Many chunks, so the close is seen inside the read loop rather than at the
/// flush.
///
/// A forwarded write's error appears one chunk after the write that caused it:
/// `Blocking::poll_write` hands the chunk to a blocking task and returns `Ok`
/// without waiting, and the next `poll_write` — or the flush — reports it. At
/// 588,895 bytes there is always a next chunk, so the loop is where it lands.
/// `ARRIVES_IN_ONE_CHUNK` covers the case where there is not.
const OVERFLOWS_THE_PIPE: &str = "bash -c 'echo done >&2; seq 1 100000'";

/// The producer is last on purpose: `bash` exits with the status of the last
/// command, so bare it is `seq`'s death by SIGPIPE that the shell reports. Put
/// the `echo` last and bare exits 0 too, and the differential proves nothing.
fn wrapped_into_head(cap: &Path) -> String {
    format!(
        "{} run-core --capture-dir {} -- {OVERFLOWS_THE_PIPE} | head -3",
        bin(),
        cap.display()
    )
}

/// Run `script` under `bash -c` with `pipefail`, so the pipeline reports the
/// producer's status rather than the consumer's — which is the whole question a
/// quitting downstream raises.
fn pipefail(script: &str) -> std::process::Output {
    Command::new("bash")
        .args(["-c", &format!("set -o pipefail; {script}")])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .output()
        .unwrap()
}

#[test]
fn downstream_quitting_neither_kills_the_child_nor_the_call() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");

    let bare = pipefail(&format!("{OVERFLOWS_THE_PIPE} | head -3"));
    assert_eq!(
        bare.status.code(),
        Some(141),
        "bare: the producer dies of SIGPIPE and pipefail reports it"
    );

    let out = pipefail(&wrapped_into_head(&cap));
    assert_eq!(
        String::from_utf8_lossy(&out.stdout),
        "1\n2\n3\n",
        "the caller still sees exactly what it asked for"
    );
    let captured = std::fs::read_to_string(cap.join("stdout"))
        .or_else(|_| std::fs::read_to_string(cap.join("output")))
        .unwrap();
    assert!(
        captured.ends_with("100000\n"),
        "the whole result still lands on disk; got {} bytes",
        captured.len()
    );
    assert_eq!(
        out.status.code(),
        Some(0),
        "nothing died of SIGPIPE: the producer's own status is reported, not 141"
    );
}

**This test does not guard this task, and must not be described as if it does.** It passes
10/10 against the unfixed code and against the real parent commit: a write to a pipe with no
reader returns `EPIPE` at once rather than blocking, so discarding that error costs nothing
any of these three assertions can see. Enlarging the producer did not change that, and the
size was never the reason — the plan's original 48,893-byte producer fails its forward write
5/5, measured. What this test does pin is the "differs from bare by design" clause, against a
measured bare side rather than a bare assertion of `!= 141`, and it will catch a Task 6 drain
bound that fires when it should not. The test that guards Task 5 is Step 1b.
```

- [ ] **Step 1b: Write the test that does guard it**

The observable this task adds is the notice, not the byte counts. Two tests are needed
because the close reaches the tee by two different paths, and the second path is the one the
common shape takes — a small command piped into `head`.

```rust
/// One chunk, one read, so only the flush can see the close.
///
/// The error from a forwarded write appears one chunk after the write that
/// caused it: `Blocking::poll_write` hands the chunk to a blocking task and
/// returns `Ok` without waiting, and the next `poll_write` — or the flush —
/// is what reports it. So a child whose whole output is a single chunk fails
/// nothing in the loop, and `EPIPE` has exactly one place left to appear.
///
/// 2000 bytes is one `write` under `PIPE_BUF`, so it reaches the tee whole in
/// a single read rather than in however many pieces the producer chose. The
/// consumer is gone before any of it exists: `(exit 0)` forks, exits and closes
/// the read end while the child is still sleeping.
const ARRIVES_IN_ONE_CHUNK: &str = r#"bash -c 'sleep 0.5; printf "%01999d\n" 0'"#;

#[test]
fn a_close_seen_only_at_the_flush_is_stated_too() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");
    let out = pipefail(&format!(
        "{} run-core --capture-dir {} -- {ARRIVES_IN_ONE_CHUNK} | (exit 0)",
        bin(),
        cap.display()
    ));

    let err = String::from_utf8_lossy(&out.stderr);
    assert!(
        err.contains("agent-tools: stdout downstream closed"),
        "a close only the flush can see is still stated; stderr was {err:?}"
    );
    let captured = std::fs::read(cap.join("stdout"))
        .or_else(|_| std::fs::read(cap.join("output")))
        .unwrap();
    assert_eq!(
        captured.len(),
        2000,
        "and the capture still holds everything the child wrote"
    );
}

#[test]
fn a_closed_downstream_is_stated_on_stderr() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");

    let out = pipefail(&wrapped_into_head(&cap));

    let err = String::from_utf8_lossy(&out.stderr);
    let stated = err
        .lines()
        .find(|l| l.starts_with("agent-tools: stdout downstream closed"))
        .unwrap_or_else(|| panic!("nothing said the forwarding stopped; stderr was {err:?}"));
    assert!(
        stated.contains(&cap.join("stdout").display().to_string()),
        "the notice names where the output is still going; got {stated:?}"
    );
    assert_eq!(
        err.lines()
            .filter(|l| l.starts_with("agent-tools: stdout downstream closed"))
            .count(),
        1,
        "said once, not once per chunk; stderr was {err:?}"
    );
}
```

The "said once" filter matches the whole notice prefix rather than any `agent-tools:` line,
or Task 6's drain notice would count toward it and this assertion would start failing for a
reason that has nothing to do with it.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cargo test --test core_test downstream` and `cargo test --test core_test a_close`
Expected: both `_is_stated_` tests FAIL — nothing writes a notice today. Expected:
`downstream_quitting_neither_kills_the_child_nor_the_call` **passes**, because it does not
guard this task; that is stated above and is not a reason to skip the other two.

Run each of them ten times, not once. `a_close_seen_only_at_the_flush_is_stated_too` depends
on the child's whole output reaching the tee in a single read, which is an argument about
`PIPE_BUF` and the tee's 8192-byte buffer rather than a documented contract, so 10/10 is the
evidence that it holds. Confirm the regime as well as the result: with only the loop fixed and
the flush still discarded, this test must fail while `_is_stated_on_stderr` passes. If both
pass, the producer is landing in two chunks and the test is guarding nothing.

**Never `eprintln!` from inside the tee.** It panics when its own write fails, and the
stream that just closed can be the one it writes to: `cmd 2>&1 | head -3` puts both of the
caller's descriptors on the pipe `head` drops, which is exactly the shape the merge rule
admits. Measured with `eprintln!` in place — rc `141`, capture 32,773 B — against a plain
`write_all` — rc `0`, capture 588,900 B: the panic kills the tee, the read end closes, and the
child dies of SIGPIPE, which is both of the failures this task exists to prevent. Use a helper
that formats once and writes once to `std::io::stderr()`, discarding the error; that is also
atomic under `PIPE_BUF`, where `write_fmt` emits a syscall per fragment. Tasks 6 and 7 print
from the same place and inherit this rule.

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
    pub bytes_since_close_detected: u64,
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
            outcome.bytes_since_close_detected += n as u64;
        } else if let Err(e) = forward.write_all(chunk).await {
            // A caller that went away is expected — capturing on is the point —
            // but it is a difference from bare and is never inferred silently.
            outcome.forward_closed = true;
            outcome.bytes_since_close_detected += n as u64;
            state_forward_closed(stream_name, &e, &capture_path);
        }
        // ... unchanged: last_activity store and first_byte event
    }
    file.flush().await.ok();
    // The same error, at the second write site. A forwarded write's error
    // surfaces one chunk after the write that caused it: `Blocking::poll_write`
    // hands the chunk to a blocking task and returns `Ok` without waiting, and
    // the next `poll_write` — or this flush — is what reports it. The last chunk
    // has no next write, so its error can appear nowhere but here; and a child
    // whose whole output arrives in one 8192-byte read has no earlier chunk
    // either. Discarded, the caller's stream is silently short by whatever was
    // still in flight and the outcome says forwarding was fine.
    match forward.flush().await {
        Err(e) if !outcome.forward_closed => {
            outcome.forward_closed = true;
            state_forward_closed(stream_name, &e, &capture_path);
        }
        // Already reported in the loop, or nothing to report.
        _ => {}
    }
    Ok(outcome)
```

and the helper the loop calls:

```rust
/// Say once, on stderr, that forwarding stopped and capturing did not.
///
/// Not `eprintln!`: that panics when the write fails, and the stream that just
/// closed can be this one — `cmd 2>&1 | head -3` puts both of the caller's
/// descriptors on the pipe `head` drops, which is exactly the shape the merge
/// rule admits. A panic there would kill the tee, stopping the capture the
/// message is about, and the outcome would come back saying nothing happened.
///
/// Formatted first and written once, so the notice cannot be spliced by the
/// other stream's tee mid-line: one `write` under `PIPE_BUF` is atomic, while
/// `write_fmt` emits a syscall per fragment.
fn state_forward_closed(stream_name: &str, err: &std::io::Error, capture_path: &std::path::Path) {
    use std::io::Write as _;
    let msg = format!(
        "agent-tools: {stream_name} downstream closed ({err}); still capturing to {}\n",
        capture_path.display()
    );
    let _ = std::io::stderr().write_all(msg.as_bytes());
}
```

- [ ] **Step 4: Carry the outcome out of the core**

In `core.rs`, add to `Outcome`:

```rust
    /// A downstream stopped accepting writes, on either stream, and forwarding
    /// to it stopped. The child ran on and the capture kept growing.
    pub forward_closed: bool,
```

`bytes_since_close_detected` stays on `TeeOutcome`, where Task 6 compares it against the drain bound,
and does not go on `Outcome`: no task in this plan reads it there, and it is not what its
name suggests — it counts from the chunk whose forward write returned the error, which is two
of the tee's 8192-byte chunks after the real close, and it adds that whole chunk even though
`write_all` may have accepted a prefix of it. Say that where it is defined rather than leaving
a later reader to infer a precision it does not have.

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
Expected: PASS, 14 tests.

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
/// Far more than the bound, and it ends on its own.
///
/// Ending on its own is the load-bearing half. `yes yes-line` never stops, so
/// against an implementation that adds the flag but not the `break` the test
/// does not fail — it hangs, writing at F1's measured 400 MB/s into the temp
/// dir until the disk is gone. A test for a disk-filling bug must not be one.
/// 10 MiB overruns a 64 KiB bound by 160x and takes about 25 ms either way.
const OVERRUNS_THE_BOUND: &str = "bash -c 'yes yes-line | head -c 10485760'";

#[test]
fn post_close_drain_is_bounded_and_the_bound_is_recorded() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");
    let out = pipefail(&format!(
        "{} run-core --drain-cap-bytes 65536 --capture-dir {} -- {OVERRUNS_THE_BOUND} | head -1",
        bin(),
        cap.display()
    ));

    assert_eq!(String::from_utf8_lossy(&out.stdout), "yes-line\n");
    // `stdout`, not a fallback to `output`: `Command::output()` hands the outer
    // bash two independent pipes, so `decide_merge` sees two inodes and always
    // splits. A hedge here would be a branch that cannot run.
    let captured = std::fs::metadata(cap.join("stdout")).unwrap().len();
    // Generous but not vacuous. At most the 64 KiB pipe buffer got through
    // before the consumer quit, the counter starts up to two 8192-byte reads
    // after that, and the bound then allows 64 KiB more: about 145 KiB worst
    // case. 300 KB catches a bound that fires at twice its size; 10 MB, the
    // producer's own length, would only catch one that never fires at all.
    assert!(
        captured < 300_000,
        "the drain stops at the bound, not at the producer's end; \
         captured {captured} bytes of 10485760"
    );
    let err = String::from_utf8_lossy(&out.stderr);
    // Position, not presence: the `agent-tools:` prefix begins a line is what
    // the system prompt teaches, so nothing a child writes can forge it.
    assert!(
        err.lines().any(|l| l.starts_with("agent-tools: stdout drain bound")),
        "reaching the bound is recorded, never silent; stderr was {err:?}"
    );
    assert_eq!(
        out.status.code(),
        Some(141),
        "at the bound the read end closes, so the child sees SIGPIPE as it would bare"
    );
}
```

`pipefail` is Task 5's helper, so the pipeline reports `run-core`'s status rather than
`head`'s. Task 5's own test asserts the opposite exit code on a similar shape and both are
right: there the whole 588 KB is under the bound and nothing is ever cut off, here the bound
is deliberately set below the producer and cutting the child off is the behaviour under
test.

- [ ] **Step 2: Run the test to verify it fails**

Run: `cargo test --test core_test post_close`
Expected: FAIL — `unexpected argument '--drain-cap-bytes'`.

Once the flag parses, check the test can still fail for the right reason: delete the `break`
alone, rebuild, and re-run. It must fail on the byte count within a second or two. If it
hangs instead, the producer is unbounded and the test is worthless — fix the producer, not
the timeout.

- [ ] **Step 3: Add the bound**

First give the tee one place to speak from. Task 5 shipped `state_forward_closed`, a helper
specialized to one message; this task and Task 7 both need to say something else, and the
reason the tee may not use `eprintln!` should live in one place rather than three. In
`capture.rs`, split it:

```rust
/// Say something once on the caller's stderr, from inside a tee.
///
/// Not `eprintln!`: that panics when the write fails, and the stream that just
/// closed can be this one — `cmd 2>&1 | head -3` puts both of the caller's
/// descriptors on the pipe `head` drops, which is exactly the shape the merge
/// rule admits. A panic there would kill the tee, stopping the capture the
/// message is about, and the outcome would come back saying nothing happened.
///
/// Formatted by the caller and written once, so a notice cannot be spliced by
/// the other stream's tee mid-line: one `write` under `PIPE_BUF` is atomic,
/// while `write_fmt` emits a syscall per fragment. Callers pass the trailing
/// newline; nothing here adds one, because a second write would break that.
fn state(msg: &str) {
    use std::io::Write as _;
    let _ = std::io::stderr().write_all(msg.as_bytes());
}

/// Say that forwarding stopped and capturing did not.
fn state_forward_closed(stream_name: &str, err: &std::io::Error, capture_path: &std::path::Path) {
    state(&format!(
        "agent-tools: {stream_name} downstream closed ({err}); still capturing to {}\n",
        capture_path.display()
    ));
}
```

Then add a `drain_cap_bytes: u64` parameter to `tee` (0 meaning uncapped) and a
`drain_capped: bool` to `TeeOutcome`. In the post-close branch:

```rust
        if outcome.forward_closed {
            outcome.bytes_since_close_detected += n as u64;
            if drain_cap_bytes > 0 && outcome.bytes_since_close_detected >= drain_cap_bytes {
                outcome.drain_capped = true;
                state(&format!(
                    "agent-tools: {stream_name} drain bound of {drain_cap_bytes} bytes \
                     reached; dropping the read end so the child sees SIGPIPE as bare\n"
                ));
                break;
            }
        }
```

Breaking out of the loop drops `reader`, which closes the read end of the child's pipe. The
child's next write then gets `EPIPE`/`SIGPIPE`, exactly as it would have without the wrapper.

- [ ] **Step 4: Wire the flag**

Define the production default in `core.rs`:

```rust
/// Bytes captured after the downstream closed before the read end is dropped.
/// Normal operation never reaches it: it only applies once forwarding has failed.
pub const DEFAULT_DRAIN_CAP_BYTES: u64 = 256 * 1024 * 1024;
```

In `main.rs`, add to the `RunCore` variant:

```rust
        #[arg(long, default_value_t = core::DEFAULT_DRAIN_CAP_BYTES)]
        drain_cap_bytes: u64,
```

**The default is the production one, not 0.** The spec makes `run-core` agree with `run`
"byte for byte on both forwarded streams and on the exit code", and a `run-core` that drained
without a bound while `run` capped at 256 MiB would disagree with it about exactly the case
this task adds — the child that gets `SIGPIPE` at the bound. Only the test names a different
bound, and it names it explicitly. Task 5's test drains 588 KB, far under 256 MiB, so it is
unaffected.

Then give `run_core` the parameter, ahead of the callbacks:

```rust
pub async fn run_core<S, R>(
    cmd: &[String],
    capture_dir: &Path,
    drain_cap_bytes: u64,
    on_spawn: S,
    on_reap: R,
) -> Result<Outcome, CoreError>
```

Adding a parameter to `tee` breaks every call site, so update all of them: the three in
`core.rs` — `:221` on the merged arm, `:247` and `:255` on the split arm, of which only one
arm runs; the `run-core` dispatch arm at
`main.rs:409-418`; the `core::run_core` call in `run.rs`; and the three inline tokio tests in
`capture.rs` that call `tee` — `tee_writes_capture_file`, `tee_forwards_through_to_writer`
and `tee_records_first_byte_event` — which pass `0` for uncapped. The fourth test in that
module, `silence_watcher_emits_event_after_threshold`, drives `watch_silence` and does not
change.

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
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cargo test --test core_test`
Expected: PASS, 15 tests. (14 before this task: Task 5 landed three, not one.)

- [ ] **Step 6: Commit**

```bash
git add agent-tools/src/capture.rs agent-tools/src/core.rs agent-tools/src/main.rs agent-tools/tests/core_test.rs
git commit -m "agent-tools: an unbounded post-close drain was a disk-filling mechanism"
```

---

## Task 7: A capture that cannot be written never kills the child

F2: the capture write at `capture.rs:60` propagates its error out of `tee`; the task dies, nothing
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
/// The child F2 was measured against: enough output to keep writing well past
/// the first failed capture write, and an exit code nothing else would produce.
const TALKS_THEN_EXITS_5: [&str; 3] =
    ["bash", "-c", "for i in $(seq 1 2000); do echo line-$i; done; exit 5"];

#[test]
fn capture_failure_never_kills_the_child() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");
    std::fs::create_dir_all(&cap).unwrap();
    // `/dev/full` opens and then fails every write with ENOSPC, which is F2's
    // own trigger — a full disk — reached without privileges or a mount. A
    // directory in the same place would fail the *open* instead, and the open
    // is a different branch from the one that kills the child; it gets its own
    // test below. Two shapes are symlinked because the merge decision picks the
    // capture name, and `stderr` deliberately is not, so the test can tell one
    // failed stream from a wholly broken run.
    std::os::unix::fs::symlink("/dev/full", cap.join("stdout")).unwrap();
    std::os::unix::fs::symlink("/dev/full", cap.join("output")).unwrap();

    let out = run_core_cmd(&cap, &TALKS_THEN_EXITS_5).output().unwrap();

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
    let err = String::from_utf8_lossy(&out.stderr);
    // Position, not presence, the same way the forward-close tests check it:
    // the prefix beginning a line is the contract, not the substring.
    assert_eq!(
        err.lines()
            .filter(|l| l.starts_with("agent-tools: capture to"))
            .count(),
        1,
        "stated once on stderr, not once per chunk and not inferred from a wrong \
         exit code; stderr was {err:?}"
    );
}

#[test]
fn a_capture_that_cannot_be_opened_is_stated_and_not_fatal() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");
    std::fs::create_dir_all(&cap).unwrap();
    // A directory where the capture file goes: the open fails with EISDIR and
    // the loop never runs, so this reaches the branch the test above cannot.
    std::fs::create_dir_all(cap.join("stdout")).unwrap();
    std::fs::create_dir_all(cap.join("output")).unwrap();

    let out = run_core_cmd(&cap, &TALKS_THEN_EXITS_5).output().unwrap();

    assert_eq!(out.status.code(), Some(5));
    assert!(String::from_utf8_lossy(&out.stdout).contains("line-2000\n"));
    let err = String::from_utf8_lossy(&out.stderr);
    assert!(
        err.lines().any(|l| l.starts_with("agent-tools: capture to")),
        "an open that failed is stated too; stderr was {err:?}"
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
                state(&format!(
                    "agent-tools: capture to {} failed ({e}); forwarding continues, \
                     the capture is incomplete from here\n",
                    capture_path.display()
                ));
            }
        }
```

Opening the capture file must not abort the run either. Replace the `?` on `OpenOptions::open`
with a branch that records the error into the outcome, states it through the same message,
and continues with capture disabled — `a_capture_that_cannot_be_opened_is_stated_and_not_fatal`
covers only this branch, and the loop's message is never reached when the open is what failed.

**And the capture's flush, one line above the forward's.** `capture.rs:87` is
`file.flush().await.ok()`, and `tokio::fs::File` has the same mechanism the forward side did:
`fs/file.rs:743-770` returns `Ok(n)` after spawning the blocking write, and `:1096-1108`
reports that write's error at the flush. So the last chunk's capture error appears nowhere
else, and a child whose whole output is one 8192-byte read has no earlier chunk either.
Measured today, capture symlinked to `/dev/full`: a 2000-byte child gives exit 0, nothing on
stderr, an empty capture, and `TeeOutcome::default()` — a clean outcome for a capture that
never happened, which is "a capture never silently stops growing" failing in the most ordinary
shape there is. Handle it the same way as the write:

```rust
    match file.flush().await {
        Err(e) if outcome.capture_error.is_none() => {
            outcome.capture_error = Some(e.to_string());
            state(&format!(
                "agent-tools: capture to {} failed at the flush ({e}); the capture is \
                 short by whatever was still in flight\n",
                capture_path.display()
            ));
        }
        // Already reported in the loop, or nothing to report.
        _ => {}
    }
```

Both of this task's tests above use `TALKS_THEN_EXITS_5`, which is 18,893 bytes — three
reads, so it lands in the loop and would ship without noticing this. Add the single-chunk
case:

```rust
#[test]
fn a_capture_that_fails_only_at_the_flush_is_stated_too() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");
    std::fs::create_dir_all(&cap).unwrap();
    std::os::unix::fs::symlink("/dev/full", cap.join("stdout")).unwrap();
    std::os::unix::fs::symlink("/dev/full", cap.join("output")).unwrap();

    // 2000 bytes is one write under `PIPE_BUF`, so the tee reads it whole and
    // there is no second chunk for the first chunk's error to surface at.
    let out = run_core_cmd(&cap, &["bash", "-c", r#"printf "%01999d\n" 0; exit 5"#])
        .output()
        .unwrap();

    assert_eq!(out.status.code(), Some(5));
    assert_eq!(out.stdout.len(), 2000, "the caller still gets everything");
    let err = String::from_utf8_lossy(&out.stderr);
    assert!(
        err.lines().any(|l| l.starts_with("agent-tools: capture to")),
        "a capture that failed with nothing left to write is still stated; stderr was {err:?}"
    );
}
```

Mutate it: restore `file.flush().await.ok()` and confirm this test fails while the other two
pass. If all three pass, the producer is landing in more than one read.

Because the loop no longer exits on a capture error, the pipe keeps draining and the child
never sees `SIGPIPE`.

**Now that there are two of them, extract both.** The forward side already has this shape —
try the write, and on failure record it once, say so once, and keep going — and this task
adds the capture side's mirror image. Two inline `if`s doing the same thing with different
nouns, in a loop that also carries the drain bound and the first-byte event, is where this
function stops being readable. One helper per side, named for what it protects, called from a
loop body that reads as: capture it, forward it, count it, say it started. Do not generalise
the two into one — they differ in what failure means, and collapsing that is how "capture
failure never kills the child" gets lost.

- [ ] **Step 4: Carry the error out of the core**

Add `capture_error: Option<String>` to `core::Outcome`, populated from either tee outcome
(prefer the first non-`None`).

**And stop swallowing a tee that died.** `core.rs:303`/`:305` await the handles as
`.ok().and_then(|r| r.ok()).unwrap_or_default()`. The `.ok()` discards a `JoinError` — the
tee **panicked** — and `unwrap_or_default()` then reports `forward_closed: false` and no
capture error: a clean outcome for a capture that stopped dead. Nothing else in this plan
touches it, and it is the one failure the "loud failure" clause cannot tolerate, so close it
here. A tee that panicked or errored sets `capture_error` to what went wrong instead of
defaulting:

```rust
    fn tee_outcome(
        joined: Result<Result<capture::TeeOutcome>, tokio::task::JoinError>,
    ) -> capture::TeeOutcome {
        match joined {
            Ok(Ok(o)) => o,
            // The tee stopped without finishing. It owns the capture, so the
            // capture stopped with it, and the only honest outcome says so.
            Ok(Err(e)) => capture::TeeOutcome {
                capture_error: Some(format!("{e:#}")),
                ..Default::default()
            },
            Err(e) => capture::TeeOutcome {
                capture_error: Some(format!("tee task died: {e}")),
                ..Default::default()
            },
        }
    }
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cargo test --test core_test`
Expected: PASS, 18 tests.

- [ ] **Step 6: Commit**

```bash
git add agent-tools/src/capture.rs agent-tools/src/core.rs agent-tools/src/run.rs agent-tools/tests/core_test.rs
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
fn the_merge_condition_is_recorded_beside_the_capture() {
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

Add a second test, for the two cases stderr cannot reach at all:

```rust
#[test]
fn a_close_that_stderr_could_not_carry_is_still_in_the_record() {
    let home = tempfile::tempdir().unwrap();
    let parent = home.path().join("parent");
    std::fs::create_dir_all(&parent).unwrap();

    // `2>&1` makes both of the wrapper's descriptors the same pipe, which the
    // merge rule admits, so the notice `capture::state` writes goes into the
    // pipe `head` just dropped and no reader ever sees it. Same for a split
    // run whose stderr is the stream that closed. The record is the only place
    // either can appear, which is why the spec asks for stderr *and* the status.
    let script = format!(
        "{} run --desc probe -- bash -c 'seq 1 100000' 2>&1 | head -3",
        bin()
    );
    let out = std::process::Command::new("bash")
        .args(["-c", &script])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("AGENT_TOOLS_PARENT_DIR", &parent)
        .env("HOME", home.path())
        .output()
        .unwrap();
    assert_eq!(String::from_utf8_lossy(&out.stdout), "1\n2\n3\n");

    let meta = read_meta(&parent).expect("meta.json written");
    assert_eq!(
        meta.get("forward_closed").and_then(|v| v.as_bool()),
        Some(true),
        "the record carries what stderr could not: {meta}"
    );
}
```

`seq 1 100000` is 588,895 bytes — many reads, so the close is seen in the loop and does not
depend on the flush path. It is also far under `DEFAULT_DRAIN_CAP_BYTES`, so Task 6's bound
never fires here and the child still exits 0.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cargo test --test run_facts_test the_merge_condition` and
`cargo test --test run_facts_test a_close_that_stderr`
Expected: FAIL — `meta.json` has neither a `merge` nor a `forward_closed` field.

- [ ] **Step 3: Record the facts**

First give `core::Merge` a recorded form. It is an enum of two `&'static str` reasons and
`meta.json` holds strings, so add to `core.rs`:

```rust
impl Merge {
    /// The condition that decided it, for the record. Which way it was decided
    /// is not carried with it: `status::Capture` already reads that off disk
    /// from how many capture files exist, and two records of one fact drift.
    pub fn condition(&self) -> &'static str {
        match *self {
            Merge::Merged(why) | Merge::Split(why) => why,
        }
    }
}
```

Add to `ChildMeta` in `meta.rs` (all optional so old captures still parse):

```rust
    /// The condition that decided whether the child's streams shared one
    /// destination. Whether they did is `status::Capture`, off the disk.
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

In `run.rs`, copy them off the `Outcome` in the same block that sets `drained_at`, before
that final `write_meta`, so one write carries all of them:

```rust
        m.merge = Some(outcome.merge.condition().to_string());
        m.forward_closed = outcome.forward_closed;
        m.drain_capped = outcome.drain_capped;
        m.capture_error = outcome.capture_error.clone();
```

That write is best-effort like the others — `record_meta_write` already logs and discards its
error, and these facts must not decide the caller's exit code either.

- [ ] **Step 4: Render them**

`status.rs::render` builds one `format!` and has no list to push onto, so build the segment
and splice it in. Add before the final `format!` at `status.rs:197`:

```rust
    // Everything that explains a difference from bare, so `final(0)` never sits
    // beside a capture that stopped growing an hour ago. Empty on a clean run,
    // which is nearly every run: these lines land in every tool result, and a
    // note that is always there stops being read.
    let mut notes: Vec<String> = Vec::new();
    // Only a split is the difference. Bare had one destination and one
    // interleaving; splitting is what loses them, and merging is what restores
    // them. `s.capture` is where the shape is known — it is read off the files
    // that exist — and `meta.merge` supplies only the condition.
    if let (Capture::Split { .. }, Some(why)) =
        (&s.capture, s.meta.as_ref().and_then(|m| m.merge.as_deref()))
    {
        notes.push(format!("streams split: {why}"));
    }
    if s.meta.as_ref().is_some_and(|m| m.forward_closed) {
        notes.push("downstream closed".to_string());
    }
    if s.meta.as_ref().is_some_and(|m| m.drain_capped) {
        notes.push("drain capped".to_string());
    }
    if let Some(e) = s.meta.as_ref().and_then(|m| m.capture_error.as_deref()) {
        notes.push(format!("capture failed: {e}"));
    }
    let notes = if notes.is_empty() {
        String::new()
    } else {
        format!(" [{}]", notes.join("; "))
    };
```

and change the returned line to carry it, between the byte counts and the stat problems:

```rust
    format!("{name} [{}] pid {pid}, {age}, {bytes}{notes}{problems} -> {paths}", s.key)
```

- [ ] **Step 4b: Test the rendering, not just the record**

Step 1 pins the fact reaching `meta.json`; nothing yet pins it reaching a line, which is what
this task is named for. Add to `status.rs`'s inline tests, beside the others that call
`render`:

```rust
    #[test]
    fn a_difference_from_bare_is_readable_beside_the_key() {
        let d = TempDir::new().unwrap();
        let mut m = base();
        m.merge = Some("different destinations".into());
        m.forward_closed = true;
        m.capture_error = Some("No space left on device".into());
        write(&d, &m);
        std::fs::write(d.path().join("stdout"), b"x").unwrap();

        let now = Utc::now();
        let line = render(d.path(), &derive(d.path(), now), now);
        assert!(line.contains("streams split: different destinations"), "line: {line}");
        assert!(line.contains("downstream closed"), "line: {line}");
        assert!(line.contains("capture failed: No space left on device"), "line: {line}");
    }

    #[test]
    fn a_clean_run_carries_no_notes() {
        // Nearly every run is this one, and these lines land in every tool
        // result: a note that is always there stops being read.
        let d = TempDir::new().unwrap();
        let mut m = base();
        m.merge = Some("both appending, same file".into());
        write(&d, &m);
        std::fs::write(d.path().join("output"), b"x").unwrap();

        let now = Utc::now();
        let line = render(d.path(), &derive(d.path(), now), now);
        assert!(!line.contains("merge"), "a merged run explains nothing: {line}");
        assert!(!line.contains('['), "no bracketed notes at all: {line}");
    }
```

The second test's `[` assertion is deliberately blunt and will fail if a future note is added
unconditionally. That is the point; `base()` produces no `stat_errors`, so the only bracket a
clean line could carry is the status key — check that assumption when you write it, and if
the key does bracket, narrow the assertion to the notes segment rather than deleting it.

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

## Task 9: The prompt promises more than the wrapper delivers

The spec's "Not achievable" tier ends: "The prompt must stop promising otherwise." Nothing
before this task does that, and Tasks 5-7 make the promise worse rather than better, because
they add wrapper diagnostics on a stream the prompt says the wrapper never writes to.

What `sys_prompt/alan-default-next.md` claims today, in the `agent-tools run` bullet list:

> The wrapper passes the child's stdout and stderr through byte-for-byte and propagates the
> child's exit code. Pipelines, redirections, `2>&1`, exit-status checks, and downstream
> filters behave exactly as if you had run the bare command. The wrapper itself writes
> nothing to stdout or stderr.

Three of those clauses are false. Downstream filters do **not** behave as bare: a quitting
downstream stops neither the child nor the call, and `pipefail` reports the producer's own
status rather than `141` — that is the tool's purpose, not a defect. The wrapper writes to
stderr whenever a stream or capture fails. And `2>&1` is not merely honoured, it is a no-op
wherever the caller's own descriptors already reach one destination.

An agent that believes the current text will misread an exit code and misattribute a
diagnostic line to its own command.

**Files:**
- Modify: `sys_prompt/alan-default-next.md`
- Modify: `agent-tools/CLAUDE.md` (the prompt-coupled strings table)

- [ ] **Step 1: Replace the claim**

Substitute this for the bullet quoted above. It replaces `sys_prompt/alan-default-next.md:170`
in full — one bullet in, one bullet out, never a second one added beside it.

**Write it as a single line, indented `  - ` like its neighbours.** Claude Code loads this
file as text rather than rendered markdown, so the wrapping below would appear verbatim in
the prompt, and every other bullet in that list is one unwrapped line. The blockquote and
line breaks here are this document's formatting, not the file's.

> - The wrapper forwards the child's bytes unchanged, in order within each stream, and exits
>   with the child's own code — `128 + signum` if the child was signalled, since the wrapper
>   cannot die of its child's signal. Stdin is inherited. Where the caller's stdout and
>   stderr already reach one destination, the child gets one too, so ordinary calls keep
>   their interleaving and `2>&1` is a no-op. Three deliberate differences: a downstream that
>   quits stops neither the child nor the call, so `… | head -3` prints three lines while the
>   whole result still lands on disk, and `pipefail` reports the producer's own status rather
>   than `141`; the wrapper is a real process, so `pgrep -f` matches it and it outlives
>   signals its child ignores; and it writes its own diagnostics to stderr, always prefixed
>   `agent-tools:`, when a stream or capture fails. `isatty` is false under the wrapper.

- [ ] **Step 2: Make the stderr prefix true**

The text above promises every wrapper diagnostic begins `agent-tools:`. Check each
diagnostic Tasks 5, 6 and 7 added actually carries it, and fix any that does not. A promise
the emitters do not keep is worse than the claim it replaced.

Run: `grep -rn "eprintln!\\|stderr()" agent-tools/src/`
The tee does not use `eprintln!` — it writes through `capture::state`, for the reason given in
Task 5 — so grepping only for the macro would miss every diagnostic that matters here.

The promise is scoped to a wrapped run, so judge each hit by whether it can reach the caller's
stderr *while a child is running*: `capture::state` and its callers can, and must carry the
prefix. `main.rs`'s argument-parsing and dispatch errors cannot — no child exists yet — and
are out of scope, though they already read `agent-tools <subcommand>:` and should stay that
way. Anything else that prints during a run either gets the prefix or stops printing.

- [ ] **Step 3: Record the coupling**

`agent-tools/CLAUDE.md` has a table of strings emitted by the binary and quoted in the system
prompt, so drift between them can be caught. The `agent-tools:` diagnostic prefix is now such
a string. Add a row naming the emitters (`capture.rs`, `core.rs`), the prompt location, and
what breaks if they drift: the agent stops being able to tell the wrapper's diagnostics from
its own command's output.

- [ ] **Step 4: Verify**

Run: `bash scripts/check-prompt-coupling.sh`
Expected: exit 0. This script pins the status-key literals and headers, not this bullet, so
it should pass unchanged — confirm that rather than assume it.

Run: `agent-tools count-tokens --file sys_prompt/alan-default-next.md`
Expected: the file is a system prompt loaded on every session; note the before and after so
the change's cost is visible.

- [ ] **Step 5: Commit**

```bash
git add sys_prompt/alan-default-next.md agent-tools/CLAUDE.md
git commit -m "prompt: it promised bare-equivalence the wrapper never had"
```

---

## Closing out

- [ ] Update `notes/agent-tools-run-stress-findings.md`: mark F1, F2 and F3 fixed, naming the
      commit that closed each. Leave the reproductions in place — they are the regression
      record.
- [ ] Update the spec's deviations table in
      `docs/superpowers/specs/2026-08-26-agent-tools-run-design.md`: remove the F1 and F2
      rows, and correct the count. F3's row is already gone, removed when Task 4 closed it —
      close each finding as it lands rather than in a batch, so the spec is never a document
      that describes a defect the branch has already fixed. The count in the sentence above
      the table goes from eleven to nine, and it must keep adding up to fifteen: nine still
      departing, three fixed by this branch (F1, F2, F3), two accepted differences (F9, F12),
      and F10 breaking no clause. Re-check the token budget with
      `agent-tools count-tokens --file docs/superpowers/specs/2026-08-26-agent-tools-run-design.md`
      (it must stay under 4000; it was 3855 after the deviations table was reduced to a
      clause-to-finding map, so the headroom is about 145 tokens).
- [ ] Document the two things this branch added to the binary's public surface, neither of
      which appears in any `CLAUDE.md` today — checked with
      `grep -rn "run-core" CLAUDE.md agent-tools/CLAUDE.md`, which returns nothing:
    - The root `CLAUDE.md` subcommand list gains `agent-tools run-core --capture-dir <dir>
      [--drain-cap-bytes N] -- <cmd>`: the same run without the scope, ledger or hooks,
      existing so passthrough can be tested against a real process. Say that root resolution
      binds it like every other subcommand, and that the prompt deliberately does not teach it.
    - `agent-tools/CLAUDE.md` gains the merge rule — when the child's two streams share one
      destination, why the enumeration is short, and that `core::Merge` and `status::Capture`
      are one fact recorded twice, so a change to what either arm opens has to move both.
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
