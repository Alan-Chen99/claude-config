# opencode-pretty Design

## Goal

Add `agent-tools opencode-pretty <session-id>` to pretty-print opencode session transcripts in a format similar to `agent-tools cc-pretty`.

The command should retrieve session data through the installed `opencode` binary, not by reading opencode internals directly.

## Command Surface

Add a new `agent-tools` subcommand:

```bash
agent-tools opencode-pretty <session-id> [options]
```

Initial options should mirror the useful `cc-pretty` display controls where they apply:

- `--tool-max N`: maximum rendered tool output length.
- `--truncate-input`: truncate tool input to `--tool-max` characters; otherwise show tool input in full.
- `--no-color`: disable ANSI colors.
- `--no-thinking`: hide reasoning text and show a compact reasoning marker instead.
- `--agent`: use chunked output behavior if rendered output is too large for direct Bash output.

## Architecture

Reuse the existing Rust forwarding pattern in `agent-tools/src/main.rs`:

- Add `OpencodePretty { args }` to `Cmd` with `#[command(name = "opencode-pretty")]`.
- Dispatch it through `uv_run(&root, &root, &["python3", "-m", "claude_config.opencode_pretty.main"], &args)`.

Add a Python package under `src/claude_config/opencode_pretty/`:

- `main.py`: CLI parsing, `opencode export` invocation, JSON loading, record rendering, and agent chunk output.
- Keep opencode-specific parsing local to this module because opencode export JSON is structurally different from Claude Code JSONL.
- Reuse `claude_config.cc_pretty.render` for colors, timestamp formatting, truncation, tool input formatting, separators, and usage-like display helpers where possible.

## Data Flow

The Python command should run:

```bash
opencode export <session-id>
```

It should parse stdout as JSON. Current opencode prints a non-JSON status line before the JSON object, so the loader should locate the first `{` and parse from there.

Expected export shape:

- Top-level `info` contains session metadata, model, version, costs, tokens, and timestamps.
- Top-level `messages` is a list of message objects.
- Each message has `info` for role, timestamps, model, tokens, finish reason, and IDs.
- Each message has `parts`, including text, reasoning, tool, step-start, and step-finish records.

## Rendering

Render a header containing available session metadata:

- session title or slug
- abbreviated session ID
- opencode version
- model/provider/variant
- working directory when available

Render message turns in chronological order:

- User text parts as `User` blocks.
- Assistant text parts as `Assistant` blocks.
- Reasoning parts as thinking/reasoning blocks when `--no-thinking` is not set, or compact markers when hidden.
- Tool parts as `Tool` blocks, including tool name, call ID, input, status, output, title, and elapsed duration when available.
- Ignore structural parts such as `step-start` and `step-finish` by default, except use step-finish token/cost metadata when helpful for assistant summaries.

The format does not need to be byte-for-byte identical to `cc-pretty`; it should be visually consistent and use the same color/separator style.

## Error Handling

- If `session-id` is missing, argparse should show usage and exit nonzero.
- If `opencode export` exits nonzero, print stderr and exit with that status when possible.
- If stdout does not contain JSON, print a clear parse error.
- If unknown part types are encountered, hide them by default to avoid noisy output.

## Testing

Add unit-level tests for the Python renderer using a fixture export JSON with:

- one user text message
- one assistant text response
- one assistant tool part with input and output
- one reasoning part

Add Rust CLI coverage that `agent-tools opencode-pretty` forwards arguments to the Python module in the same style as existing Python-backed subcommands if the existing test harness makes that practical. If forwarding is hard to assert without invoking `uv`, rely on Python tests plus Rust compile tests.

Run verification:

```bash
uv run pytest
cd agent-tools && cargo test
```

## Non-Goals

- Do not read opencode's database or files directly.
- Do not implement opencode import/export mutation.
- Do not emulate Claude Code compaction or rewind detection for opencode sessions unless opencode export exposes equivalent data.
- Do not preserve backward compatibility for any nonexistent previous `opencode-pretty` command.
