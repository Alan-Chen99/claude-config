# `agent-tools count-tokens` subcommand

**Date:** 2026-05-17
**Status:** approved (pending user review)

## Problem

There is no convenient CLI for counting Claude input tokens of a piece of text. The Anthropic `messages.count_tokens` endpoint is already wrapped inside `docs/system-prompt-snapshot/capture.py` (line 110), but only for the snapshot pipeline's specific `system=`/`tools=` shapes — it is not callable as a general-purpose utility.

## Goal

A new subcommand `agent-tools count-tokens` that:

- Takes plain text from stdin, a file, or a positional argument.
- Calls the free Anthropic `messages.count_tokens` endpoint with `ANTHROPIC_TOKEN_COUNT_API_KEY` (already loaded from `/repos/claude-config/.env` by `claude_config.config`), the text as one user message.
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

`--model` defaults to `claude-opus-4-7` and is passed verbatim to the SDK; `--file` is read as UTF-8.

**Input resolution (exclusive, in order):** positional `TEXT`, else `--file PATH`, else stdin to EOF. Both `TEXT` and `--file` → exit 1, `count-tokens: --file and TEXT are mutually exclusive`. None of the three with stdin a TTY → exit 1, `count-tokens: no input provided (pass TEXT, --file PATH, or pipe via stdin)`.

Empty input (zero-length text after reading) is **not** an error — the SDK returns a positive token count for a single user message with empty content, and forcing an error here would surprise pipelines that legitimately feed empty strings. Print whatever the API returns. No whitespace stripping; the text is passed through verbatim.

### Code layout

`agent-tools/src/main.rs` gains a `Cmd::CountTokens { args: Vec<String> }` variant forwarding its args verbatim to `python3 -m claude_config.count_tokens` (new module `src/claude_config/count_tokens.py`, directly invokable). The variant carries `args: Vec<String>` rather than typed fields because argparse on the Python side already handles flag parsing and gives better error messages than mixing clap + argparse for the same flags — as `Skill`, `CcPretty`, `CcWorkflow`, `NtfyHook` and `PreOutputRecord` all forward to Python. `anthropic` is already a dependency (the snapshot scripts use it). `CLAUDE.md` lists `count-tokens` among the agent-tools subcommands.

### Error handling

All errors surface visibly per the "loud failure" rule — no fallbacks, no silent swallow:

- A missing `ANTHROPIC_TOKEN_COUNT_API_KEY` raises `KeyError` with a full traceback: the key is read via `os.environ[...]`, not `.get(...)`.
- API auth/network/quota errors propagate as `anthropic.*` exceptions; a missing or unreadable `--file` as `FileNotFoundError` / `PermissionError`.
- The two input-resolution errors above are argparse-driven exits.

### Tests

The Python package `src/claude_config/` has **no test suite**; only `skills/scripts/tests/` is wired for pytest. Rather than scaffold Python test infrastructure for a 30-line module, `agent-tools/tests/count_tokens_test.rs` invokes the built binary as a subprocess and checks `--help`, a missing `--file`, the mutual-exclusion error (with an existing file, so the failure is unambiguously the exclusion check), and the `KeyError` with the key cleared — arg parsing, input resolution and error propagation, never the live API. An end-to-end live-API check (`echo hello | agent-tools count-tokens` prints a small positive integer) runs once manually during implementation and is recorded in the plan's verification step, not in CI.

No Python unit tests are added. If the Python logic grows beyond ~30 lines or gains branching the Rust integration tests can't exercise cheaply, a Python test suite under `tests/claude_config/` is introduced then — out of scope here.

## Acceptance criteria

Beyond the behaviour above: `agent-tools count-tokens --help` shows `--model`, `--file` and positional `TEXT`; stdin, positional and `--file` input each print a positive integer and exit 0; `--model claude-haiku-4-5-20251001 "hello"` prints a (different) positive integer for the Haiku tokenizer; an unset `ANTHROPIC_TOKEN_COUNT_API_KEY` (or a loader pointed at an empty `.env`) gives a `KeyError` traceback, not a silent zero.
