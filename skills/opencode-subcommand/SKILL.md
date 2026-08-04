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
      "model": "openai/gpt-5.5",
      "variant": "xhigh",
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
- **`model` and `variant` belong in the agent block, not the agent-file
  frontmatter.** `{file:...}` is a raw-text include (see the contamination
  section below): frontmatter fields are not parsed as agent config, only
  inlined as prompt text. Without a `model:` field in the agent block or
  `--model` on the command line, opencode falls back to the "most recent"
  model from `~/.local/share/opencode/state/model.json`, which is
  session-history-dependent (round 18 fixture-side confound: fell through
  to `openai/gpt-5.4` on the first run of `E-permission`). Always set
  `model` explicitly and verify with `agent-tools opencode-pretty
  <session> --agent` after the run.

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
the shell expands `$REPO` while the rest of the JSON literal stays intact.

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

## System-prompt contamination (load-bearing for probes)

opencode has three known channels that inject content into the system
prompt that the caller may not realise is there. All three matter for
prompt-evaluation and mechanism-probe work; ignore them and you will
attribute contamination-driven behaviour to the spec under test. Round
19 named F87b (frontmatter leak) after round 18 spent effort on a
spec-design hypothesis (F80) that round 20 subsequently CONTRADICTED
once frontmatter was stripped — 0-tool-call cells became 19/34-tool-call
cells with only the frontmatter block removed.

### C1 — `{file:PATH}` template is a raw-text include, frontmatter and all

`packages/opencode/src/config/variable.ts:44-88` (`substitute()`) expands
`{file:PATH}` tokens by reading the file raw
(`Filesystem.readText(...).trim()`) and inlining the whole content as a
JSON-escaped string. YAML `---` fences, key/value pairs, and `#`
comments are preserved verbatim. When used as
`"prompt": "{file:agent.md}"`, the entire raw file — frontmatter
included — becomes `agents[name].prompt` and flows to
`session/llm.ts:116` as the system prompt.

Mitigations, in order of preference:

1. **Strip YAML frontmatter from any spec loaded via `{file:...}`.**
   The frontmatter block cannot describe the probe, cite prior cells,
   or state hypotheses — the model reads it as system-prompt text.
   Verify per file with:

   ```bash
   grep -c 'probe\|round-1[0-9]\|compliance-check\|Investigation trail\|F[0-9]\{2\}' <spec>.md
   ```

2. **Use an inline `prompt` string in `OPENCODE_CONFIG_CONTENT`** for
   probe agents instead of `{file:...}`. Model/variant fields still go
   in the agent block. This is verbose but eliminates the file-read
   step entirely.

3. **Commit the agent under `.opencode/agents/<name>.md` and load it
   via `agent.load()`** (`packages/opencode/src/config/agent.ts:105-130`).
   That path parses via `gray-matter`; frontmatter is stripped
   cleanly. Only useful for stable agents — probes should not be
   committed.

Contrast: the `.opencode/agents/*.md` disk-load path is clean because it
calls `matter(template)` and returns `{ ...md.data, prompt:
md.content.trim() }`. `{file:...}` is a different code path with no
gray-matter call. Round-19 F87 briefly conflated them; the actual
mechanism is F87b.

### C2 — `agent-tools run --desc "..."` argv leak (opt-in fix)

Round 19 F88 named this: a probe launched as `agent-tools run --desc
"E-k3-v8: Kimi K3 + v8 + H17" -- opencode run ...` had the desc string
visible via `ps aux` and `/proc/*/cmdline`, and E-k3-nodontact's
test-agent quoted it back verbatim.

Fix: `agent-tools run --hide-cmdline ...` overwrites the argv memory
region so peers reading `ps aux` or `/proc/*/cmdline` see only
`agent-tools: <exe>` instead of the full `--desc "..." -- <cmd>`. The
hide is **opt-in**: without the flag, `comm` is set to `at:<hint>`
but the argv is left visible because clarity is more useful than
privacy for general debugging.

For probe work, always pass `--hide-cmdline` on the wrapping
`agent-tools run` invocation:

```bash
agent-tools run --hide-cmdline --desc "F80-clean re-run" -- \
  opencode run --agent v8 --format json --dir "$SCRATCH" < task.md
```

`desc` remains in `meta.json` for `agent-tools ps` regardless of the
flag.

If you are running against an older `agent-tools` build (e.g. via the
canonical `~/.local/bin/agent-tools` installed before the F88 fix
landed), the `--hide-cmdline` flag will not be recognized — rebuild
from the current tree, or invoke `opencode run` directly without the
wrapper for probe work.

### C3 — `CLAUDE.md` / `AGENTS.md` / `CONTEXT.md` injection

`packages/opencode/src/session/instruction.ts:14-18, 154-168` reads:

- `~/.claude/CLAUDE.md` (unless `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1`)
- The first `AGENTS.md`/`CLAUDE.md`/`CONTEXT.md` found walking up from
  `--dir`
- `~/.config/opencode/AGENTS.md`

Each file's full content is concatenated into the system prompt at
`session/prompt.ts:1426`. Currently benign in this repo (grep across
active CLAUDE.md files returned zero probe/round/F-number matches as
of round 19), but a live channel: any future edit to those files with
probe-related content would inject unchecked.

Set both `OPENCODE_DISABLE_PROJECT_CONFIG=1` **and**
`OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1` for probes. The
`prompt-tests` recipe already does this; extend to any custom probe
harness.

## Reasoning-summary visibility (F62 — Codex backend only)

### Scope: F62 is entirely a ChatGPT Codex backend behavior

Opencode's default OpenAI credential is OAuth against a ChatGPT
Pro/Plus account (see `packages/opencode/src/plugin/codex.ts`). The
codex plugin's fetch override at
`packages/opencode/src/plugin/codex.ts:479-481` rewrites requests from
`api.openai.com/v1/responses` to
`https://chatgpt.com/backend-api/codex/responses` before they leave
the process. That is the ChatGPT web backend that Codex CLI also uses;
it is not the public OpenAI Responses API.

**Verified 2026-07-27:** the same request body (`reasoning: {"effort":
"xhigh", "summary": "auto"}`, model `gpt-5.5`, same math task) returns
dramatically different content on the two endpoints:

| Endpoint | Auth | `reasoning_summary_text.done` |
|---|---|---|
| `chatgpt.com/backend-api/codex/responses` | ChatGPT OAuth | 43 chars — `**Calculating original price per apple**` |
| `api.openai.com/v1/responses` | `OPENAI_API_KEY` | 363 chars — `**Calculating apple cost**\n\nI need to answer a math question...` (full paragraph with actual arithmetic) |

The Codex backend reduces reasoning summaries to a single bold
heading. The public API returns paragraph-level content that describes
the actual arithmetic performed. Same model, same request, different
endpoint. **F62 as a "gpt-5.5 reasoning-summary cutover" claim is
wrong — it's a Codex backend policy, not a model or API change.**

All F62-scoped measurements in this doc and in the round-9+ notes
were against the Codex backend without recognizing that (round 9 had
no wire-level check to expose the URL rewrite). Findings that depend
on paragraph-level reasoning content can be recovered on the public
API path.

### How to route through the public API

Opencode's stored OAuth takes precedence over `OPENAI_API_KEY` env
var. To force the public-API path in a single command, override auth
via `OPENCODE_AUTH_CONTENT`:

```bash
export OPENCODE_AUTH_CONTENT="{\"openai\":{\"type\":\"api\",\"key\":\"$OPENAI_API_KEY\"}}"
```

The codex plugin's `if (auth.type !== "oauth") return {}` guard
(`packages/opencode/src/plugin/codex.ts:406`) then declines to attach
its fetch override, the SDK's default fetch is used, and the request
goes to `api.openai.com/v1/responses` with `Authorization: Bearer
<sk-...>`. Verify with `OPENCODE_F62_LOG_DIR` — request URL will be
`https://api.openai.com/v1/responses` and no `*CODEX*` capture files
will be produced.

### What the "summary" is

OpenAI's Responses API for gpt-5-class reasoning models never returns
the actual chain-of-thought tokens — those stay confidential and are
streamed only as opaque `reasoning.encrypted_content` blocks (visible
in opencode's `include: ["reasoning.encrypted_content"]` setting,
`transform.ts:1152`) that the server can rehydrate for prompt-cache
reuse. The `reasoning.summary` field is a **separate** server-generated
summary of what the model was thinking about, delivered to the client
as plain text. Opencode requests `reasoningSummary: "auto"` for gpt-5.5
(`transform.ts:1129, 1136, 1153`).

On the ChatGPT Codex backend, the response is reduced to a single
bold heading (mean 39 chars). On the public OpenAI API with the same
model / same request body, the response is a full paragraph (~360
chars) with actual arithmetic content. The reduction is a Codex
backend policy, not an API-wide or model-wide change.

### Evidence (verified 2026-07-27 via wire-level capture)

Reproduced by instrumenting opencode at two points, both gated behind
`OPENCODE_F62_LOG_DIR`: `provider.ts:1567` customFetch (pre-rewrite
URL) and `codex.ts` fetch override (post-rewrite URL). Compared side
by side against `api.openai.com/v1/responses` (via
`OPENCODE_AUTH_CONTENT` API-key override) and
`chatgpt.com/backend-api/codex/responses` (via stored OAuth).

**Same-day paired data (same model, same request body, same task):**

| Endpoint | `reasoning_summary_text.done` |
|---|---|
| `chatgpt.com/backend-api/codex/responses` | 43 chars — `**Calculating original price per apple**` |
| `api.openai.com/v1/responses` | 363 chars — `**Calculating apple cost**\n\nI need to answer a math question by focusing just on the numbers. So, I have 5 apples that cost a total of $10.50 after a 30% discount. This means I'm paying 70% of the original price. To find the original total, I calculate $10.50 divided by 0.7, which gives me $15. That means each apple costs $3. So, the final answer should be "3."` |

**Additional Codex-backend measurements (all heading-only):** with
`reasoning: {"effort": <e>, "summary": <s>}` for `s ∈ {auto, detailed,
concise}` × `e ∈ {medium, xhigh}` — 5 data points, mean 39 chars,
always single-line bold heading, always exactly one
`response.reasoning_summary_text.done` event. Values: 43, 32, 36, 48,
36. Bogus `summary` value returns HTTP 400 with *"Invalid value: '…'.
Supported values are: 'concise', 'detailed', and 'auto'."*

The public API returns per-chunk `response.reasoning_summary_text.delta`
events streaming word-by-word into the final `.done` event with the
full paragraph. The Codex backend emits exactly one delta whose payload
is the whole heading, followed by an identical `.done`.

### Likely reasons the Codex backend reduces summaries (speculative)

Not directly attested by OpenAI. The shapes that fit:

- **Distillation defense on the subscription path.** Paragraph
  summaries are the highest-signal externally-visible piece of the
  model's decision process. Codex CLI users are paying per-subscription
  (not per-token), so the ROI on giving them full summaries is lower
  than for API-key users paying per-token who explicitly opt into
  reasoning tokens. Reducing to headings on the subscription path
  drops training signal without breaking the API-key product.
- **User-content leak reduction on the subscription path.** Paragraph
  summaries can restate user input verbatim; heading-only cannot.
- **Consistency with Codex CLI's own UX.** Codex CLI shows brief
  reasoning headings by default in its TUI — the reduction is
  aligned with how that product surfaces reasoning to end users.

### Practical implications for probe work

- **Route through the public API for probe work that needs
  reasoning-summary content.** Set `OPENAI_API_KEY` + the
  `OPENCODE_AUTH_CONTENT` override shown above. Paragraph-level
  reasoning summaries are available. This is the primary fix.
- Findings from rounds 8-20 in the notes that describe gpt-5.5 as
  "heading-only" were measured on the Codex backend without knowing.
  Where a finding rests on the absence of paragraph reasoning content,
  reconsider under the public API path.
- Non-OpenAI reasoning-visible models via OpenRouter (`deepseek/*`,
  `qwen/*`) remain useful for cross-model triangulation.
  Round 18 F85 used DeepSeek R1 as a substitute when we couldn't see
  gpt-5.5's reasoning body — with the public API path now known to
  work, F85's cross-check is still useful for model-family
  differences but is no longer required to recover paragraph content
  on gpt-5.5.
- Design-side workaround (commentary surfacing) is unaffected by
  endpoint choice.

Reference scaffold: `scripts/reasoning-probe.py` (raw OpenRouter API,
frontmatter-strip on spec before send, tool definitions matching
opencode's schema; the model can nominate tool calls but the script
does not execute them — decision-time reasoning is the target). Use
against non-OpenAI upstreams (`deepseek/*`, `qwen/*`); OpenRouter's
`openai/*` chat-completions endpoint synthesizes reasoning
different from what OpenAI's Responses API returns and is not a
faithful gpt-5.5 substitute.

### F62 direct-wire reproduction (opencode instrumentation)

Set `OPENCODE_F62_LOG_DIR=<dir>` before running opencode. Two hooks
fire:

- `packages/opencode/src/provider/provider.ts:1567` (customFetch) —
  captures the request before the codex plugin's URL rewrite. Logs
  the SDK-intended URL (`api.openai.com/v1/responses`) even when the
  request actually goes elsewhere.
- `packages/opencode/src/plugin/codex.ts` (fetch override) — captures
  the request post-rewrite. Files are named `*CODEX*.req` and
  `*CODEX*.res`. If no CODEX files appear, the OAuth path was not
  used and the SDK's default fetch went directly to the public API.

Both hook points SSE-tee the response body without changing what the
client sees. Zero cost when the env var is unset.

Minimal repro on the **public API** (paragraph reasoning):

```bash
source /repos/claude-config/.env  # provides OPENAI_API_KEY
export OPENCODE_AUTH_CONTENT="{\"openai\":{\"type\":\"api\",\"key\":\"$OPENAI_API_KEY\"}}"
export OPENCODE_F62_LOG_DIR=/tmp/f62-public
mkdir -p "$OPENCODE_F62_LOG_DIR"
export OPENCODE_DISABLE_PROJECT_CONFIG=1 OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1
export OPENCODE_CONFIG_CONTENT='{"$schema":"https://opencode.ai/config.json","plugin":[],"agent":{"probe":{"mode":"primary","model":"openai/gpt-5.5","variant":"xhigh","prompt":"You are a math helper.","permission":{"read":"deny","glob":"deny","grep":"deny","list":"deny","bash":"deny","edit":"deny","write":"deny"}}}}'
echo "What is 2+2?" | opencode run --agent probe --format json
```

Minimal repro on the **Codex backend** (heading-only reasoning): omit
the `OPENCODE_AUTH_CONTENT` override; opencode falls through to the
stored OAuth.

## Continuing and forking sessions

Two forms of resumption; three forms of fork; one form of revert. Get these
wrong and probe results silently contaminate the parent session or measure
the wrong branch.

### CLI: `--session $ID` alone appends to parent — use `--fork` for probes

```bash
opencode run --session ses_xxx < followup.md            # appends to parent
opencode run --session ses_xxx --fork < followup.md     # forks; parent untouched
```

`--fork` is **required** to create a new session. Without it, `--session $ID`
mutates the parent's transcript in place — silently invalidating any future
re-fork or re-audit of that session. R37 methodological note: R35's
`run-followup-mot2.sh` omitted `--fork`, likely mutating the parent E-series
sessions.

Rule for probe scripts: **always pass `--fork` when `--session` is set**, or
explicitly document why parent mutation is intentional.

CLI `--fork` does full-session fork (all messages kept). To rewind and fork
at a specific message, use HTTP (below).

### HTTP: `POST /session/:sid/fork` with `{messageID}` rewinds and forks

The CLI has no message-truncating fork. Use the HTTP API:

```bash
# 1. Start the HTTP server on the same DB
opencode serve --port 4096 --hostname 127.0.0.1 > /tmp/oc-serve.log 2>&1 &
sleep 4

# 2. Enumerate messages to find the rewind target's messageID
opencode export ses_xxx 2>/dev/null | \
  jq -r '.messages | to_entries[] | "L\(.key+1) id=\(.value.info.id) role=\(.value.info.role) parts=\(.value.parts|length)"'

# 3. Fork at a chosen messageID (drops that message and everything after)
curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"messageID":"msg_xxx"}' \
  http://127.0.0.1:4096/session/ses_xxx/fork | jq
# → returns Session.Info with a new .id

# 4. Continue the fork via CLI (or HTTP /session/:sid/message)
opencode run --session <new-sid> < probe.md
```

Semantics from `packages/opencode/src/session/session.ts:677`:

```typescript
for (const msg of msgs) {
  if (input.messageID && msg.info.id >= input.messageID) break
  ...
}
```

The messageID and everything after are dropped. Passing no `messageID` in the
payload gives full-session fork (same as CLI `--fork`).

**Do NOT `tail -n +2` on `opencode export` stdout.** The *"Exporting session:
…"* line is on stderr; stripping the first stdout line removes the JSON's
opening `{`. Use `2>/dev/null` to drop stderr; leave stdout alone.

### HTTP: `POST /session/:sid/revert` mutates in place (destructive)

`revert` marks the session for rewind on next prompt; the abandoned tail is
permanently dropped by `cleanup()` at the next prompt turn. Payload:
`{"messageID": "msg_xxx", "partID": "prt_xxx"?}`.

`POST /session/:sid/unrevert` restores. Cannot restore after `cleanup` fires
(next prompt).

**For probes: use fork, not revert.** Fork preserves the parent; revert is
one-way and only useful for interactive TUI rewind.

### R37 P5 recipe (rewind-fork + inject probe at pre-decision points)

```bash
opencode serve --port 4096 --hostname 127.0.0.1 > /tmp/oc-serve.log 2>&1 &
sleep 4

for label_msgid in "L6|msg_a..." "L12|msg_b..." "L14|msg_c..."; do
  IFS='|' read -r label msgid <<< "$label_msgid"
  new_sid=$(curl -s -X POST -H 'Content-Type: application/json' \
    -d "{\"messageID\":\"$msgid\"}" \
    http://127.0.0.1:4096/session/$PARENT/fork | jq -r .id)

  # Re-supply agent config since fork is a new session
  export OPENCODE_CONFIG_CONTENT='{"$schema":"...","agent":{...}}'
  opencode run --agent my-agent --session "$new_sid" --format json \
    --dir "$WORKDIR" < probe.md > "$OUT/$label-stdout.jsonl"
done

kill %1  # stop the server
```

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
- **Frontmatter is prompt text under `{file:...}`.** See the
  "System-prompt contamination" section above. Category-A frontmatter
  (probe descriptions, hypothesis statements, prior-cell outcomes) is
  the highest-severity leak channel and is not detectable from behavior
  alone — round-20 F90 named it after round 18/19 attributed the effect
  to spec design.
- **Model can silently fall through to "recent" default.** Without an
  explicit `model:` in the agent block or `--model` on the CLI,
  opencode picks from `~/.local/share/opencode/state/model.json`. Round
  18 hit this and got `openai/gpt-5.4`. Verify the model after every
  run with `agent-tools opencode-pretty <session> --agent` — the
  session header prints the resolved provider/model/variant.

## Wrapper note

`agent-tools opencode` is a thin wrapper that loads the repo `.env` and maps
the `OPENCODE_LANGFUSE_*` keys to the unprefixed `LANGFUSE_*` names the
opencode Langfuse plugin expects. Use `agent-tools opencode` only when you
need that env mapping; pure `opencode` is fine otherwise.
