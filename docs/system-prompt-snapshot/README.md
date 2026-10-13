# Claude Code System Prompt Snapshots

Captured: 2026-10-06, every model and variant, on claude-cli/2.1.289 — the three
`opus-5/logged-in*` variants and `opus-5/bypass-permissions` in a second session half an hour
after the rest. `builtin-output-styles/` is a 2.1.87 capture;
both self-label.
Mode: interactive (real pty via `capture.py`, `--setting-sources project,local`), under an
isolated `CLAUDE_CONFIG_DIR` — see "How to re-capture".
Default captures include a project CLAUDE.md.

This file is the procedure: what each variant is, what credential it needs, how to re-capture
and what goes wrong. What the captured prompt and tools *say* is `what-the-model-gets.md`;
eight `notes/cc-2.1.269-*.md` records hold the 2.1.269 release analysis, one behaviour each.

`git show e9caa2ce:docs/system-prompt-snapshot/...` gives the 2.1.269 artifact for any path
here and `git show b318e59:...` the 2.1.235 one. Every number below was re-derived from the
artifacts on disk; an older figure kept for comparison is labelled with its release.

Directories are named for the model id the request carried, minus its `claude-` prefix.
Aliases are repointed as models ship — `opus` meant `claude-opus-4-6` in the 2.1.143 capture
and `claude-opus-5` in the 2.1.269 one, and resolves to `claude-opus-5-5` here while `sonnet`
resolves to `claude-sonnet-5-5` (`latest_per_family: {..., opus: "claude-opus-5-5", sonnet:
"claude-sonnet-5-5", ...}`, `src/chunk-jepmcrwm.js:845-849`) — so an alias-named directory
changes meaning between captures while its path stays put. `opus-5-5/` and `sonnet-5-5/` are
what the aliases capture; `opus-5/` and `sonnet-5/` are the explicit ids. `claude-fable-5-1`,
`claude-mythos-5` and `claude-mythos-5-1` are selectable too and none is captured —
`notes/cc-2.1.269-fable-and-mythos-model-ids.md`.

## Files

| File | What |
|---|---|
| `<model-id>/<variant>/request.json` | Full API request body — the artifact of record. Metadata redacted. |
| `<model-id>/<variant>/prompt.md` | Everything in that request except the tool definitions: parameters, the tool roster in request order, every system block, every message |
| `<model-id>/<variant>/tools/<Name>.md` | One tool definition each — attributes, description, input schema |
| `<model-id>/<variant>/summary.json` | Block count, token counts, tool inventory, `tools_server` |
| `builtin-skills/<name>.md` | What invoking that built-in skill injects. Shared across models: bodies byte-identical on opus-5 and sonnet-5 |
| `builtin-skills/<name>/` | The files that skill extracts for the model to read |
| `builtin-skills/manifest.json` | Per skill: delivery shape, which route reached it, size, sha256; the same per file |
| `capture.py` | Captures one variant via pty + MITM proxy |
| `capture_skills.py` | Captures every built-in skill's body and files into `builtin-skills/` |
| `regenerate.py` | Drives `capture.py` across every variant, writes `summary.json` |
| `render_capture.py` | Renders `prompt.md` and `tools/` from a `request.json`; `--tree <root>` does a whole directory |
| `scripts/intercept/` — repo root | MITM proxy for API call logging |

### Reading a capture as a diff

`request.json` is the artifact of record and is unreadable as a diff: one line per string with
every newline escaped, so a reworded paragraph inside `Artifact`'s 19,888-character description
arrives in `git diff` as a single changed line 19,888 characters wide. `prompt.md` and
`tools/<Name>.md` carry the same content as text for the person reading that diff across a
release. They are derived — never hand-edit them: `./render_capture.py --tree .` rebuilds them
and `tests/test_snapshot_rendering.py` fails when they drift from the `request.json` beside them.

The split is per tool because that makes the diff legible — a changed tool is one file with
line-level hunks, an unchanged one absent, an added or removed tool an added or removed file.
Everything else stays in one file because it is read as a whole: a section moving between the
system prompt and the messages, which 2.1.269 did to the environment block, is only visible if
both sit in the same diff.

The review at an upgrade is `git diff` after re-capturing. A release older than 2.1.269
predates the layout: `git show <ref>:<path>/request.json` into a scratch tree,
`./render_capture.py --tree` it, then `diff -ru -x request.json -x summary.json` against the
live directory.

### What a default capture leaves out, and where it now lives

| Withheld from `default` | Captured in |
|---|---|
| The 19 deferred tools' descriptions and schemas — the reminder lists their names, and `tools/` holds one `DeferredToolPlaceholder` stub | `<model-id>/tool-search-loaded/tools/` |
| The Chrome and claude.ai connector tools entirely — `default` does not even list their names | `opus-5/logged-in-tool-search-loaded/tools/` |
| The 17 built-in skills' bodies — the reminder carries each name and description, never the text an invocation injects — and the files five extract | `builtin-skills/` |

The deferred half works because `ToolSearch` does not do what its own description says: it
advertises a `<functions>` block, and no such block exists anywhere in the binary except that
sentence. It returns a `tool_result` of `{"type": "tool_reference", "tool_name": ...}` entries
plus `Tool loaded.`, and the **server** expands those into the next request's `tools` array —
measured on opus-5, 15 entries before the call and 34 after. Those `tool_reference` blocks sit
inside the `tool_result` block's own `content` array, not directly in `messages[].content`.

`tool-search-loaded` is captured for opus-5 and sonnet-5, enough to separate per-model text
from shared — which of the 19 split by prompt branch is in `what-the-model-gets.md`.

`regenerate.py`'s `VARIANTS` dict defines the eleven variants; coverage is uneven by design.
sonnet-5 has the seven prompt-shape variants (`default`, `append`, `custom-output-style`,
`system-prompt`, `system-prompt-file`, `subagent`, `tool-search-loaded`); opus-5 adds
`bypass-permissions` and the `logged-in` three, which no other model needs; opus-4-7, opus-4-8,
fable-5, opus-5-5 and sonnet-5-5 have `default` only. opus-4-8 exists to test whether fable's
prompt was a Fable-family oddity or per-model (per-model;
`notes/cc-2.1.269-prompt-split-per-model-id.md`).

`opus-5/bypass-permissions` is the mode `scripts/claude.sh` launches,
`--dangerously-skip-permissions`. It matches `opus-5/default` but for two things: no
`safeguards` key at all (12 top-level keys against 13), so that block is emitted only where a
permission classifier is in play; and a `messages[1]` reminder opening `While bypass
permissions mode is active:` instead of `While auto mode is active:` over a byte-identical
body. `capture.py` passes the startup acceptance dialog by writing
`skipDangerousModePermissionPrompt: true` into the temp cwd's `.claude/settings.local.json`
(gate `mz()`, `src/chunk-3z4drmxy.js:3958`, read by the dialog at `src/chunk-q08t3k8v.js:129`);
accepting by hand writes that key into the real `settings.json`, and `.claude.json`'s older
`bypassPermissionsModeAccepted` is migrated into it by
`tengu_migrate_bypass_permissions_accepted` (`src/chunk-ya33qr7x.js:851-866`).

### The three `logged-in` variants

Every other variant exports `CLAUDE_CODE_OAUTH_TOKEN` and is MCP-free. These three drop it
(`capture.py --capture-no-oauth-token`) so the child authenticates from
`~/.claude/.credentials.json`, the condition under which it reaches the Chrome extension and
the claude.ai connectors.

The mechanism is an OAuth scope check, not a preference. `WFt()`
(`src/chunk-gppff98a.js:16875-16887`) returns false before it looks at any flag or setting when
`/api/oauth/validate` rejects the token's scopes, and its log line names them: *"needs
user:profile, user:office, or user:ccr_inference; env-var and setup-token sessions default to
user:inference only"*. An exported `CLAUDE_CODE_OAUTH_TOKEN` child cannot reach Chrome however
it is flagged; the interactive login's token carries `user:profile` and does.

`logged-in` is the reference roster: 5,090 system tokens over blocks 190/57/1,603/13,440 chars,
block 3 carrying a `# Claude in Chrome browser automation` section no MCP-free capture has.
`logged-in-no-artifact` adds `CLAUDE_CODE_DISABLE_ARTIFACT=1` through `--capture-child-env`,
which is how a variant names a `CLAUDE_CODE_*` knob it wants after the wholesale strip. The
pair prices the `Artifact` tool with the credential fixed and both captures in one session:
24,597 tool tokens against 13,273, 14 upfront tools against 13, the three `artifact-*` skills
listed against absent, 92 deferred names against 90 — `ArtifactComments` and `ArtifactData`
leave with the key. `notes/artifact-tool-roster-cost.md` records the same comparison on
2.1.269, when `Artifact` was 25,099 characters rather than 19,888.

`logged-in-tool-search-loaded` is the only place the Chrome and connector definitions live.
Both sets are MCP, and the deferral predicate (`h()`, `src/chunk-sspbjbr8.js:52-57`) defers
every MCP tool unconditionally — `if (e.isMcp === !0) return !0;` (`:53`) — so `logged-in`
records their names and not one definition. The variant adds `--chrome` and the
`tool-search-loaded` machinery to the `logged-in` credential: `WFt()` reads the flag ahead of
both `CLAUDE_CODE_ENABLE_CFC` and the `claudeInChromeDefaultEnabled` setting, and that setting
lives in `~/.claude.json`, which `--setting-sources project,local` does not filter — so without
the flag the Chrome roster would be a property of the operator's machine. Its 111 `tools[]`
entries are 14 upfront + 96 deferred-loaded + `DeferredToolPlaceholder`, still sent with
everything loaded. The 96: 22 `mcp__claude-in-chrome__*`, 51 connector tools (30 Gmail, 8
Google Drive, 8 Claude Docs, 4 Indeed, 1 ZipRecruiter), the 22 built-in deferred names, and
`advisor` — exactly `logged-in`'s 92 reminder names plus the four definitions it already
carries (three Claude Docs tools and `advisor`), so the two are same-session comparable.
`check_deferred_loaded` compares a load against its own `requires_variant` sibling for this
reason: verified against `default`, which knows only its 19 names, a capture whose 22 Chrome
schemas never arrived would pass.

`advisor` is a **server tool**: `{"type": "advisor_20260301", "name": "advisor", "model":
"claude-opus-5-5", "defer_loading": true}` (`var lTt = "advisor_20260301"`,
`src/chunk-wgfrtm7w.js:44092`), in every logged-in roster and no MCP-free one. It has no
description and no schema, so `tools/advisor.md` renders its `type` and `model` under
`## attributes` with both empty. `regenerate.py` lists such entries under `tools_server` and
excludes them from `tools_total_tokens`: `count_tokens` rejects a request on one.

**Privacy.** The tool definitions carry no account data — the only mail addresses in the 73 MCP
definitions are Google's documentation placeholders (`gduser1@workspacesamples.dev`,
`user@example.com`), and no ids, tokens or paths. The request body does: the `userEmail`
reminder in `messages[0]` always has, and 2.1.289's `safeguards` adds `user_identity` plus
absolute paths — the temp working directory, and the isolated config directory inside block 3's
memory line. Committed as captured.

### Built-in skill captures

`builtin-skills/` holds what invoking each of the 17 built-in skills injects on 2.1.289
(sonnet-5, 2026-10-12), 533,724 characters in all, and the 114 files five of them extract;
the per-skill table, the extraction and the three capture conditions that change the result
are in `builtin-skills/README.md`. The 2.1.289 listing drops `design` and adds
`plugin-authoring`; `capture_skills.py` prunes a dropped skill's entry, body and files on a
full-roster run. A wrong condition produces a plausible short body rather than an error, so
`capture_skills.py` refuses to write a body opening with harness text and
`tests/test_builtin_skills.py` checks the committed files for the same thing: the first run
wrote cc's type-ahead suggester prompt into two files and a bare system reminder into a third.

### Subagent captures

`capture.py --subagent` adds a `subagents/NNN/` directory per child, with the same four files
as a top-level capture — except that a child's `summary.json` is written by `capture.py` rather
than `regenerate.py`: per-tool token counts, and `tools_server` as a name → type map.
The rosters are smaller than the parent's: 6 tool files for Explore, 10 for general-purpose,
against 15.

Subagent requests are identified by `cc_is_subagent=true` in the billing header, not by size or
tool count — the security-monitor call (below) also carries tools and a large system prompt.
`sonnet-5/subagent`'s two children carry it and their own `cc_prompt_id`.

## Credentials

The spawned child needs its own credentials: `CLAUDE_CODE_OAUTH_TOKEN` in the environment, or
an access token in `~/.claude/.credentials.json`. Claude Code strips the variable from tool
subprocess environments, so a capture launched from inside a session inherits none and falls
back to the file — empty when the session itself authenticates by env var, populated after an
interactive login.

**Export the token even when the credentials file would do.** The credentials-file login
reaches MCP and the exported token does not. Measured on 2.1.269, two `claude-opus-5`
`default` captures minutes apart and identical in every flag: with the exported token, 15
`tools` entries, 18 deferred names, 3,338 system tokens; with the credentials-file login, 18
entries, 57 deferred names, the `Claude in Chrome browser automation` and `MCP Server
Instructions` sections, 4,756 system tokens — same 14 upfront names in both. Every capture here
but the `logged-in` three is MCP-free, so a re-capture without the export is not comparable to
one.

Three knobs that are not `CLAUDE_CODE_*` decide the same thing, so `capture.py` drops them from
the child along with the prefix: `ENABLE_CLAUDEAI_MCP_SERVERS`, which this repo's
`settings.json` has exported into every tool subprocess since `56168fdf` and which would have
silently cost a re-capture its connector tools; `ENABLE_TOOL_SEARCH`, which off ends deferral
so every definition arrives upfront; and `ANTHROPIC_BASE_URL` with the two `ANTHROPIC_*`
tokens, which `kimi.sh` and `zai.sh` export and which would send the child to another provider
or make it an API-key session with no OAuth scope at all.

`/workspace/.env` carries a second `CLAUDE_CODE_OAUTH_TOKEN`, commented out, for when the
active one is out of credit — that failure reads as a quota error on the first request, not an
auth error. Swap which line is commented; do not export both.

**Counting tokens is a separate credential.** Every `summary.json` figure comes from the free
`count_tokens` endpoint, which `ANTHROPIC_TOKEN_COUNT_API_KEY` reaches — and an API-key account
at a zero credit balance is rejected there too, with a 400 naming billing, after the session
has already run. `capture.py` falls back to the `~/.claude/.credentials.json` access token as a
bearer and prints which credential answered; checked on 2026-10-02 against every committed
`opus-5` `summary.json`, the OAuth credential reproduced each figure exactly.

`tools_total_tokens` prices only the entries without `defer_loading` — the endpoint honours the
flag, which is why `logged-in-tool-search-loaded`, `logged-in` and `default` all report 24,597
across 111, 19 and 15 `tools[]` entries. What the server charges for `advisor` is not visible
from here.

`capture.py` refuses to spawn when neither source has credentials. Without the guard the child
renders "Not logged in", issues zero API calls, and the failure surfaces only as an empty
capture.

## `--system-prompt` behavior

Replaces blocks 2-3 with the custom text plus the `WebSearch` `mode` paragraph that tails an
unoverridden block 3; the identity block survives. Block 2 is 452 chars in all three override
captures: 27 of custom text (`"You are a custom assistant."`, `regenerate.py`'s
`CUSTOM_PROMPT`), a blank line, and that 423-char paragraph. `gitStatus` is not appended — it
moved into `messages[0]` unconditionally in 2.1.269, so it survives an override the way
`userEmail` always has.

`system_tokens` for the replacement-prompt variants (exact, from `summary.json`):

| Flag | Sonnet 5 (2.1.235 / 2.1.269 / 2.1.289) | Opus 5 (2.1.269 / 2.1.289) |
|---|---|---|
| `--system-prompt` | 228 / 116 / 279 | not captured |
| `--system-prompt-file` | 226 / 114 / 279 | 117 / 276 |

The 2.1.269 drop was `gitStatus` leaving, the rise the `WebSearch` paragraph arriving.
`--append-system-prompt` still inserts the custom text at the end of block 3, after that
paragraph.

What survives the removal of blocks 2-3: billing header, identity, the `WebSearch` paragraph,
the CLAUDE.md wrapper reminder with its "these instructions OVERRIDE any default behavior"
line, `userEmail`+`gitStatus`+Attribution
(all in `messages[0]`), every upfront tool definition, the deferred-tool placeholder, and one
system-role block (or a prepend to `messages[0]`) holding `# Environment`, the model-identity
line, the deferred-tool listing, the agent-type roster, the permission-mode reminder and every
skill description. Read that last item as behaviour, not facts — the skill and agent text is
Anthropic-authored guidance about when to delegate, and an override displaces none of it
(`sonnet-5/system-prompt/prompt.md`, `opus-5/system-prompt-file/prompt.md`, under
`## messages[1] system, content[0]`).

### Background sessions do not inherit the flag

The forked-argv list is built from scratch at `src/chunk-8w9chsdq.js:767-769` and carries
`--resume`, `--model`, `--permission-mode`, `--append-system-prompt`,
`--system-prompt-snapshot` and nine others — but neither `--system-prompt` nor
`--system-prompt-file`, and no other path carries them across, so a custom prompt is replaced
by the default one the moment a session backgrounds. `docs/background-sessions.md` is the
maintained source for the handoff, kept current against 2.1.289; no backgrounding capture lives
here.

### Sub-agent behavior

Neither `--system-prompt` nor `--append-system-prompt` propagates to sub-agents (unchanged; not
re-tested, since no capture combines `--subagent` with a prompt override). The identity line
subagents receive — `"You are a Claude agent, built on Anthropic's Claude Agent SDK."` — is
byte-identical to 2.1.235.

| Agent | Prompt identity | Model | Upfront tools |
|-------|----------------|-------|---------------|
| Explore | "file search specialist" | claude-sonnet-5 | Bash, Read, Skill, ToolSearch, SubagentHandback, DeferredToolPlaceholder |
| general-purpose | "an agent for Claude Code" | claude-sonnet-5 | Agent, Artifact, Bash, Edit, Read, Skill, ToolSearch, Write, SubagentHandback, DeferredToolPlaceholder |

`SubagentHandback` (643 tokens) is the one upfront tool a subagent has and the main session
does not; `SendFeedback` is the reverse. A matching `messages[0]` block tells the child that
only a `SubagentHandback` call reaches its caller. Explore's deferred list stays at 7,
general-purpose's went 8 -> 10 with the two `Artifact*` names. Per-tool token figures exist
only in these two captures: `Artifact` 11,678, `Bash` 4,504, `Agent` 3,236, `Read` 1,260,
`Skill` 977, `Edit` 933, `ToolSearch` 889, `Write` 714, `DeferredToolPlaceholder` 432.

## Security-monitor calls

**Not re-verified since 2.1.235.** Measuring the side-channel harm-classifier calls needs a
live session making tool calls under a permission mode other than
`--dangerously-skip-permissions`, which the 2.1.235 measurement notes suppresses them
entirely — no capture here provides that. Its description (model, prompt structure,
`<severity>`/`<block>` response forms) is historical.

## Interactive vs `-p` mode differences

**Not re-verified since 2.1.235.** gitStatus and the Environment block both moved to a
messages-level reminder in interactive mode, so the old finding that "gitStatus is appended in
`-p` mode too, block 2 is byte-identical" needs one `claude -p` capture to settle, as do
`safeguards` and the permission-mode reminder, both permission-mode-derived.

## How to re-capture

Every capture runs under its own config directory. A stock launch against the shared
`~/.claude` rewrites `~/.claude.json`, refetches caches other sessions read, and can write
`settings.json` through its symlink into the canonical checkout.

```bash
CFG=<fresh dir>; cp ~/.claude.json "$CFG/.claude.json"; ln -sfn ~/.claude/sessions "$CFG/sessions"
set -a; . /workspace/.env; set +a     # CLAUDE_CODE_OAUTH_TOKEN
UNSET=$(env | grep -o '^CLAUDE_CODE_[A-Z_0-9]*' | sed 's/^/-u /' | tr '\n' ' ')
env $UNSET CLAUDE_CODE_OAUTH_TOKEN="$CLAUDE_CODE_OAUTH_TOKEN" CLAUDE_CONFIG_DIR="$CFG" \
    CLAUDE_SECURESTORAGE_CONFIG_DIR=$HOME/.claude PATH=<dir of the claude under test>:$PATH \
    uv run python docs/system-prompt-snapshot/regenerate.py --model <id> <variants...>
```

`.claude.json` is a copy, not a symlink: it carries `migrationVersion`, the onboarding and
auto-mode flags and `oauthAccount`, and a symlink would defeat the `.claude.json.lock`.
`sessions/` is a symlink because the intercept proxy maps the session header to a pid through
that directory and `capture.py` filters its logs by pid.
`CLAUDE_SECURESTORAGE_CONFIG_DIR` keeps the `logged-in` variants' token refresh in the shared
`.credentials.json`. A capture's own session logs therefore live under `$CFG/projects/`, not
`~/.claude/projects/`.

`ANTHROPIC_TOKEN_COUNT_API_KEY` comes from the checkout's own `.env`, which
`claude_config.config.load()` resolves relative to the package. `CLAUDE_CODE_OAUTH_TOKEN` must
be exported for every variant but the `logged-in` three, even when the credentials file holds a
token — see "Credentials".

`./capture.py` takes one variant at a time (`--system-prompt`, `--system-prompt-file`,
`--append-system-prompt`, `--subagent`, or no flag for the default prompt);
`./regenerate.py --model <id>` runs every variant for a model, `--model <id> <name>` one of
them. Never two `regenerate.py` at once — they share `capture-output/` and
`~/.claude/requests-log/` and overwrite each other's intermediates.

### Trust-dialog default flipped

2.1.269's first-run trust dialog starts with the cursor on **"No, exit"** rather than the trust
option (2.1.235 defaulted to trust, so the bare `\r` `capture.py` sent accepted it). Confirming
"No, exit" quits the child before its first API call, and the only symptom is `ERROR: No API
calls captured.` — indistinguishable at a glance from a credentials or proxy-logging problem.
`capture.py` reads which option the cursor (`❯`) is on from the live pty screen and sends a
down-arrow (`\x1b[B`) before the accepting `\r` when needed (`_trust_arrow_presses` /
`TRUST_OPTION` / `DECLINE_OPTION` / `MENU_CURSOR`), so it tolerates the default flipping again.
If that error recurs with valid credentials and a reachable proxy, check this first.

A capture is not byte-reproducible: the billing header fingerprints, the temp working
directory, the scratchpad UUID and gitStatus's content change per run. Token totals are stable
apart from those — 2.1.235 ran `sonnet-5/default` and `opus-5/default` three to four times each
(9,359/9,365/9,365/9,368 and 3,871/3,866/3,860). The *roster* is not: `sonnet-5/default` came
back with 13 upfront tools and no `EndConversation` deferred name on the first run of both the
2.1.269 and the 2.1.289 batch, and a same-version re-capture fixed it both times — remote
GrowthBook flag `tengu_juniper_relay`, default off, occasionally resolving that way with a
correct value cached on disk (`notes/cc-2.1.269-upfront-roster-flag-flicker.md`).
`fable-5/default` flickered on 2.1.269 and not on 2.1.289.

`capture.py` strips every `CLAUDE_CODE_*` variable but `CLAUDE_CODE_OAUTH_TOKEN` from the
child: each is a knob that can change what its prompt says, and a capture that inherits one
records this machine instead of the CLI. Two that demonstrably do: `CLAUDE_CODE_TMPDIR` moves
the scratchpad path the prompt prints (captures reflect cc's own default temp root, `/tmp`
here — `os.tmpdir()` falls back to it once `$TMPDIR` is unset too), and
`CLAUDE_CODE_FORK_SUBAGENT=0`, in this repo's `settings.json` since c70788a (2026-09-04),
swaps the subagent guidance from the `fork` paragraph to the older Agent/Explore bullets.

A placeholder CLAUDE.md in the temp working directory gets the claudeMd block into the capture.
Intermediates go to `capture-output/`.

### Why pty (not heredoc/pipe)

Piping stdin (heredoc, `echo |`, subprocess with piped stdin) makes claude detect
non-interactive mode, which changes the identity block and skips gitStatus. `pty.fork()` gives
a real pty on both stdin and stdout, so claude runs interactive.

### Bracketed paste

Claude Code enables xterm bracketed-paste mode (`\x1b[?2004h`), so a `\r` concatenated into the
same write as the message body is absorbed into the paste payload instead of submitting.
`spawn_claude` writes the message and the submit-Enter as separate `os.write()` calls, with a
short `time.sleep` between.

### Proxy log layout

The MITM proxy writes logs per-session under `~/.claude/requests-log/<session_id>/NNNN.json`
whatever the child's `CLAUDE_CONFIG_DIR`, and concurrent sessions on the same machine all write
under that root. `capture.py` filters by `session.pid` matching its spawned claude PID (the
proxy resolves PID from `~/.claude/sessions/<pid>.json`); mtime alone does not isolate one
capture's traffic. The proxy logs request bodies only, never headers, so no credential reaches
disk.
