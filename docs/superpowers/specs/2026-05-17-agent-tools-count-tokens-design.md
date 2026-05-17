# `agent-tools count-tokens` subcommand

**Date:** 2026-05-17
**Status:** approved (pending user review)

## Problem

There is no convenient CLI for counting Claude input tokens of a piece of text. The Anthropic `messages.count_tokens` endpoint is already wrapped inside `docs/system-prompt-snapshot/capture.py` (line 110), but only for the snapshot pipeline's specific `system=`/`tools=` shapes — it is not callable as a general-purpose utility. Users who want to know how many tokens a chunk of text consumes for a Claude model currently have no one-shot command.

## Goal

A new subcommand `agent-tools count-tokens` that:

- Takes plain text from stdin, a file, or a positional argument.
- Calls the free Anthropic `messages.count_tokens` endpoint with `ANTHROPIC_TOKEN_COUNT_API_KEY` (already loaded from `/repos/claude-config/.env` by `claude_config.config`).
- Prints a single integer to stdout. Composable in shell pipelines.

## Non-goals

- Counting tokens for full request bodies (system blocks, tools, multi-turn messages). The snapshot scripts already handle this internally; exposing it would require a richer JSON-in/JSON-out CLI that is out of scope here.
- Local/offline tokenization. tiktoken is for OpenAI models; Anthropic's old client-side tokenizer is deprecated and not accurate for Claude 3+. Anyone needing offline counting should reach for a different tool.
- Streaming or batched inputs. One call, one number.

## Design

### CLI surface

```
agent-tools count-tokens [--model MODEL] [--file PATH] [TEXT]
```

| Flag / arg | Type | Default | Meaning |
|---|---|---|---|
| `--model MODEL` | string | `claude-opus-4-7` | Model ID passed verbatim to the SDK. |
| `--file PATH` | path | — | Read text from PATH as UTF-8. |
| `TEXT` | positional | — | Use as text directly. |

**Input resolution (exclusive, in order):**

1. If positional `TEXT` is given → use it.
2. Else if `--file PATH` is given → read PATH.
3. Else → read stdin to EOF.

If both `TEXT` and `--file` are given → exit 1 with stderr: `count-tokens: --file and TEXT are mutually exclusive`.

If none of the three is given and stdin is a TTY → exit 1 with stderr: `count-tokens: no input provided (pass TEXT, --file PATH, or pipe via stdin)`.

Empty input (zero-length text after reading) is **not** an error — the SDK will return a positive token count for a single user message with empty content, and forcing an error here would surprise pipelines that legitimately feed empty strings. Print whatever the API returns. (No whitespace stripping; the text is passed through verbatim.)

### Backend call

```python
from claude_config.config import load
load()  # populates os.environ from /repos/claude-config/.env

import os, anthropic
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_TOKEN_COUNT_API_KEY"])
result = client.messages.count_tokens(
    model=args.model,
    messages=[{"role": "user", "content": text}],
)
print(result.input_tokens)
```

Note: API key is read via `os.environ[...]` (not `.get(...)`) so a missing key raises `KeyError` with a backtrace, surfacing the misconfiguration loudly per project conventions.

### Code layout

| File | Change |
|---|---|
| `agent-tools/src/main.rs` | Add a new `Cmd::CountTokens { args: Vec<String> }` variant with `#[command(name = "count-tokens")]` and `trailing_var_arg = true`. In the match arm, dispatch to `python3 -m claude_config.count_tokens` with the args forwarded verbatim. Matches the `NtfyHook` / `PreOutputRecord` pattern at `main.rs:209-224`. |
| `src/claude_config/count_tokens.py` | New module. `argparse` with `--model`, `--file`, positional `text`. Implements input resolution (above), calls SDK, prints int. Module is directly invokable: `python3 -m claude_config.count_tokens [args...]`. |
| `pyproject.toml` | No change. `anthropic` is already a dep (used by snapshot scripts). |
| `CLAUDE.md` | Add `count-tokens` to the agent-tools subcommand list in the `agent-tools/` section. |

The Rust variant carries `args: Vec<String>` rather than typed fields because argparse on the Python side already handles flag parsing and gives better error messages than mixing clap + argparse for the same flags. Matches how `Skill`, `CcPretty`, `CcWorkflow`, `NtfyHook`, and `PreOutputRecord` all forward `args: Vec<String>` to Python.

### Error handling

| Failure | Result |
|---|---|
| Missing `ANTHROPIC_TOKEN_COUNT_API_KEY` | `KeyError` propagates from Python with full traceback. |
| API auth/network/quota error | `anthropic.*` exception propagates with full traceback. |
| Both `TEXT` and `--file` given | argparse-driven exit 1, stderr message. |
| No input and stdin is a TTY | argparse-driven exit 1, stderr message. |
| `--file PATH` doesn't exist / unreadable | Python `FileNotFoundError` / `PermissionError` propagates. |

All errors surface visibly per the "loud failure" rule — no fallbacks, no silent swallow.

### Tests

The Python package `src/claude_config/` currently has **no test suite**; only `skills/scripts/tests/` is wired for pytest. Rather than scaffold a new Python test infrastructure for a 30-line module, drive testing from the Rust integration tests that already exist in `agent-tools/tests/`.

**`agent-tools/tests/count_tokens_test.rs`** — invokes the built `agent-tools` binary as a subprocess:

1. `agent-tools count-tokens --help` exits 0 and stdout contains `count-tokens`, `--model`, `--file`.
2. `agent-tools count-tokens --file /nonexistent/path` exits non-zero (Python `FileNotFoundError` propagates).
3. `agent-tools count-tokens --file /etc/hostname "inline text"` exits non-zero with a stderr message about mutual exclusion. (Existing path used so the failure is unambiguously the exclusion check, not a missing-file error.)
4. `echo "" | agent-tools count-tokens </dev/null` with `ANTHROPIC_TOKEN_COUNT_API_KEY` cleared exits non-zero (KeyError propagates). This is the loud-failure check.

The tests above do NOT hit the live Anthropic API; they verify arg parsing, input resolution, and error propagation. An end-to-end live-API check is performed once manually during implementation (`echo hello | agent-tools count-tokens` should print a small positive integer) and recorded in the implementation plan's verification step — not in CI.

No Python unit tests are added. If the Python logic later grows beyond ~30 lines or gains branching that the Rust integration tests can't exercise cheaply, a Python test suite under `tests/claude_config/` should be introduced at that point — out of scope for this spec.

## Acceptance criteria

1. `agent-tools count-tokens --help` shows the subcommand with `--model`, `--file`, and positional `TEXT`.
2. `echo "hello world" | agent-tools count-tokens` prints a positive integer and exits 0.
3. `agent-tools count-tokens "hello"` prints a positive integer and exits 0.
4. `agent-tools count-tokens --file /etc/hostname` prints a positive integer and exits 0.
5. `agent-tools count-tokens --file foo "bar"` exits non-zero with a clear stderr message.
6. `agent-tools count-tokens --model claude-haiku-4-5-20251001 "hello"` prints a (different) positive integer for the Haiku tokenizer.
7. Unsetting `ANTHROPIC_TOKEN_COUNT_API_KEY` (or pointing the loader at a temp empty `.env`) causes a `KeyError` traceback, not a silent zero.
8. `CLAUDE.md` lists `count-tokens` in the agent-tools subcommand table.
