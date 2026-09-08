# Claude Code System Prompt Snapshots

Captured: 2026-09-08 (`default`, all three models); 2026-08-22 (every other
sonnet-5 variant)
Version: claude-cli/2.1.235
Mode: interactive (real pty via `capture.py`, `--setting-sources project,local`)
Default captures include a project CLAUDE.md.

Directories are named for the model id the request carried, minus its `claude-`
prefix. Aliases are repointed as models ship — `opus` meant `claude-opus-4-6` in
the 2.1.143 capture and `claude-opus-5` here — so an alias-named directory
changes meaning between captures while its path stays put.

## Files

| File | What |
|---|---|
| `<model-id>/<variant>/system-prompt.md` | System prompt blocks, separated by `---BLOCK_SEPARATOR---` |
| `<model-id>/<variant>/request.json` | Full API request body. Metadata redacted. |
| `<model-id>/<variant>/summary.json` | Block count, token counts, tool inventory |
| `capture.py` | Captures one variant via pty + MITM proxy |
| `regenerate.py` | Drives `capture.py` across every variant, writes `summary.json` |
| `scripts/intercept/` | MITM proxy for API call logging (see `scripts/intercept/README.md`) |

Variants: `default`, `custom-output-style`, `system-prompt`, `system-prompt-file`,
`append`, `subagent`.

### Subagent captures

`capture.py --subagent` adds a `subagents/` directory:

| File | What |
|---|---|
| `subagents/NNN-system-prompt.md` | System prompt for subagent N |
| `subagents/NNN-request.json` | Full API request for subagent N |
| `subagents/NNN-summary.json` | Block structure and tools for subagent N |

Subagent requests are identified by `cc_is_subagent=true` in the billing header,
not by size or tool count — the security-monitor call (below) also carries tools
and a large system prompt.

## Credentials

The spawned child needs its own Claude credentials. Claude Code strips
`CLAUDE_CODE_OAUTH_TOKEN` from tool subprocess environments, so a capture
launched from inside a Claude Code session inherits none, and
`~/.claude/.credentials.json` is empty when the session itself authenticates by
env var. Export the token before running:

```bash
set -a && . /workspace/.env && set +a   # or wherever the token lives
```

`capture.py` refuses to spawn when neither source has credentials. Without the
guard the child renders "Not logged in", issues zero API calls, and the failure
surfaces only as an empty capture.

## System prompt structure (v2.1.235, interactive mode)

The `system` array carries 4 text blocks. Blocks 2 and 3 carry `cache_control`;
only block 2 sets `scope: global` (block 3 omits `scope`, so it falls back to
org scope). Same layout as 2.1.143.

| Block | Content | Cache | Opus 4.7 | Sonnet 5 | Opus 5 |
|---|---|---|---|---|---|
| 0 | Billing header (`cc_version=2.1.235...`) | none | 84 | 82 | 84 |
| 1 | Identity (`"You are Claude Code, Anthropic's official CLI for Claude."`) | none | 24 | 24 | 24 |
| 2 | Static behavioral rules | 1h, global scope | 3,285 | 3,247 | 393 |
| 3 | Output style, session guidance, memory, environment, scratchpad, context mgmt, gitStatus | 1h, org scope | 5,938 | 6,017 | 3,361 |

Total: 9,329 (opus-4-7) / 9,368 (sonnet-5) / 3,860 (opus-5) tokens.

Token counts from the Anthropic count_tokens API.

### The prompt split is per model id, not per model family

2.1.235 ships two different default prompts and picks between them by model id.
`sV` (`globals/21.js:13394` in the 2.1.235 decompile) branches on `aT`, which
resolves through `EAb` (`globals/06.js:9819`): every id containing `claude-3-`,
`haiku` or `sonnet`, plus `claude-opus-4-0` through `claude-opus-4-7`, gets the
older multi-section prompt; anything else — `claude-opus-5` here — gets the
compressed one. Both bodies ship in the same binary, so a version number does
not identify which prompt a session received.

Opus 4.7 is captured alongside Opus 5 because it is the nearest model on the
other side of that branch: the pair isolates the prompt difference from every
other opus-vs-sonnet difference.

Through 2.1.143 all models received byte-identical prompt text and differed only
in tokenizer. That is no longer true on either axis.

The tokenizers now agree: block 1 is the same 57-character string and counts 24
tokens under all three models. The ~38% opus inflation documented for
`claude-opus-4-7` vs `claude-sonnet-4-6` is gone.

The text diverges by branch, not by family — opus-4-7 sits with sonnet:

| | Opus 4.7 | Sonnet 5 | Opus 5 |
|---|---|---|---|
| Block 2 | 10,676 chars | 10,574 chars | 1,210 chars |
| Block 3 | 18,579 chars | 18,812 chars | 10,231 chars |

Opus 5's block 2 replaces the other two models' `# System` / `# Doing tasks` /
`# Executing actions with care` / `# Using your tools` / `# Tone and style`
sections with a single five-bullet `# Harness` section. Its block 3 adds
`# Delivering work` and `# Corrections` sections the others do not receive.
Comparisons must therefore name a model; there is no longer one "the system
prompt".

Opus 4.7 and sonnet-5 differ in three lines only, all downstream of which tools
each model is served rather than of the prompt text itself:

| Line | Opus 4.7 | Sonnet 5 |
|---|---|---|
| `Use TaskCreate to plan and track work...` | present | absent |
| model identity in `# Environment` | `Opus 4.7` | `Sonnet 5` |
| `EndConversation (deferred tool): ...` | absent | present |

`ldE` emits the task bullet only when a task tool is in the request, and the
`EndConversation` hint only when that tool is; opus-4-7 is served
`TaskCreate`/`TaskGet`/`TaskList`/`TaskUpdate` and no `EndConversation`, and the
5-family models the reverse.

### Behavioral changes in block 2 (sonnet, vs 2.1.143)

- Destructive-action policy gained a reversibility preference (move/rename/stash
  over delete), an explicit carve-out for self-created scratch files, a
  mandatory `git status` before work-discarding git commands, and a
  secret-review step before pushing.
- `Use TaskCreate to plan and track work` was dropped along with the task tools.

### Behavioral changes in block 3 (sonnet, vs 2.1.143)

- New: they/them default for unstated pronouns, applied to visible thinking too.
- New: `# Scratchpad Directory` — a session-specific path under
  `/tmp/claude-0/<project-slug>/<session-id>/scratchpad` that the model is told
  to use instead of `/tmp`.
- New: act-when-you-have-enough-information guidance in `# Context management`.
- New: `EndConversation` usage note.
- New: `<total_tokens>N tokens left</total_tokens>` budget line.
- Subagent guidance was rewritten around `subagent_type: "fork"`, which inherits
  the parent's full context and runs in the background. The old
  Explore-for-broad-exploration bullet is gone.
- `/ultrareview` is now documented as a deprecated alias for `/code-review ultra`.
- The `/schedule` offer policy paragraph was removed.

## Tools

13 upfront tools plus one `DeferredToolPlaceholder` entry flagged
`defer_loading: true`:

```
Agent, Artifact, AskUserQuestion, Bash, Edit, ListAgents, Read,
ReportFindings, ScheduleWakeup, Skill, ToolSearch, Workflow, Write
```

Against 2.1.143: **added** `Artifact`, `ListAgents`, `ReportFindings`,
`Workflow`; **removed** `ShareOnboardingGuide`.

Upfront tool definitions cost 31,542 tokens (opus-4-7) / 31,221 (sonnet-5) /
25,546 (opus-5), against 10,559 / 14,596 in 2.1.143. Two tools new in 2.1.235
account for most of the rise: `Workflow` (19,290 chars of description) and
`Artifact` (12,564).

`Artifact`'s description grew 11,175 -> 12,564 chars between the 2026-08-22 and
2026-09-08 captures, adding an "Artifact database" paragraph, with no CLI
upgrade in between — both captures are 2.1.235.cf9. Tool descriptions therefore
track account-side feature rollout, not only the installed version, and a tool
token count is only comparable against others captured the same day.

Tool descriptions are model-specific, the same way the system prompt is. Opus 5
gets a much shorter description for every tool that predates 2.1.235, while the
newer tools are byte-identical across models:

| Tool | Sonnet 5 | Opus 5 |
|---|---|---|
| Bash | 10,067 chars | 1,043 |
| Agent | 7,081 | 1,811 |
| Read | 1,782 | 790 |
| Edit | 1,094 | 360 |
| Write | 618 | 240 |
| AskUserQuestion | 1,531 | 1,786 |
| Artifact, Workflow, Skill, ToolSearch, ScheduleWakeup, ListAgents, ReportFindings, DeferredToolPlaceholder | identical | identical |

`AskUserQuestion` is the one tool whose opus description is longer.

18 deferred tools for the 5-family models, listed by name in a system-reminder
rather than as `tools[]` entries:

```
CronCreate, CronDelete, CronList, DesignSync, EndConversation, EnterPlanMode,
EnterWorktree, ExitPlanMode, ExitWorktree, Monitor, NotebookEdit,
PushNotification, RemoteTrigger, SendMessage, TaskOutput, TaskStop, WebFetch,
WebSearch
```

Opus 4.7 gets 21: the same list minus `EndConversation`, plus `TaskCreate`,
`TaskGet`, `TaskList` and `TaskUpdate`. The deferred roster is therefore
model-conditioned too, and it is what drives the three-line prompt difference
tabulated above.

Against 2.1.143: **added** `DesignSync`, `EndConversation`, `SendMessage`;
**removed** `TaskCreate`, `TaskGet`, `TaskList`, `TaskUpdate` — removed for the
5-family models only; opus-4-7 still receives all four. The
`mcp__claude_ai_Google_Drive__*` tools present in the 2.1.143 capture are absent
here — MCP tools depend on the capturing account's connectors, not on the CLI
version.

The Bash tool description still instructs `NEVER use the TaskCreate or Agent
tools` in its git-commit examples. On the 5-family models that names a tool
absent from both lists; on opus-4-7 `TaskCreate` is still deferred, so there the
instruction still has a referent.

## messages structure (model-gated, not version-gated)

System-reminders moved out of the first user message into a dedicated
`role: "system"` message placed **after** it — on the 5-family models only.
Opus 4.7 on this same 2.1.235 build still receives the 2.1.143 layout, with
every reminder inline in `messages[0]`, so this is the same per-model-id split
the system prompt shows, not a version change.

| | 2.1.143, and 2.1.235 opus-4-7 | 2.1.235 5-family |
|---|---|---|
| `messages[0]` (user) | deferred tools, agent types, skills, auto mode, token budget, claudeMd, user text | claudeMd, user text |
| `messages[1]` | — | `role: "system"`: deferred tools, agent types, skills, auto mode, token budget |

Measured over the messages array, minus a bare `"x"` request:

| | Opus 4.7 | Sonnet 5 | Opus 5 |
|---|---|---|---|
| `messages[0]` | 4,664 | 350 | 347 |
| `role: "system"` message | — | 4,303 | 3,961 |
| total | 4,664 | 4,653 | 4,308 |

The reminder payload therefore costs about the same either way; only its
placement, and so its cache behaviour, differs. Its size tracks the user's
installed skills and agents. Where the system message exists its `content` is a
list of blocks on the first turn and a bare string on later turns — both shapes
occur in one session.

New reminders in that message: the agent-type roster, `## Auto Mode Active`,
and `<total_tokens>N tokens left</total_tokens>`.

Auto mode is the default for an interactive session in 2.1.235. Two probes
differing only in `.claude/settings.local.json`: with `permissions.defaultMode`
unset the TUI shows `auto mode on` and the reminder is present; with
`defaultMode: "default"` both disappear. The other three reminders are present
either way. The reminder tells the model to bias toward acting without
clarifying questions, and repeats the `git status`-before-destructive-commands
and secret-review rules from block 2.

### Request parameters

| | 2.1.143 | 2.1.235 |
|---|---|---|
| `max_tokens` (sonnet) | 32,000 | 64,000 |
| `max_tokens` (opus) | 64,000 | 64,000 |
| model | `claude-sonnet-4-6` / `claude-opus-4-7` | `claude-sonnet-5` / `claude-opus-5` |
| `fallbacks` (opus only) | absent | `[{"model": "claude-opus-4-8"}]` |

`context_management` (`clear_thinking_20251015`, keep all), `diagnostics`,
`output_config` (`effort: max`), `stream`, and `thinking` (`adaptive`) are
unchanged.

### Billing header fields

`cc_version` and `cch` are unchanged. New: `cc_prompt_id` (a UUID, on every
request), `cc_prev_req` (on follow-up turns), and `cc_is_subagent=true` (on
subagent calls). All three vary per request, so dedup normalizes the entire
header line rather than individual fields.

The `cc_version` suffix (`2.1.235.cf9`, `.df1`, `.6db`…) varies by call type
within one session. It did so in 2.1.143 as well.

## `--system-prompt` behavior

Unchanged from 2.1.143. Replaces blocks 2-3 with the custom text; gitStatus is
still appended unconditionally; the identity block survives.

The table below describes the session you launch. It does not hold for the rest
of that session's life — a session that backgrounds itself loses the flag. See
"Background sessions do not inherit the flag" below.

All five rows are from the 2026-08-22 sonnet-5 set, so they are comparable with
each other; the `(none)` row is that day's default capture rather than the
2026-09-08 one tabulated above.

| Flag | Blocks | Sonnet tokens | What happens |
|---|---|---|---|
| (none) | 4 | 9,365 | Full default prompt |
| `--system-prompt` | 3 | 228 | Custom text replaces blocks 2-3; gitStatus appended |
| `--system-prompt-file` | 3 | 226 | Identical to `--system-prompt` (file read at startup) |
| `--append-system-prompt` | 4 | 9,376 | Full default prompt + custom text |
| output style (`Explanatory`) | 4 | 9,679 | Block 2 preamble swaps to the output-style framing |

`--append-system-prompt` inserts the custom text at the end of block 3, after
the context-management section and before gitStatus — same position as 2.1.143.

What `--system-prompt` removes (blocks 2-3): all behavioral rules, output style,
session-specific guidance, memory instructions, environment info, scratchpad
directory, context management.

What survives: billing header, identity, gitStatus, all upfront tool
definitions, the deferred-tool placeholder, and the system-role reminder message.

### Background sessions do not inherit the flag

A session that moves to the background is not the same process. Claude Code
spawns a fork and hands the transcript over; the fork's argv is built from a
fixed list in `X_r` (`globals/24.js:30356` of the 2.1.235 decompile):

```
--resume, --fork-session, --reply-on-resume, --add-dir…, --allowed-tools…,
--disallowed-tools…, --model, --effort, --permission-mode, --agent, --agents,
--append-system-prompt (only when keepParent, i.e. /fork)
```

`--system-prompt` and `--system-prompt-file` appear nowhere in that list, so a
custom prompt is **silently replaced by the default prompt** the moment a
session backgrounds. `--append-system-prompt` survives only a `/fork`, not a
background handoff. The job's `state.json` records the same truncated set under
`respawnFlags`, so resuming the job later does not restore the flag either.

Measured on one session, same machine, same minute:

| | Foreground (launched with `--system-prompt-file`) | After backgrounding |
|---|---|---|
| Blocks | 3 | 4 |
| Block 2 | prompt file verbatim (25,237 chars) + gitStatus | CC default, 1,273 chars |
| Block 3 | — | 24,024 chars (CC default + output style) |
| argv | `--system-prompt-file <path>` | absent |

What still propagates: the process environment (`HTTPS_PROXY`,
`NODE_EXTRA_CA_CERTS`, `IS_SANDBOX`, `GIT_AUTHOR_*` were all present in the
fork), so proxy-based request capture keeps working across the handoff.

Consequence for prompt work: only settings-based configuration is durable
across a background handoff. An output style survives (it is read from
`settings.json` by the fork); a `--system-prompt-file` does not. A prompt that
must hold for every session therefore belongs in `output-styles/`, not in
`sys_prompt/`. See `docs/background-sessions.md` for the trigger and the
disable knobs.

### Sub-agent behavior

Neither `--system-prompt` nor `--append-system-prompt` propagates to sub-agents.
Each agent type gets its static persona regardless of parent flags.

Subagents now receive the identity line `"You are a Claude agent, built on
Anthropic's Claude Agent SDK."` — in 2.1.143 they got the interactive
`"You are Claude Code, Anthropic's official CLI for Claude."` line.

| Agent | Prompt identity | Model | Upfront tools |
|-------|----------------|-------|---------------|
| Explore | "file search specialist" | claude-sonnet-5 | Bash, Read, Skill, ToolSearch, DeferredToolPlaceholder |
| general-purpose | "an agent for Claude Code" | claude-sonnet-5 | Agent, Artifact, Bash, Edit, Read, Skill, ToolSearch, Write, DeferredToolPlaceholder |

Explore ran on `claude-haiku-4-5` in 2.1.143 and now runs on sonnet-5.
Subagents also went from a full upfront tool list (27 entries for Explore in
2.1.143) to the deferred mechanism.

## Security-monitor calls

A session makes side-channel classification calls that are neither the main
conversation nor a subagent — a harm classifier run against pending tool calls:

- model `claude-sonnet-5`, `max_tokens: 64`, no tools
- a ~112K-character system prompt, cached 1h, opening `You are a security …`
  with `## Threat Model`, `## HARD BLOCK`, `## SOFT BLOCK`, `## ALLOW`,
  `## Classification Process`, and `## Output Format` sections
- messages carry the user's CLAUDE.md and a `<transcript>` of the pending call
- two response forms, both labelled "Stage 1" (stage 2 applies user intent and
  the ALLOW exceptions): `<severity>N</severity>` — observed 2 and 5 — and
  `<block>yes|no</block>`, each terminated by a stop sequence

Observed firing once per tool call (`Agent` and `Bash` seen) in sessions where
the harness evaluates permissions. A session run with
`--dangerously-skip-permissions` produced none across hundreds of tool calls,
and a session that made no tool call produced none.

`capture.py` does not write these to the snapshot; the `cc_is_subagent` filter
excludes them.

## Interactive vs `-p` mode differences

These captures use interactive mode (real pty). Measured against a `-p` run on
the same version:

| | Interactive | `-p` mode |
|---|---|---|
| Identity (block 1) | `"You are Claude Code, Anthropic's official CLI for Claude."` | `"You are a Claude agent, built on Anthropic's Claude Agent SDK."` |
| `cc_entrypoint` | `cli` | `sdk-cli` |
| gitStatus | Appended | Appended |
| Upfront tools | 13 | 11 — no `Artifact`, no `AskUserQuestion` |
| `## Auto Mode Active` reminder | present (session was in auto mode) | absent |

gitStatus **is** appended in `-p` mode as of 2.1.235; through 2.1.143 it was
not. Block 2 is byte-identical to the interactive capture (10,574 chars), so
the behavioral rules and `--system-prompt` replacement logic are the same in
both modes.

## How to re-capture

```bash
# ANTHROPIC_TOKEN_COUNT_API_KEY must be in /repos/claude-config/.env
# (loaded automatically by both scripts via claude_config.config.load()).
# See /repos/claude-config/.env.example for the full list of expected keys.
# CLAUDE_CODE_OAUTH_TOKEN must be exported — see "Credentials" above.

./capture.py                                        # default prompt
./capture.py --system-prompt "Your custom prompt"
./capture.py --system-prompt-file /path/to/prompt.txt
./capture.py --append-system-prompt "Extra instructions"
./capture.py --subagent                             # Explore + general-purpose

./regenerate.py --model claude-sonnet-5 default     # one variant
./regenerate.py --model claude-opus-4-7 default     # the other prompt branch
./regenerate.py --model claude-opus-5               # all variants
```

Do not run two `regenerate.py` invocations in parallel — they share
`capture-output/` and `~/.claude/requests-log/` and will overwrite each
other's intermediates.

A capture is not byte-reproducible: the billing header fingerprints, the
per-session temp working directory, the scratchpad UUID, and gitStatus all
change per run. Token totals are still stable — four `sonnet-5/default` runs
gave 9,359 / 9,365 / 9,365 / 9,368, and three `opus-5/default` runs gave
3,871 / 3,866 / 3,860. Blocks 2 and 3 are byte-identical between runs apart from
those paths, so the divergence above is a property of the build, not of one
capture: the 2026-09-08 sonnet-5 recapture reproduced the 2026-08-22 one exactly
except for the billing fingerprints and those paths.

`capture.py` strips every `CLAUDE_CODE_*` variable except
`CLAUDE_CODE_OAUTH_TOKEN` from the spawned session's environment, because each
one is a knob that can change what the child's prompt says — a capture that
inherits one records this machine's setup instead of the CLI's behaviour, and
the committed snapshots stop being comparable with no diff to show for it. Two
that demonstrably do so: `CLAUDE_CODE_TMPDIR` moves the scratchpad path the
prompt prints, so every capture instead reflects cc's own default temp root
(`/tmp` here — `os.tmpdir()` falls back to it once `$TMPDIR` is unset too); and
`CLAUDE_CODE_FORK_SUBAGENT=0`, which this repo's `settings.json` has set since
c70788a (2026-09-04), swaps the subagent guidance from the `fork` paragraph to
the older Agent/Explore bullets. The first opus-4-7 capture attempt inherited
the latter and was discarded. The scratchpad paths quoted throughout this
document are spelled as they appear in the captured artifacts under the default
root, not as they would read from inside a redirected session.

`capture.py` spawns claude with a real pty via `pty.fork()` and
`--setting-sources project,local` to isolate from user settings, sends a canary
message, then extracts the system prompt from the intercepted API request. A
placeholder CLAUDE.md is created in the temp working directory so the capture
includes the claudeMd context block. Output goes to `capture-output/`
(system.txt, request.json, summary.json) and stdout.

### Why pty (not heredoc/pipe)

Piping stdin (heredoc, `echo |`, subprocess with piped stdin) makes claude
detect non-interactive mode, which changes the identity block and skips
gitStatus. `pty.fork()` provides a real pty on both stdin and stdout so claude
runs in true interactive mode.

### Bracketed paste

Claude Code enables xterm bracketed-paste mode (`\x1b[?2004h`). A `\r`
concatenated into the same write as the message body gets absorbed into the
paste payload instead of submitting. `spawn_claude` therefore writes the
message and the submit-Enter as separate `os.write()` calls with a short
`time.sleep` between them.

### Proxy log layout

The MITM proxy writes logs per-session under
`~/.claude/requests-log/<session_id>/NNNN.json`. Concurrent Claude Code
sessions on the same machine all write under the same root. `capture.py`
filters logs by `session.pid` matching its spawned claude PID (the proxy
resolves PID from `~/.claude/sessions/<pid>.json`); mtime alone is not
sufficient to isolate one capture's traffic.

The proxy logs request bodies only, never headers, so no credential reaches
disk.
