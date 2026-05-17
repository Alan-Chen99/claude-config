# agent-tools count-tokens Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `agent-tools count-tokens [--model MODEL] [--file PATH] [TEXT]` — a one-shot CLI that reports the Anthropic `count_tokens` API result for a piece of text, composable in shell pipelines.

**Architecture:** Thin Rust dispatcher (`Cmd::CountTokens { args: Vec<String> }`) in the existing `agent-tools` binary forwards args via `uv_run` to a new Python module `claude_config.count_tokens`. The Python module uses `argparse` for input resolution (positional > `--file` > stdin) and calls `anthropic.Anthropic(api_key=...).messages.count_tokens(...)` with the key from `/repos/claude-config/.env` (loaded by `claude_config.config.load()`). Output is a bare integer + newline to stdout. Errors propagate loudly (no swallow).

**Tech Stack:**
- Rust crate at `agent-tools/` with `clap` (already a dep). No new Rust deps.
- Python module under `src/claude_config/`. `anthropic`, `python-dotenv`, `argparse` (stdlib) — `anthropic` and `python-dotenv` already in `pyproject.toml`.
- Tests via `cargo test` in `agent-tools/`. Tests subprocess the binary at `env!("CARGO_BIN_EXE_agent-tools")` and set `CLAUDE_CONFIG_ROOT` to the worktree root derived from `env!("CARGO_MANIFEST_DIR")`.
- Build: `cd agent-tools && cargo build --release` (and `cargo build` for debug used by tests).
- **Worktrees must NOT run `install.sh`** (per `CLAUDE.md`). Manual smoke runs the worktree's freshly-built binary directly, not the installed symlink.

**Spec:** `docs/superpowers/specs/2026-05-17-agent-tools-count-tokens-design.md`

---

## File Structure

| Path | Responsibility |
|---|---|
| `agent-tools/src/main.rs` | Add `Cmd::CountTokens { args: Vec<String> }` variant with `#[command(name = "count-tokens")]` and `trailing_var_arg = true, allow_hyphen_values = true`. Add match-arm that calls `uv_run(&root, &root, &["python3", "-m", "claude_config.count_tokens"], &args)`. |
| `src/claude_config/count_tokens.py` | New Python module. Top-level: `from claude_config.config import load; load()`. `main()` runs argparse, resolves input source, calls Anthropic SDK, prints `result.input_tokens`. Invoked as `python3 -m claude_config.count_tokens`. |
| `agent-tools/tests/count_tokens_test.rs` | New integration test file. 4 subprocess tests: --help wiring, mutual exclusion, file-not-found, missing-API-key. Uses `env!("CARGO_BIN_EXE_agent-tools")` for the binary and `env!("CARGO_MANIFEST_DIR")` parent for `CLAUDE_CONFIG_ROOT`. |
| `CLAUDE.md` | Add `agent-tools count-tokens [args]` entry to the agent-tools subcommand bullet list in the `agent-tools/` section. |

No changes to `Cargo.toml`, `pyproject.toml`, or `install.sh`. No new Rust or Python deps.

The Rust variant carries `args: Vec<String>` rather than typed fields — Python's argparse handles flag parsing and gives better error messages than splitting flag responsibility across clap + argparse. Matches the existing pattern for `Skill`, `CcPretty`, `CcWorkflow`, `NtfyHook`, and `PreOutputRecord`.

---

## Task 1: Wire the Rust dispatch and Python module skeleton

This task adds the subcommand to clap, dispatches to a Python module, and creates a Python skeleton that prints help. End of task: `agent-tools count-tokens --help` exits 0 with help text mentioning `--model` and `--file`.

**Files:**
- Modify: `agent-tools/src/main.rs` (Cmd enum + match arm)
- Create: `src/claude_config/count_tokens.py`
- Create: `agent-tools/tests/count_tokens_test.rs`

- [ ] **Step 1: Write the failing test**

Create `agent-tools/tests/count_tokens_test.rs` with the following content:

```rust
use std::path::PathBuf;
use std::process::{Command, Stdio};

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

/// Worktree root = parent of agent-tools/ (which is CARGO_MANIFEST_DIR).
fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("agent-tools/ should have a parent")
        .to_path_buf()
}

#[test]
fn count_tokens_help_dispatches_to_python_and_shows_flags() {
    let out = Command::new(bin())
        .arg("count-tokens")
        .arg("--help")
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .expect("failed to run agent-tools count-tokens --help");

    assert!(
        out.status.success(),
        "exit={:?} stderr={}",
        out.status.code(),
        String::from_utf8_lossy(&out.stderr)
    );
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(stdout.contains("--model"), "stdout missing --model: {stdout}");
    assert!(stdout.contains("--file"), "stdout missing --file: {stdout}");
}
```

- [ ] **Step 2: Run the test and verify it fails**

```bash
cd /root/claude-config-work2/agent-tools && cargo test --test count_tokens_test count_tokens_help_dispatches_to_python_and_shows_flags
```

Expected: FAIL during compile (`Cmd::CountTokens` doesn't exist) OR FAIL at runtime (subcommand `count-tokens` is unknown to clap).

- [ ] **Step 3: Add the `Cmd::CountTokens` variant to `main.rs`**

In `agent-tools/src/main.rs`, find the `Cmd` enum (around line 30-89). After the `PreOutputRecord` variant (which ends at line 81), and before `Ps` (line 82), add:

```rust
    /// Count tokens via Anthropic count_tokens API: agent-tools count-tokens [--model M] [--file P] [TEXT]
    #[command(name = "count-tokens")]
    CountTokens {
        /// Arguments forwarded to claude_config.count_tokens
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },
```

- [ ] **Step 4: Add the match arm dispatching to the Python module**

In the same file, find the inner `match cmd` block (around lines 183-224). After the `Cmd::PreOutputRecord { args } => { ... }` arm (ends around line 224), and before `Cmd::HookPre => unreachable!()` (line 225), add:

```rust
                Cmd::CountTokens { args } => {
                    uv_run(
                        &root,
                        &root,
                        &["python3", "-m", "claude_config.count_tokens"],
                        &args,
                    );
                }
```

- [ ] **Step 5: Create the Python module skeleton**

Create `src/claude_config/count_tokens.py` with this content:

```python
"""agent-tools count-tokens: report Anthropic count_tokens for stdin/file/arg text.

Invoked via `agent-tools count-tokens [--model MODEL] [--file PATH] [TEXT]`.
Reads ANTHROPIC_TOKEN_COUNT_API_KEY from /repos/claude-config/.env (loaded by
claude_config.config.load()) and prints a single integer to stdout.
"""

from __future__ import annotations

import argparse
import sys

from claude_config.config import load as _load_env

_load_env()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="count-tokens",
        description="Count input tokens for Claude models via the Anthropic count_tokens API.",
    )
    p.add_argument(
        "--model",
        default="claude-opus-4-7",
        help="Model ID (default: claude-opus-4-7).",
    )
    p.add_argument(
        "--file",
        dest="file",
        default=None,
        help="Read text from PATH as UTF-8.",
    )
    p.add_argument(
        "text",
        nargs="?",
        default=None,
        help="Text to count. If omitted and --file is omitted, read stdin.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    parser.parse_args(argv)
    # Subsequent tasks add input resolution, mutex check, and API call here.
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: Build the binary**

```bash
cd /root/claude-config-work2/agent-tools && cargo build
```

Expected: build succeeds. (Debug build, used by `cargo test`.)

- [ ] **Step 7: Run the test and verify it passes**

```bash
cd /root/claude-config-work2/agent-tools && cargo test --test count_tokens_test count_tokens_help_dispatches_to_python_and_shows_flags -- --nocapture
```

Expected: PASS. (First run may take a minute as `uv` provisions the Python 3.14 venv at `~/.claude/venvs/claude-config-work2/`. Subsequent runs are fast.)

If the test errors with "uv: command not found" or "venv setup failed", verify `uv` is on PATH and that `pyproject.toml` is intact at the worktree root.

- [ ] **Step 8: Commit**

```bash
cd /root/claude-config-work2
git add agent-tools/src/main.rs agent-tools/tests/count_tokens_test.rs src/claude_config/count_tokens.py
git commit -m "$(cat <<'EOF'
agent-tools: count-tokens — wire Rust dispatch + Python skeleton

Subcommand routes to `python3 -m claude_config.count_tokens` via the
existing uv_run pattern. Python module currently exposes --model, --file,
and a positional TEXT arg via argparse, returning 0 without doing work.
Follow-up tasks add input resolution, mutual-exclusion check, and the
Anthropic count_tokens call.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Implement input resolution (positional > file > stdin)

End of task: passing `--file /nonexistent` exits non-zero (FileNotFoundError propagates with traceback). Reading stdin and reading a real file both work end-to-end (covered by the next task's mutex test plus the manual smoke at the end).

**Files:**
- Modify: `src/claude_config/count_tokens.py`
- Modify: `agent-tools/tests/count_tokens_test.rs`

- [ ] **Step 1: Write the failing test**

Append to `agent-tools/tests/count_tokens_test.rs`:

```rust
#[test]
fn count_tokens_file_not_found_propagates_loudly() {
    let out = Command::new(bin())
        .arg("count-tokens")
        .arg("--file")
        .arg("/nonexistent/path/that/should/not/exist")
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .expect("failed to run agent-tools count-tokens --file /nonexistent");

    assert!(
        !out.status.success(),
        "expected failure, got exit=0 stdout={}",
        String::from_utf8_lossy(&out.stdout)
    );
    let stderr = String::from_utf8_lossy(&out.stderr);
    assert!(
        stderr.contains("FileNotFoundError") || stderr.contains("/nonexistent/path"),
        "expected loud file-not-found error, got stderr: {stderr}"
    );
}
```

- [ ] **Step 2: Run the test and verify it fails**

```bash
cd /root/claude-config-work2/agent-tools && cargo test --test count_tokens_test count_tokens_file_not_found_propagates_loudly
```

Expected: FAIL — the current skeleton returns 0 without reading the file.

- [ ] **Step 3: Implement input resolution in the Python module**

Replace the body of `main()` in `src/claude_config/count_tokens.py` with:

```python
def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    text = _resolve_input(parser, args)
    # API call added in a later task; for now just confirm the path executed.
    _ = text
    return 0


def _resolve_input(parser: argparse.ArgumentParser, args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    if args.file is not None:
        with open(args.file, "r", encoding="utf-8") as f:
            return f.read()
    if sys.stdin.isatty():
        parser.error("no input provided (pass TEXT, --file PATH, or pipe via stdin)")
    return sys.stdin.read()
```

(`parser.error()` exits with code 2 and writes to stderr — standard argparse behavior, satisfies the loud-failure rule.)

- [ ] **Step 4: Run the test and verify it passes**

```bash
cd /root/claude-config-work2/agent-tools && cargo build && cargo test --test count_tokens_test count_tokens_file_not_found_propagates_loudly
```

Expected: PASS. Also re-run the Task 1 test to confirm no regression:

```bash
cd /root/claude-config-work2/agent-tools && cargo test --test count_tokens_test
```

Expected: both tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work2
git add src/claude_config/count_tokens.py agent-tools/tests/count_tokens_test.rs
git commit -m "$(cat <<'EOF'
agent-tools: count-tokens — input resolution (positional > file > stdin)

Positional TEXT wins; else --file PATH is read; else stdin is read.
TTY + no input → argparse error. File-not-found propagates loudly
(FileNotFoundError with traceback) per the loud-failure rule.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Reject mutually-exclusive positional + --file

End of task: passing both a positional `TEXT` and `--file PATH` exits non-zero with a clear "mutually exclusive" stderr message, regardless of whether the file exists.

**Files:**
- Modify: `src/claude_config/count_tokens.py`
- Modify: `agent-tools/tests/count_tokens_test.rs`

- [ ] **Step 1: Write the failing test**

Append to `agent-tools/tests/count_tokens_test.rs`:

```rust
#[test]
fn count_tokens_rejects_file_plus_positional() {
    // Use an existing path so the failure is unambiguously the mutual-exclusion
    // check, not a missing-file error.
    let out = Command::new(bin())
        .arg("count-tokens")
        .arg("--file")
        .arg("/etc/hostname")
        .arg("inline text")
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .expect("failed to run agent-tools count-tokens --file ... TEXT");

    assert!(
        !out.status.success(),
        "expected non-zero exit, got 0; stdout={}",
        String::from_utf8_lossy(&out.stdout)
    );
    let stderr = String::from_utf8_lossy(&out.stderr);
    assert!(
        stderr.contains("mutually exclusive"),
        "expected 'mutually exclusive' in stderr, got: {stderr}"
    );
}
```

- [ ] **Step 2: Run the test and verify it fails**

```bash
cd /root/claude-config-work2/agent-tools && cargo test --test count_tokens_test count_tokens_rejects_file_plus_positional
```

Expected: FAIL — the current code happily accepts both and reads the file.

- [ ] **Step 3: Add the mutex check in the Python module**

In `src/claude_config/count_tokens.py`, modify `_resolve_input` to check mutual exclusion first:

```python
def _resolve_input(parser: argparse.ArgumentParser, args: argparse.Namespace) -> str:
    if args.text is not None and args.file is not None:
        parser.error("--file and TEXT are mutually exclusive")
    if args.text is not None:
        return args.text
    if args.file is not None:
        with open(args.file, "r", encoding="utf-8") as f:
            return f.read()
    if sys.stdin.isatty():
        parser.error("no input provided (pass TEXT, --file PATH, or pipe via stdin)")
    return sys.stdin.read()
```

`parser.error()` writes `count-tokens: error: --file and TEXT are mutually exclusive` to stderr and exits with code 2. That string contains "mutually exclusive", which the test asserts on.

- [ ] **Step 4: Run the test and verify it passes**

```bash
cd /root/claude-config-work2/agent-tools && cargo test --test count_tokens_test
```

Expected: all three tests PASS (--help, file-not-found, mutex).

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work2
git add src/claude_config/count_tokens.py agent-tools/tests/count_tokens_test.rs
git commit -m "$(cat <<'EOF'
agent-tools: count-tokens — reject positional TEXT + --file

Passing both is ambiguous; fail loudly via argparse with
'--file and TEXT are mutually exclusive' to stderr (exit 2).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Call the Anthropic count_tokens API and print the integer

End of task: `echo hello | agent-tools count-tokens` prints a small positive integer and exits 0. Missing `ANTHROPIC_TOKEN_COUNT_API_KEY` fails loudly with a traceback that names the missing key.

**Files:**
- Modify: `src/claude_config/count_tokens.py`
- Modify: `agent-tools/tests/count_tokens_test.rs`

- [ ] **Step 1: Write the failing test**

Append to `agent-tools/tests/count_tokens_test.rs`:

```rust
#[test]
fn count_tokens_missing_api_key_fails_loudly() {
    // NOTE: this test assumes the worktree does NOT have a populated
    // ANTHROPIC_TOKEN_COUNT_API_KEY in its top-level .env file. In a fresh
    // worktree, .env is gitignored and absent, so claude_config.config.load()
    // is a no-op and os.environ remains without the key.
    let out = Command::new(bin())
        .arg("count-tokens")
        .arg("hello")
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env_remove("ANTHROPIC_TOKEN_COUNT_API_KEY")
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .expect("failed to run agent-tools count-tokens hello");

    assert!(
        !out.status.success(),
        "expected non-zero exit (missing API key), got 0; stdout={}",
        String::from_utf8_lossy(&out.stdout)
    );
    let stderr = String::from_utf8_lossy(&out.stderr);
    assert!(
        stderr.contains("ANTHROPIC_TOKEN_COUNT_API_KEY"),
        "expected stderr to name the missing key, got: {stderr}"
    );
}
```

- [ ] **Step 2: Run the test and verify it fails**

```bash
cd /root/claude-config-work2/agent-tools && cargo test --test count_tokens_test count_tokens_missing_api_key_fails_loudly
```

Expected: FAIL — current code accepts the positional and returns 0.

If this test passes unexpectedly, check whether `/root/claude-config-work2/.env` exists and contains `ANTHROPIC_TOKEN_COUNT_API_KEY=...`. If so, temporarily move it aside while running this test (and restore after). Document this in a comment on the test if needed.

- [ ] **Step 3: Implement the API call in the Python module**

Replace `main()` in `src/claude_config/count_tokens.py` with:

```python
def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    text = _resolve_input(parser, args)

    import os
    import anthropic

    api_key = os.environ["ANTHROPIC_TOKEN_COUNT_API_KEY"]
    client = anthropic.Anthropic(api_key=api_key)
    result = client.messages.count_tokens(
        model=args.model,
        messages=[{"role": "user", "content": text}],
    )
    print(result.input_tokens)
    return 0
```

The `os.environ["ANTHROPIC_TOKEN_COUNT_API_KEY"]` access (not `.get`) raises `KeyError` with a traceback if the key is unset. The traceback prints `KeyError: 'ANTHROPIC_TOKEN_COUNT_API_KEY'` to stderr, which satisfies the test's assertion that stderr contains the key name.

Imports of `os` and `anthropic` are kept inside `main()` to avoid loading the (somewhat heavy) `anthropic` SDK during `--help` or test-only argparse invocations. This is a minor latency optimization, not a correctness requirement.

- [ ] **Step 4: Run the test and verify it passes**

```bash
cd /root/claude-config-work2/agent-tools && cargo build && cargo test --test count_tokens_test
```

Expected: all four tests PASS.

- [ ] **Step 5: Manual smoke test (live API)**

This step hits the live Anthropic API.

**Important wrinkle:** the worktree at `/root/claude-config-work2/` has no `.env` of its own (gitignored, not present). The canonical `/repos/claude-config/.env` is what holds the real key, but `claude_config.config.load()` resolves `.env` relative to the Python module path — when running under `CLAUDE_CONFIG_ROOT=/root/claude-config-work2`, that's `/root/claude-config-work2/.env`, which doesn't exist.

Workaround: extract the key from the canonical `.env` and pass it via shell env. `python-dotenv` is a no-op when its target file is missing, so the shell env carries through to `os.environ`.

```bash
cd /root/claude-config-work2/agent-tools && cargo build --release

ANTHROPIC_TOKEN_COUNT_API_KEY="$(grep '^ANTHROPIC_TOKEN_COUNT_API_KEY=' /repos/claude-config/.env | cut -d= -f2-)" \
CLAUDE_CONFIG_ROOT=/root/claude-config-work2 \
./target/release/agent-tools count-tokens "hello world"
```

Expected: a single small positive integer on stdout (likely in the range 8-15 for `claude-opus-4-7`), then a newline. Exit code 0.

Also try the stdin path:

```bash
echo "hello world" | \
  ANTHROPIC_TOKEN_COUNT_API_KEY="$(grep '^ANTHROPIC_TOKEN_COUNT_API_KEY=' /repos/claude-config/.env | cut -d= -f2-)" \
  CLAUDE_CONFIG_ROOT=/root/claude-config-work2 \
  ./target/release/agent-tools count-tokens
```

Expected: same shape (likely 1 higher because of the trailing newline that `echo` adds).

And the file path:

```bash
ANTHROPIC_TOKEN_COUNT_API_KEY="$(grep '^ANTHROPIC_TOKEN_COUNT_API_KEY=' /repos/claude-config/.env | cut -d= -f2-)" \
CLAUDE_CONFIG_ROOT=/root/claude-config-work2 \
./target/release/agent-tools count-tokens --file /etc/hostname
```

Expected: positive integer. Exit 0.

And a model override:

```bash
ANTHROPIC_TOKEN_COUNT_API_KEY="$(grep '^ANTHROPIC_TOKEN_COUNT_API_KEY=' /repos/claude-config/.env | cut -d= -f2-)" \
CLAUDE_CONFIG_ROOT=/root/claude-config-work2 \
./target/release/agent-tools count-tokens --model claude-haiku-4-5-20251001 "hello world"
```

Expected: positive integer (likely different from the Opus result). Exit 0.

If any of the four manual invocations fail, do NOT proceed to commit. Diagnose:
- `KeyError: 'ANTHROPIC_TOKEN_COUNT_API_KEY'` → the `grep|cut` substitution returned empty. Check `/repos/claude-config/.env` actually has a line `ANTHROPIC_TOKEN_COUNT_API_KEY=sk-ant-...`.
- 401 / auth error → key is stale or wrong; refresh it in `/repos/claude-config/.env`.
- `uv: command not found` → confirm uv is on PATH.
- `ModuleNotFoundError: anthropic` → run `cd /root/claude-config-work2 && uv sync` to materialize the venv.

(After `install.sh` is eventually run on the canonical clone, end users invoking the installed binary via PATH no longer need any of these env-var gymnastics — the binary resolves to `/repos/claude-config` and `claude_config.config.load()` finds `/repos/claude-config/.env` automatically. The dance above is only needed for testing the as-yet-uninstalled worktree build.)

- [ ] **Step 6: Commit**

```bash
cd /root/claude-config-work2
git add src/claude_config/count_tokens.py agent-tools/tests/count_tokens_test.rs
git commit -m "$(cat <<'EOF'
agent-tools: count-tokens — Anthropic count_tokens API call

Calls anthropic.Anthropic().messages.count_tokens(model=..., messages=[
{"role": "user", "content": text}]) with the key from
ANTHROPIC_TOKEN_COUNT_API_KEY (loaded from /repos/claude-config/.env)
and prints input_tokens as a bare integer. Missing key raises KeyError
with full traceback (loud failure).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Document the new subcommand in CLAUDE.md

End of task: `CLAUDE.md` lists `count-tokens` in the agent-tools subcommand bullet list, matching the style of the other entries.

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Locate the agent-tools subcommand list**

In `CLAUDE.md`, find the `### \`agent-tools/\`` section. It contains a bullet list of existing subcommands, e.g.:

```
- `agent-tools skill <mod> [args]` — run a skill script via `uv run python3 -m skills.<mod>`
- `agent-tools cc-pretty [args]` — pretty-print Claude Code JSONL session logs
- `agent-tools cc-workflow [args]` — extract sub-agent workflow summary
- `agent-tools ntfy-hook [args]` — Claude Code notification hook (wraps `python3 -m claude_config.ntfy_hook`)
```

- [ ] **Step 2: Add the count-tokens entry**

Add this line at the end of that bullet list (after the `ntfy-hook` line):

```
- `agent-tools count-tokens [--model MODEL] [--file PATH] [TEXT]` — count input tokens via Anthropic `count_tokens` API (wraps `python3 -m claude_config.count_tokens`)
```

- [ ] **Step 3: Verify the file still parses cleanly as Markdown**

```bash
cd /root/claude-config-work2 && grep -A 8 '^### `agent-tools/`' CLAUDE.md | head -15
```

Expected output includes the new `count-tokens` line in the bullet list, formatted consistently with the others.

- [ ] **Step 4: Commit**

```bash
cd /root/claude-config-work2
git add CLAUDE.md
git commit -m "$(cat <<'EOF'
docs: list count-tokens in CLAUDE.md agent-tools subcommands

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Final verification

After all tasks complete, run the full integration suite once more and re-check the acceptance criteria from the spec:

```bash
cd /root/claude-config-work2/agent-tools && cargo test --test count_tokens_test
```

Expected: 4 tests PASS.

Spec acceptance criteria walk-through (each should be satisfied by the work above):

1. ✅ `agent-tools count-tokens --help` shows subcommand + flags → Task 1 test.
2. ✅ `echo "hello world" | agent-tools count-tokens` prints positive int → Task 4 manual smoke.
3. ✅ `agent-tools count-tokens "hello"` prints positive int → Task 4 manual smoke.
4. ✅ `agent-tools count-tokens --file /etc/hostname` prints positive int → Task 4 manual smoke.
5. ✅ `agent-tools count-tokens --file foo "bar"` exits non-zero with clear stderr → Task 3 test.
6. ✅ `agent-tools count-tokens --model claude-haiku-4-5-20251001 "hello"` prints (different) positive int → Task 4 manual smoke.
7. ✅ Unsetting `ANTHROPIC_TOKEN_COUNT_API_KEY` causes a `KeyError` traceback → Task 4 test.
8. ✅ `CLAUDE.md` lists `count-tokens` in the agent-tools subcommand table → Task 5.
