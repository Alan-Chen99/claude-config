---
name: opencode-subcommand
description: Use when running opencode programmatically — test harness, automation, batch runs. Covers inline-config invocation, plugin loading, model overrides, capturing/exporting sessions, and common pitfalls.
---

# opencode-subcommand

How to drive opencode as a subprocess: inline config so an installed or
global opencode config doesn't interfere, capture the session, pull it back
out later for inspection.

## Basic invocation

```bash
opencode run --agent <name> --format json --dir <workdir> < task.md
```

- `--agent <name>` selects an agent defined in the (possibly inline) config.
- `--format json` makes the per-turn JSON the only thing on stdout.
- `--dir <workdir>` sets opencode's working directory — used to restrict what
  the agent can see when fixture confinement matters.
- stdin is the user task. Use `< task.md` or `echo '...' | ...`.

## Inline config (no project config interference)

```bash
OPENCODE_DISABLE_PROJECT_CONFIG=1 \
OPENCODE_CONFIG_CONTENT='{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "my-agent": {
      "mode": "primary",
      "prompt": "{file:/absolute/path/to/agent.md}",
      "permission": {
        "read": "allow",
        "glob": "allow",
        "grep": "allow",
        "list": "allow",
        "bash": "allow",
        "edit": "deny"
      }
    }
  }
}' \
opencode run --agent my-agent ...
```

- `OPENCODE_DISABLE_PROJECT_CONFIG=1` skips any `.opencode/*` config that
  would otherwise be picked up from the working directory.
- Per-agent `permission` must be an **object** (per-tool keys). opencode
  `1.15.5+0086a0b` rejects the string form `"permission": "allow"`.
- `prompt` accepts `{file:<absolute-path>}` to point at a prompt file on disk.
  Relative paths will not resolve.

### Worktree-portable `$REPO` interpolation

To make the same command work from any worktree, resolve `REPO` via git and
escape the single-quoted JSON literal locally:

```bash
REPO="$(git rev-parse --show-toplevel)"
OPENCODE_CONFIG_CONTENT='{
  ...
  "prompt": "{file:'"$REPO"'/opencode/agents/alan-default-ids.md}",
  ...
}'
```

The `'"$REPO"'` segments switch from single-quote to double-quote and back so
the shell expands `$REPO` while the rest of the JSON literal stays intact. Use
`alan-default.md` only when intentionally running the legacy unlabelled variant.

## Plugin loading

```json
"plugin": ["superpowers@git+https://github.com/obra/superpowers.git"]
```

The plugin field is a top-level config key, peer to `agent`. Plugins install
into opencode's package cache on first run.

## Model overrides

```bash
opencode run --agent my-agent --model anthropic/claude-sonnet-4 ...
```

`--model` is a `provider/model` string. It overrides whatever the agent's
config or opencode's default would have picked.

## Capturing the session

`opencode run --format json` writes JSON per turn to stdout. To keep it for
later inspection:

```bash
opencode run --agent my-agent --format json ... < task.md | tee /tmp/session.jsonl
```

The session id is in the JSON output. To re-fetch a session later:

```bash
opencode export <session-id>
```

`opencode export` writes a single JSON document to stdout; pipe to a file or
pass the session id directly to `agent-tools opencode-pretty`.

## Common pitfalls

- **JSON gotchas.** `OPENCODE_CONFIG_CONTENT` is a JSON literal inside a
  shell single-quoted string. Escapes (`\n`, `\"`) get processed by JSON,
  not the shell. Test the JSON in isolation with `echo "$OPENCODE_CONFIG_CONTENT" | jq` before debugging opencode.
- **`--dir` matters for visibility.** Setting `--dir` to a narrow fixture
  directory hides the rest of the repo from the agent. Use this when a test
  needs to prevent the agent from grepping reference solutions.
- **String-form `permission`.** Opencode `1.15.5+0086a0b` and newer reject
  the legacy `"permission": "allow"` string form. Use the object form
  (per-tool keys) shown above.
- **No worktree path-hardcoding.** Resolve `REPO` from `git rev-parse` so the
  same command works in any worktree.

## Wrapper note

`agent-tools opencode` is a thin wrapper that loads the repo `.env` and maps
the `OPENCODE_LANGFUSE_*` keys to the unprefixed `LANGFUSE_*` names the
opencode Langfuse plugin expects. Use `agent-tools opencode` only when you
need that env mapping; pure `opencode` is fine otherwise.
