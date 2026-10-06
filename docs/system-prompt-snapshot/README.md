# Claude Code System Prompt Snapshots

Captured: 2026-09-11 (all models), plus `logged-in` and `logged-in-no-artifact` on
2026-09-30 and `logged-in-tool-search-loaded` on 2026-10-02.
Version: claude-cli/2.1.269
Mode: interactive (real pty via `capture.py`, `--setting-sources project,local`)
Default captures include a project CLAUDE.md.

This file is the procedure: what each variant is, what credential it needs, how to re-capture
and what goes wrong. What the captured prompt and tools *say* for this build is
`what-the-model-gets.md` and eight `notes/cc-2.1.269-*.md` records -- block sizes, the
per-model prompt split, what left block 3, the tool-roster delta, the flag flicker in the
upfront roster, the `messages[]` reminders, the request parameters, and the Fable/Mythos model
ids.

Previous snapshot was 2.1.235 (captured 2026-09-08 / 2026-08-22); `git show b318e59:docs/system-prompt-snapshot/...`
gives the exact 2.1.235 artifact for any path here. Every number below was re-derived from
the artifacts on disk; a 2.1.235 figure given for comparison is labelled as such.

Directories are named for the model id the request carried, minus its `claude-` prefix.
Aliases are repointed as models ship — `opus` meant `claude-opus-4-6` in the 2.1.143 capture
and means `claude-opus-5` here — so an alias-named directory changes meaning between captures
while its path stays put. 2.1.269 also ships `claude-fable-5`, `claude-fable-5-1`,
`claude-mythos-5`, `claude-mythos-5-1` and `claude-opus-4-8` as selectable ids; `fable-5/` and
`opus-4-8/` are captured (`default` only), the other three are not — see `notes/cc-2.1.269-fable-and-mythos-model-ids.md`.

## Files

| File | What |
|---|---|
| `<model-id>/<variant>/request.json` | Full API request body — the artifact of record. Metadata redacted. |
| `<model-id>/<variant>/prompt.md` | Everything in that request except the tool definitions: parameters, the tool roster in request order, every system block, every message |
| `<model-id>/<variant>/tools/<Name>.md` | One tool definition each — attributes, description, input schema |
| `<model-id>/<variant>/summary.json` | Block count, token counts, tool inventory |
| `builtin-skills/<name>.md` | What invoking that built-in skill injects into the context. Shared across models, not per-model: bodies measured byte-identical on opus-5 and sonnet-5 |
| `builtin-skills/manifest.json` | Per skill: delivery shape, which route reached it, size, sha256 |
| `capture.py` | Captures one variant via pty + MITM proxy |
| `capture_skills.py` | Captures every built-in skill's body into `builtin-skills/` |
| `regenerate.py` | Drives `capture.py` across every variant, writes `summary.json` |
| `render_capture.py` | Renders `prompt.md` and `tools/` from a `request.json`; `--tree <root>` does every capture beneath a directory |
| `scripts/intercept/` — repo root, not under this directory | MITM proxy for API call logging (see `scripts/intercept/README.md`) |

### Reading a capture as a diff

`request.json` is the artifact of record and is unreadable as a diff: one line per string with
every newline escaped, so a reworded paragraph inside `Artifact`'s 25,099-character description
arrives in `git diff` as a single changed line 25,099 characters wide. `prompt.md` and
`tools/<Name>.md` carry the same content as text, for the person reading that diff across a
release. They are derived — never hand-edit them: `./render_capture.py --tree .` rebuilds them
and `tests/test_snapshot_rendering.py` fails when they drift from the `request.json` beside them.

The split is per tool because that makes the diff legible — a changed tool is one file with
line-level hunks, an unchanged one is absent, an added or removed tool is an added or removed
file — and everything that is not a tool stays in one file because it is read as a whole: a
section moving between the system prompt and the messages, which 2.1.269 did to the environment
block, is only visible if both sit in the same diff.

From 2.1.269 on the review at an upgrade is `git diff` after re-capturing. An older release's
captures predate the layout, so render them into it first:

```bash
mkdir -p /tmp/old/opus-5/default
git show b318e59:docs/system-prompt-snapshot/opus-5/default/request.json \
  > /tmp/old/opus-5/default/request.json
./render_capture.py --tree /tmp/old
diff -ru -x request.json -x summary.json /tmp/old/opus-5/default opus-5/default
```

### What a default capture leaves out, and where it now lives

A `default` capture records two things by name only; both are text the model receives and
change between releases:

| Withheld from `default` | Now captured in |
|---|---|
| The 18 deferred tools' descriptions and schemas — the reminder lists their names, and `tools/` holds one `DeferredToolPlaceholder` stub | `<model-id>/tool-search-loaded/tools/` |
| The Chrome and claude.ai connector tools entirely — a `default` capture does not even list their names | `<model-id>/logged-in-tool-search-loaded/tools/` |
| The 17 built-in skills' bodies — the reminder carries each name and description, never the text an invocation injects | `builtin-skills/` |

Both are captured in the default configuration. The deferred half works because `ToolSearch`
does not do what its own description says: it advertises a `<functions>` block, and no such
block exists anywhere in the binary except that sentence. It returns a `tool_result` of
`{"type": "tool_reference", "tool_name": ...}` entries plus the text `Tool loaded.`, and the
**server** expands those into the next request's `tools` array — measured, 15 tools before the
call and 33 after — so the schemas arrive in a request, which this directory already renders.

`tool-search-loaded` is captured for opus-5 and sonnet-5, enough to separate per-model from
shared: of the 18 deferred tools only `WebFetch` (676 characters on opus-5, 1,909 on sonnet-5)
and `WebSearch` (312 against 1,322) take the lean/full split; the other 16 are byte-identical.

Variants: `default`, `custom-output-style`, `system-prompt`, `system-prompt-file`, `append`,
`tool-search-loaded`, `logged-in`, `logged-in-no-artifact`, `logged-in-tool-search-loaded`,
`subagent`. Captured: the original
six plus `tool-search-loaded` for sonnet-5; `default` for opus-4-7; `default`,
`system-prompt-file`, `tool-search-loaded`, `logged-in`, `logged-in-no-artifact` and
`logged-in-tool-search-loaded` for opus-5;
`default` only for fable-5 and opus-4-8 — both added after an account entitlement upgrade
partway through the capture session, opus-4-8 specifically to test whether fable's prompt was
a Fable-family oddity or per-model (per-model; see `notes/cc-2.1.269-prompt-split-per-model-id.md`).

None of them is the configuration this repo itself runs: `scripts/claude.sh` launches
`--dangerously-skip-permissions` with `--system-prompt-file`, and a capture takes the default
permission mode, which is why the bypass-permissions reminder a `claude.sh` session
demonstrably carries appears in no file here (see `notes/cc-2.1.269-messages-and-reminders.md`). `regenerate.py` defines a `bypass-permissions` variant for it, not yet captured, so
that directory is absent rather than empty.

### The three `logged-in` variants

Every other variant exports `CLAUDE_CODE_OAUTH_TOKEN` and is MCP-free. These three drop it
(`capture.py --capture-no-oauth-token`) so the child authenticates from
`~/.claude/.credentials.json`, the condition under which it reaches the Chrome extension and the
claude.ai connectors.

The mechanism is an OAuth scope check, not a preference. `WFt()`
(`src/chunk-gppff98a.js:16875-16887`) returns false before it looks at any flag or setting
when the token's scopes are rejected by `/api/oauth/validate`, and its own log line says which
tokens those are: *"needs user:profile, user:office, or user:ccr_inference; env-var and
setup-token sessions default to user:inference only"*. An exported `CLAUDE_CODE_OAUTH_TOKEN`
child therefore cannot reach Chrome however it is flagged; the interactive login's token
carries `user:profile` and does.

`logged-in-no-artifact` adds
`CLAUDE_CODE_DISABLE_ARTIFACT=1` through `--capture-child-env`, which is how a variant names a
`CLAUDE_CODE_*` knob it wants after the wholesale strip. The pair measures the `Artifact` tool
with the credential held fixed: 33,465 tool tokens against 13,255, 14 upfront tools against 13,
the three `artifact-*` skills listed against absent, the 57 deferred names unchanged —
`notes/artifact-tool-roster-cost.md`.

`logged-in-tool-search-loaded` is where the Chrome and connector tools' descriptions and
schemas live, and the only place they do. Both sets are MCP, and the deferral predicate
(`h()`, `src/chunk-sspbjbr8.js:52-57`) defers every MCP tool unconditionally — `if (e.isMcp
=== !0) return !0;` (`:53`) — so `logged-in` records their names and not one definition.
The variant adds `--chrome` and the `tool-search-loaded` machinery to the `logged-in`
credential: `WFt()` reads the flag ahead of both `CLAUDE_CODE_ENABLE_CFC` and the
`claudeInChromeDefaultEnabled` setting, and that setting lives in `~/.claude.json`, which
`--setting-sources project,local` does not filter — so without the flag the variant's Chrome
roster would be a property of the operator's machine. Captured 2026-10-02: 13 upfront, 94
deferred definitions loaded (22 `mcp__claude-in-chrome__*`, 51 `mcp__claude_ai_*`, 21
built-in), 31,513 tool tokens, 4,793 system tokens.

Its 91 reminder names against `logged-in`'s 57 are two days of account change, not a release:
the connector list gained Gmail (30 tools) and Indeed (4) between 2026-09-30 and 2026-10-02.
The pair is not same-day comparable, and `logged-in` is deliberately not re-captured — it and
`logged-in-no-artifact` are the measured pair behind
`notes/artifact-tool-roster-cost.md`, and re-capturing one of them would strand that note's
figures. `check_deferred_loaded` compares a load against its own `requires_variant` sibling
for this reason: verified against `default`, which knows only its 18 names, a capture whose 22
Chrome schemas never arrived passes.

The tool definitions carry no account data — the only mail addresses in the 73 MCP definitions
are Google's own documentation placeholders (`gduser1@workspacesamples.dev`,
`user@example.com`), and there are no ids, tokens or paths. The user's own address does appear
in every capture here including this one, in the `userEmail` system-reminder inside
`messages[0]`; that is not new with this variant.

### Built-in skill captures

`builtin-skills/` holds what invoking each of the 17 built-in skills injects — 512,397
characters in total, none of it in a `default` capture; the per-skill table and the capture
conditions are in `builtin-skills/README.md`. Three conditions change the result: interactive
rather than `-p`, or the skills gated on the `Artifact` tool are unreachable and `design`
degrades from 55,398 characters to a 169-character stub; `--setting-sources project,local`, or
`design` and `code-review` degrade too; a repo with a resolvable `origin/HEAD`, or
`/security-review` — whose prompt interpolates `` !`git diff origin/HEAD...` `` — injects nothing
at all. Each failure produces a plausible short body rather than an error, which is why
`capture_skills.py` refuses to write a body that opens with harness text and
`tests/test_builtin_skills.py` checks the committed files for the same thing: the first run
wrote Claude Code's type-ahead suggester prompt into two files and a bare system reminder into
a third.

### Subagent captures

`capture.py --subagent` adds a `subagents/` directory:

| File | What |
|---|---|
| `subagents/NNN/request.json` | Full API request for subagent N |
| `subagents/NNN/prompt.md` | Everything in it except the tool definitions |
| `subagents/NNN/tools/<Name>.md` | One tool definition each — the rosters are smaller than the parent's (5 for Explore, 9 for general-purpose, against 15) |
| `subagents/NNN/summary.json` | Block structure and tools for subagent N |

Subagent requests are identified by `cc_is_subagent=true` in the billing header, not by size or
tool count — the security-monitor call (below) also carries tools and a large system prompt.
Still true in 2.1.269: `sonnet-5/subagent`'s two children carry it and their own `cc_prompt_id`.

## Credentials

The spawned child needs its own credentials: `CLAUDE_CODE_OAUTH_TOKEN` in the environment, or
an access token in `~/.claude/.credentials.json`. Claude Code strips the variable from tool
subprocess environments, so a capture launched from inside a session inherits none and falls
back to the file — empty when the session itself authenticates by env var, populated after an
interactive login.

**Export the token even when the credentials file would do.** The two sources produce different
captures: the credentials-file login reaches MCP and the exported token does not. Two
`claude-opus-5` `default` captures taken minutes apart on 2.1.269, identical in every flag:
with the exported token, 15 `tools` entries, 18 deferred names, 3,338 system tokens; with the
credentials-file login, 18 entries, 57 deferred names (22 Chrome, 36 MCP in all), the
`Claude in Chrome browser automation` and `MCP Server Instructions` prompt sections,
`ListMcpResourcesTool` and the two `ReadMcpResource*`, 4,756 system tokens. The 14 upfront
names are the same in both. The exported token reproduces the committed rosters exactly —
every capture here but the `logged-in` three is an MCP-free capture, and a re-capture without
the export is not comparable to one. That is a property of the credential, not of this machine:
the Chrome extension was already paired when the 2026-09-11 snapshot was taken (its tool names
appear in intercepted sessions from 2026-08-22 on), and the snapshot records none of them. The
mechanism is the OAuth scope set the two credentials carry — see "The three `logged-in`
variants".

Three knobs that are not `CLAUDE_CODE_*` decide the same thing, so `capture.py` drops them from
the child along with the prefix: `ENABLE_CLAUDEAI_MCP_SERVERS`, which this repo's
`settings.json` has exported into every tool subprocess since `56168fdf` and which would have
silently cost a re-capture its 36 connector tools; `ENABLE_TOOL_SEARCH`, which off ends
deferral so every definition arrives upfront; and `ANTHROPIC_BASE_URL` with the two
`ANTHROPIC_*` tokens, which the `kimi.sh` and `zai.sh` launchers export and which would send
the child to another provider or make it an API-key session with no OAuth scope at all.

```bash
set -a && . /workspace/.env && set +a   # or wherever the token lives
```

That file carries a second `CLAUDE_CODE_OAUTH_TOKEN`, commented out, for when the active one is
out of credit — the failure reads as a quota error on the first request, not as an auth error.
Swap which line is commented rather than exporting both.

**Counting tokens is a separate credential.** Every figure in a `summary.json` comes from the
free `count_tokens` endpoint, which `ANTHROPIC_TOKEN_COUNT_API_KEY` reaches — and an API-key
account at a zero credit balance is rejected there too, with a 400 naming billing, which stops
a capture after the session has already run. `capture.py` falls back to the
`~/.claude/.credentials.json` access token as a bearer and prints which credential answered.
The two are interchangeable for this purpose: checked on 2026-10-02 against every committed
`opus-5` `summary.json`, the OAuth credential reproduced each `system_tokens` and
`tools_total_tokens` exactly.

`capture.py` refuses to spawn when neither source has credentials. Without the guard the child
renders "Not logged in", issues zero API calls, and the failure surfaces only as an empty
capture.

## `--system-prompt` behavior

Replaces blocks 2-3 with the custom text; the identity block survives. **Changed from
2.1.235**: `gitStatus` is no longer appended to the replacement block — it moved into
`messages[0]` unconditionally, so it survives an override the way `userEmail` always has.
Confirmed: `sonnet-5/system-prompt`'s block 2 shrank from 341 chars (custom text + gitStatus)
to 27 (custom text only, `"You are a custom assistant."` from `regenerate.py`'s
`CUSTOM_PROMPT`); the 314-character difference is exactly the gitStatus block.

`system_tokens` for the replacement-prompt variants (exact, from `summary.json`; opus-5's
`system-prompt-file` is new this round, sonnet-5's three were captured both times):

| Flag | Sonnet 5 (2.1.235 -> 2.1.269) | Opus 5 (2.1.269) |
|---|---|---|
| `--system-prompt` | 228 -> 116 | not captured |
| `--system-prompt-file` | 226 -> 114 | 117 |

The drop is `gitStatus` leaving the block. `--append-system-prompt` still inserts the custom
text at the end of block 3, now truly the *last* thing there.

What `--system-prompt` removes (blocks 2-3): all behavioral rules, output style,
session-specific guidance, memory instructions, the ecosystem-trivia `# Environment` remnant,
context management. What survives: billing header, identity, the CLAUDE.md wrapper reminder
with its "these instructions OVERRIDE any default behavior" line, `userEmail`+`gitStatus`+the
Attribution reminder (all in `messages[0]`), all upfront tool definitions, the deferred-tool
placeholder, and one system-role block (or a prepend to `messages[0]`) holding `# Environment`,
the model-identity line, the deferred-tool listing, the agent-type roster and every skill
description. Read that last item as behaviour, not facts: the skill and agent text is
Anthropic-authored guidance — trigger conditions, roster entries telling the model when to
delegate — and an override displaces none of it (`sonnet-5/system-prompt/prompt.md`,
`opus-5/system-prompt-file/prompt.md`, under `## messages[1] system, content[0]`).

### Background sessions do not inherit the flag

**The argv exclusion still holds; the measurements below were not retaken.** The forked-argv
list is now at `src/chunk-8w9chsdq.js:767`, and it carries `--resume`, `--fork-session`,
`--reply-on-resume`, `--add-dir`, `--allowed-tools`, `--disallowed-tools`, `--model`,
`--effort`, `--permission-mode`, `--agent`, `--agents`, `--name` and `--append-system-prompt`
— and neither `--system-prompt` nor `--system-prompt-file`. So a custom prompt is still replaced
by the default one the moment a session backgrounds.

No backgrounding capture was retaken for 2.1.269; `docs/background-sessions.md` is the
maintained source, re-verified against 2.1.269 separately. To re-verify here: capture a
session with `--system-prompt-file`, trigger a background handoff, diff its prompt, and
re-trace the forked-argv function by grepping a flag literal such as `--fork-session`.

### Sub-agent behavior

Neither `--system-prompt` nor `--append-system-prompt` propagates to sub-agents (unchanged; not
re-tested this round, since no capture combined `--subagent` with a prompt override).

The identity line subagents receive — `"You are a Claude agent, built on Anthropic's Claude
Agent SDK."` — is byte-identical to 2.1.235 (confirmed by diff). Tool rosters are unchanged:

| Agent | Prompt identity | Model | Upfront tools |
|-------|----------------|-------|---------------|
| Explore | "file search specialist" | claude-sonnet-5 | Bash, Read, Skill, ToolSearch, DeferredToolPlaceholder |
| general-purpose | "an agent for Claude Code" | claude-sonnet-5 | Agent, Artifact, Bash, Edit, Read, Skill, ToolSearch, Write, DeferredToolPlaceholder |

Neither subagent type receives `SendFeedback` — the one new upfront tool this round is scoped
to the main session's own tool list. What changed for subagents is exactly the
block-3-relocation finding above, applied to their own (much shorter) persona block: the
`<env>` block, `"You are powered by..."`, `"Assistant knowledge cutoff..."`, the entire
`# Scratchpad Directory` section, and (for `general-purpose`) `gitStatus` are all removed from
the cached persona text and reappear in a new `role: "system"` message the same way the main
session's do — confirmed by diffing both `subagents/001/prompt.md` and `002/prompt.md` against
2.1.235.

## Security-monitor calls

**Not re-verified this round.** No fresh measurement of the side-channel harm-classifier calls
was attempted for 2.1.269 — doing so needs a live session making tool calls under a permission
mode that isn't `--dangerously-skip-permissions` (the 2.1.235 measurement notes that mode
suppresses these calls entirely), which this batch's captures don't provide. Treat the 2.1.235
description (model, prompt structure, `<severity>`/`<block>` response forms) as historical only.

## Interactive vs `-p` mode differences

**Not re-verified this round.** No `-p`-mode capture was retaken for 2.1.269. Given gitStatus
and the Environment block both moved to a messages-level reminder in interactive mode (above),
the old finding that "gitStatus is appended in `-p` mode too, block 2 is byte-identical" would
need rechecking specifically for whether `-p` mode gets the same new reminders — plausible, but
not established here. Settling it needs one `claude -p` capture on 2.1.269 compared the way the
2.1.235 doc compared it.

## How to re-capture

```bash
# ANTHROPIC_TOKEN_COUNT_API_KEY: claude_config.config.load() reads the checkout's own .env,
# resolved relative to the package. Unset, or on an account out of credit, counting falls
# back to the ~/.claude/.credentials.json token and says so on stderr.
# CLAUDE_CODE_OAUTH_TOKEN must be exported for every variant but the `logged-in` three, even
# when ~/.claude/.credentials.json holds a token: the two credentials produce different
# captures. See "Credentials" above.

./capture.py                                        # default prompt
./capture.py --system-prompt "Your custom prompt"
./capture.py --system-prompt-file /path/to/prompt.txt
./capture.py --append-system-prompt "Extra instructions"
./capture.py --subagent                             # Explore + general-purpose

./regenerate.py --model claude-sonnet-5 default     # one variant
./regenerate.py --model claude-opus-4-7 default     # the other prompt branch
./regenerate.py --model claude-opus-5               # all variants

# The Chrome and connector definitions. Needs the interactive login (see
# "Credentials"): with CLAUDE_CODE_OAUTH_TOKEN exported this variant captures a
# roster with no MCP in it at all, and nothing says so.
./regenerate.py --model opus logged-in-tool-search-loaded
```

Do not run two `regenerate.py` invocations in parallel — they share `capture-output/` and
`~/.claude/requests-log/` and will overwrite each other's intermediates.

### Trust-dialog default flipped — the failure this version will most likely hit

2.1.269's first-run trust dialog starts with the cursor on **"No, exit"** rather than the trust
option (2.1.235 defaulted to the trust option, so the bare `\r` `capture.py` sent was enough to
accept it). Confirming "No, exit" quits the child before it issues a single API call, and the
only symptom is `ERROR: No API calls captured.` — indistinguishable at a glance from a
credentials problem or a proxy-logging problem.

`capture.py` now reads which option the dialog's cursor (`❯`) is on and sends a down-arrow
(`\x1b[B`) before the accepting `\r` when needed (`_trust_arrow_presses` / `TRUST_OPTION` /
`DECLINE_OPTION` / `MENU_CURSOR`), from the live pty screen, so it tolerates the default
flipping again — if `ERROR: No API calls captured.` recurs with valid credentials and a
reachable proxy, check this first.

A capture is not byte-reproducible: the billing header fingerprints, the per-session temp
working directory, the scratchpad UUID and gitStatus's content change per run. The 2.1.235 doc
ran `sonnet-5/default` and `opus-5/default` three to four times each to show token totals
stable apart from those (9,359/9,365/9,365/9,368 and 3,871/3,866/3,860); this snapshot took one
capture per variant — **and the repeat runs that did happen did not reproduce the same tool
roster**: `sonnet-5/default` retaken ~1h45m later and `fable-5/default` ~20 minutes later both
landed at 14 upfront tools against an initial 13, traced above. Single-run captures in this
format can differ from a same-variant re-capture independent of anything `capture.py` controls.

`capture.py` strips every `CLAUDE_CODE_*` variable except `CLAUDE_CODE_OAUTH_TOKEN` from the
spawned session's environment: each is a knob that can change what the child's prompt says,
and a capture that inherits one records this machine's setup instead of the CLI's behaviour.
Two that demonstrably do: `CLAUDE_CODE_TMPDIR` moves the scratchpad path the prompt prints
(every capture reflects cc's own default temp root, `/tmp` here — `os.tmpdir()` falls back to
it once `$TMPDIR` is unset too); and `CLAUDE_CODE_FORK_SUBAGENT=0`, in this repo's
`settings.json` since c70788a (2026-09-04), swaps the subagent guidance from the `fork`
paragraph to the older Agent/Explore bullets. Scratchpad paths quoted here are as captured
under the default root.

`capture.py` spawns claude with a real pty via `pty.fork()` and `--setting-sources
project,local` to isolate from user settings, sends a canary message, then extracts the system
prompt from the intercepted API request. A placeholder CLAUDE.md is created in the temp working
directory so the capture includes the claudeMd context block. Output goes to `capture-output/`
(system.txt, request.json, summary.json) and stdout.

### Why pty (not heredoc/pipe)

Piping stdin (heredoc, `echo |`, subprocess with piped stdin) makes claude detect
non-interactive mode, which changes the identity block and skips gitStatus. `pty.fork()`
provides a real pty on both stdin and stdout so claude runs in true interactive mode. Unchanged
in 2.1.269 (`capture.py`'s spawn path is untouched by this round's fix).

### Bracketed paste

Claude Code enables xterm bracketed-paste mode (`\x1b[?2004h`). A `\r` concatenated into the
same write as the message body gets absorbed into the paste payload instead of submitting.
`spawn_claude` therefore writes the message and the submit-Enter as separate `os.write()` calls
with a short `time.sleep` between them. Unchanged in 2.1.269.

### Proxy log layout

The MITM proxy writes logs per-session under `~/.claude/requests-log/<session_id>/NNNN.json`.
Concurrent Claude Code sessions on the same machine all write under the same root. `capture.py`
filters logs by `session.pid` matching its spawned claude PID (the proxy resolves PID from
`~/.claude/sessions/<pid>.json`); mtime alone is not sufficient to isolate one capture's
traffic.

The proxy logs request bodies only, never headers, so no credential reaches disk.
