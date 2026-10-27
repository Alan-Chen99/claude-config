# Claude Code System Prompt Snapshots

Captured: 2026-10-25, every model and variant, on claude-cli/2.1.310, in one session —
`opus-5/logged-in-tool-search-loaded` half an hour after the rest, retaken past the 64-name
select cap (below). `builtin-output-styles/` is a 2.1.87 capture; both self-label.
Mode: interactive (real pty via `capture.py`, `--setting-sources project,local`), under an
isolated `CLAUDE_CONFIG_DIR` — see "How to re-capture". Default captures include a project
CLAUDE.md.

This file is the procedure: what each variant is, what credential it needs, how to re-capture
and what goes wrong. What the captured prompt and tools *say* is `what-the-model-gets.md`;
eight `notes/cc-2.1.269-*.md` records hold the 2.1.269 release analysis, one behaviour each.

`git show 18e10549~1:docs/system-prompt-snapshot/...` gives the 2.1.289 artifact for any path
here, `e9caa2ce:` the 2.1.269 one and `b318e59:` the 2.1.235 one. Every number below is
re-derived from the artifacts on disk, never adjusted; an older figure is labelled with its
release.

Directories are named for the model id the request carried, minus its `claude-` prefix. The
aliases are repointed as models ship (`latest_per_family: {..., opus: "claude-opus-5-5",
sonnet: "claude-sonnet-5-5", haiku: "claude-haiku-5-5"}`, `src/chunk-dvghjmtr.js:950-954`), so
`opus-5-5/` and `sonnet-5-5/` are what the aliases capture on 2.1.310 and `opus-5/`,
`sonnet-5/` the explicit ids. `claude-fable-5-1`, `claude-mythos-5` and `claude-mythos-5-1` are
selectable and none is captured — `notes/cc-2.1.269-fable-and-mythos-model-ids.md`.

## Files

| File | What |
|---|---|
| `<model-id>/<variant>/request.json` | Full API request body — the artifact of record. Metadata redacted. |
| `<model-id>/<variant>/prompt.md` | Everything in that request except the tool definitions: parameters, the tool roster in request order, every system block, every message |
| `<model-id>/<variant>/tools/<Name>.md` | One tool definition each — attributes, description, input schema |
| `<model-id>/<variant>/summary.json` | Block count, token counts, tool inventory, `tools_server` |
| `builtin-skills/` | What invoking each built-in skill injects, the files five extract, and `manifest.json`; shared across models — `builtin-skills/README.md` |
| `capture.py` | Captures one variant via pty + MITM proxy |
| `capture_skills.py` | Captures every built-in skill's body and files into `builtin-skills/` |
| `regenerate.py` | Drives `capture.py` across every variant, writes `summary.json` |
| `render_capture.py` | Renders `prompt.md` and `tools/` from a `request.json`; `--tree <root>` does a whole directory |
| `scripts/intercept/` — repo root | MITM proxy for API call logging |

### Reading a capture as a diff

`request.json` is one line per string with every newline escaped, so a reworded paragraph
inside `Artifact`'s 21,621-character description is one changed line that wide in `git diff`.
`prompt.md` and `tools/<Name>.md` carry the same content as text. They are derived — never
hand-edit them: `./render_capture.py --tree .` rebuilds them and
`tests/test_snapshot_rendering.py` fails when they drift from the `request.json` beside them.
Tools are one file each so a changed tool is one file of line-level hunks and an added or
removed tool an added or removed file; the rest stays in one file because a section moving
between the system prompt and the messages, as 2.1.269's environment block did, shows only
when both sit in the same diff.

The review at an upgrade is `git diff` after re-capturing. A release older than 2.1.269
predates the layout: `git show <ref>:<path>/request.json` into a scratch tree,
`./render_capture.py --tree` it, then `diff -ru -x request.json -x summary.json` against the
live directory.

### What a default capture leaves out

| Withheld from `default` | Captured in |
|---|---|
| The 19 deferred tools' descriptions and schemas — the reminder lists their names, and `tools/` holds one `DeferredToolPlaceholder` stub | `<model-id>/tool-search-loaded/tools/` |
| The Chrome and claude.ai connector tools, names included | `opus-5/logged-in-tool-search-loaded/tools/` |
| The 17 built-in skills' bodies (the reminder carries name and description only) and the files five extract | `builtin-skills/` |

The deferred half works because `ToolSearch` does not return the `<functions>` block its
description advertises, which exists nowhere else in the binary: its `tool_result` holds
`{"type": "tool_reference", "tool_name": ...}` entries in its own `content` array plus `Tool
loaded.`, and the **server** expands them into the next request's `tools` array (opus-5: 15
entries before the call, 34 after). A `select:` query is cut to its first 64 names without a
word (`MDo()`, `dw = 64`, beside `cYn = /^select:(.+)$/i`), so `regenerate.py` asks for
parallel calls of at most 64.

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
`--dangerously-skip-permissions`; how it differs from `opus-5/default` is in
`what-the-model-gets.md`. `capture.py` passes the startup acceptance dialog by writing
`skipDangerousModePermissionPrompt: true` into the temp cwd's `.claude/settings.local.json`;
accepting by hand writes that key into the real `settings.json`.

### The three `logged-in` variants

Every other variant exports `CLAUDE_CODE_OAUTH_TOKEN` and is MCP-free. These three drop it
(`capture.py --capture-no-oauth-token`) so the child authenticates from
`~/.claude/.credentials.json`, whose interactive-login token carries `user:profile` and reaches
the Chrome extension and the claude.ai connectors. An exported token gets `user:inference`
only, and `zht()` (`src/chunk-6h7ejyet.js:20275-20288`) refuses Chrome on that scope before it
reads any flag or setting, so no flag makes an exported-token child reach Chrome.

`logged-in` is the reference roster, block 2 carrying a `# Claude in Chrome browser
automation` section no MCP-free capture has. `logged-in-no-artifact` adds
`CLAUDE_CODE_DISABLE_ARTIFACT=1` through `--capture-child-env`, which is how a variant names a
`CLAUDE_CODE_*` knob it wants after the wholesale strip. With the credential fixed and both
captures in one session, the pair prices `Artifact` at 26,324 tool tokens against 14,037;
`ArtifactComments`, `ArtifactData` and the three `artifact-*` skills leave with the key.
`notes/artifact-tool-roster-cost.md` records the same comparison on 2.1.269.

`logged-in-tool-search-loaded` is the only place the Chrome and connector definitions live:
every MCP tool is deferred, so `logged-in` records their names and not one definition, and
why the variant also passes `--chrome` is in `regenerate.py`. Its 117 `tools[]` entries are
14 upfront, 102 loaded — `logged-in`'s 101 reminder names plus `advisor` — and
`DeferredToolPlaceholder`, still sent with everything loaded. Three more Claude Docs tools
never enter `tools[]`: `messages[1]` carries each as a `tool_addition` block holding a whole
`tool_definition`.

`advisor` is a **server tool**: `{"type": "advisor_20260301", "name": "advisor", "model":
"claude-opus-5-5", "defer_loading": true}` (`var PXt = "advisor_20260301"`,
`src/chunk-j0tbz6ra.js:64701`), in every logged-in roster and no MCP-free one. It has no
description and no schema, so `tools/advisor.md` renders its `type` and `model` under
`## attributes` with both empty, and `summary.json` lists it under `tools_server`, outside
`tools_total_tokens`.

**Privacy.** The tool definitions carry no account data — the only mail addresses in the 79 MCP
definitions are Google's documentation placeholders, and no ids, tokens or paths. The request
body does: the `userEmail` reminder in `messages[0]`, and `safeguards`' `user_identity` plus
absolute paths — the temp working directory, and the isolated config directory inside block
3's memory line. Committed as captured.

### Built-in skill captures

`builtin-skills/` holds what invoking each of the 17 built-in skills injects (sonnet-5,
2026-10-25) and the 141 files five of them extract; the extraction and the capture conditions
that change the result are in `builtin-skills/README.md`, the per-skill record in its
`manifest.json`. `capture_skills.py` refuses to write a body opening with harness text, and
`tests/test_builtin_skills.py` checks the committed files for the same thing: the first run
wrote cc's type-ahead suggester prompt into two files and a bare system reminder into a third.

### Subagent captures

`capture.py --subagent` adds a `subagents/NNN/` directory per child with the same four files as
a top-level capture, its `summary.json` written by `capture.py` rather than `regenerate.py`:
per-tool token counts, and `tools_server` as a name → type map. A subagent request is
identified by `cc_is_subagent=true` in the billing header, not by size or tool count — the
security-monitor call (below) also carries tools and a large system prompt.

## Credentials

The spawned child needs its own credentials: `CLAUDE_CODE_OAUTH_TOKEN` in the environment, or
an access token in `~/.claude/.credentials.json`. Claude Code strips the variable from tool
subprocess environments, so a capture launched from inside a session inherits none and falls
back to the file — empty when the session itself authenticates by env var, populated after an
interactive login. `capture.py` refuses to spawn when neither source has one.

**Export the token even when the credentials file would do.** The credentials-file login
reaches MCP and the exported token does not. Measured on 2.1.269, two `claude-opus-5`
`default` captures minutes apart and identical in every flag: exported, 15 `tools` entries, 18
deferred names, 3,338 system tokens; from the file, 18 entries, 57 deferred names, the `Claude
in Chrome browser automation` and `MCP Server Instructions` sections, 4,756 system tokens.
Every capture but the `logged-in` three is MCP-free, so one taken without the export is not
comparable to them.

`capture.py` drops three knobs without the `CLAUDE_CODE_` prefix that decide the same thing,
`ENABLE_CLAUDEAI_MCP_SERVERS` (which this repo's `settings.json` exports), `ENABLE_TOOL_SEARCH`,
and `ANTHROPIC_BASE_URL` with the two `ANTHROPIC_*` tokens; its `spawn_claude` comment gives
each one's effect.

`/workspace/.env` carries a second `CLAUDE_CODE_OAUTH_TOKEN`, commented out, for when the
active one is out of credit — that failure reads as a quota error on the first request, not an
auth error. Swap which line is commented; do not export both.

**Counting tokens is a separate credential.** Every `summary.json` figure comes from the free
`count_tokens` endpoint, which `ANTHROPIC_TOKEN_COUNT_API_KEY` reaches — and an API-key account
at a zero credit balance is rejected there too, with a 400 naming billing, after the session
has already run. `capture.py` falls back to the `~/.claude/.credentials.json` access token as a
bearer and prints which credential answered; checked on 2026-10-02 against every committed
`opus-5` `summary.json`, the OAuth credential reproduced each figure exactly.

## `--system-prompt` behavior

Replaces blocks 2-3 with the custom text plus two paragraphs: the `WebSearch` `mode` one that
tails an unoverridden block 3, and the Artifact `edits` one that tails block 2; the identity
block survives. Block 2 is 1,419 chars in all three override captures: 27 of custom text
(`regenerate.py`'s `CUSTOM_PROMPT`), the 423-char `WebSearch` paragraph and the 965-char
Artifact one, blank-line separated. `gitStatus` sits in `messages[0]` (since 2.1.269), so it
survives an override the way `userEmail` does. `--append-system-prompt` inserts the custom
text at the end of block 3, after the `WebSearch` paragraph.

`system_tokens` for `--system-prompt` / `--system-prompt-file`: 570 / 567 on sonnet-5, – / 570
on opus-5, against 116 / 114 and – / 117 on 2.1.269; the `WebSearch` paragraph (2.1.289) and the
Artifact one (2.1.310) are the difference.

What survives the removal of blocks 2-3: billing header, identity, both paragraphs above, the
CLAUDE.md wrapper reminder with its "these instructions OVERRIDE any default behavior" line,
`userEmail`+`gitStatus`+Attribution (all in `messages[0]`), every upfront tool definition, the
deferred-tool placeholder, and one system-role block (or a prepend to `messages[0]`) holding
`# Environment`, the model-identity line, the deferred-tool listing, the agent-type roster, the
permission-mode reminder and every skill description. Read that last item as behaviour, not
facts — the skill and agent text is Anthropic-authored guidance about when to delegate, and an
override displaces none of it (`sonnet-5/system-prompt/prompt.md`,
`opus-5/system-prompt-file/prompt.md`, under `## messages[1] system, content[0]`).

### Sub-agent behavior

Neither `--system-prompt` nor `--append-system-prompt` propagates to sub-agents (not
re-tested: no capture combines `--subagent` with a prompt override). Subagents get the identity
line `"You are a Claude agent, built on Anthropic's Claude Agent SDK."`.

| Agent | Prompt identity | Model | Upfront tools |
|-------|----------------|-------|---------------|
| Explore | "file search specialist" | claude-sonnet-5 | Bash, Read, Skill, ToolSearch, SubagentHandback, DeferredToolPlaceholder |
| general-purpose | "an agent for Claude Code" | claude-sonnet-5 | Agent, Artifact, Bash, Edit, Read, Skill, ToolSearch, Write, SubagentHandback, DeferredToolPlaceholder |

`SubagentHandback` (643 tokens) is the one upfront tool a subagent has and the main session
does not; `SendFeedback` is the reverse. A matching `messages[0]` block tells the child that
only a `SubagentHandback` call reaches its caller, and *"Do not also send the report with
SendMessage: your caller would get it twice"*. Per-tool token figures exist only in these two
captures' `summary.json`.

## Not re-verified since 2.1.235

- **Security-monitor calls.** The side-channel harm-classifier calls need tool calls under a
  mode other than `--dangerously-skip-permissions`, which suppresses them; no capture here has
  one, so their description (model, prompt, `<severity>`/`<block>` forms) is historical.
- **Interactive vs `-p` mode differences.** Whether `-p` still differs — gitStatus,
  `safeguards`, the permission-mode reminder — needs one `claude -p` capture.

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
`sessions/` is a symlink because the intercept proxy writes every session's logs under
`~/.claude/requests-log/<session_id>/` whatever the child's `CLAUDE_CONFIG_DIR`, and
`capture.py` picks out its child's by the pid the proxy resolves through
`~/.claude/sessions/<pid>.json`; mtime alone would mix in concurrent sessions. The proxy logs
request bodies only, never headers, so no credential reaches disk.
`CLAUDE_SECURESTORAGE_CONFIG_DIR` keeps the `logged-in` variants' token refresh in the shared
`.credentials.json`. A capture's own session logs therefore live under `$CFG/projects/`, not
`~/.claude/projects/`.

`ANTHROPIC_TOKEN_COUNT_API_KEY` comes from the checkout's own `.env`, which
`claude_config.config.load()` resolves relative to the package. `CLAUDE_CODE_OAUTH_TOKEN` must
be exported for every variant but the `logged-in` three — see "Credentials".

`./capture.py` takes one variant at a time (`--system-prompt`, `--system-prompt-file`,
`--append-system-prompt`, `--subagent`, or no flag for the default prompt);
`./regenerate.py --model <id>` runs every variant for a model, `--model <id> <name>` one of
them. Never two `regenerate.py` at once — they share `capture-output/` and
`~/.claude/requests-log/` and overwrite each other's intermediates.

### Trust-dialog default flipped

Since 2.1.269 the first-run trust dialog opens on **"No, exit"**, which quits the child before
its first API call with only `ERROR: No API calls captured.` to show for it. `capture.py` reads
the cursor (`❯`) off the pty screen and sends a down-arrow before the `\r` when needed
(`_trust_arrow_presses`); check this first when that error recurs with valid credentials and a
reachable proxy.

A capture is not byte-reproducible: the billing header fingerprints, the temp working
directory, the scratchpad UUID and gitStatus's content change per run. Token totals are stable
apart from those — 2.1.235 ran `sonnet-5/default` four times for 9,359–9,368. The *roster* is
not: `sonnet-5/default` came back with 13 upfront tools and no `EndConversation` deferred name
on the first run of both the 2.1.269 and the 2.1.289 batch, and a same-version re-capture fixed
it both times — remote GrowthBook flag `tengu_juniper_relay`, default off, occasionally
resolving that way with a correct value cached on disk
(`notes/cc-2.1.269-upfront-roster-flag-flicker.md`). `fable-5/default` flickered on 2.1.269.

`capture.py` strips every `CLAUDE_CODE_*` variable but `CLAUDE_CODE_OAUTH_TOKEN` from the child:
each can change what its prompt says (`CLAUDE_CODE_TMPDIR` moves the scratchpad path it prints,
which shows cc's default temp root, `/tmp` here, only while `$TMPDIR` is unset too;
`CLAUDE_CODE_FORK_SUBAGENT=0` swaps the `fork` paragraph for the older Agent/Explore bullets),
and a capture that inherits one records this machine instead of the CLI.

A placeholder CLAUDE.md in the temp working directory gets the claudeMd block into the capture.
Intermediates go to `capture-output/`.

### Why pty (not heredoc/pipe)

Piping stdin (heredoc, `echo |`, subprocess with piped stdin) makes claude detect
non-interactive mode, which changes the identity block and skips gitStatus. `pty.fork()` gives
a real pty on both stdin and stdout, so claude runs interactive. Claude Code enables
bracketed-paste mode, so `spawn_claude` writes the message and the submit `\r` as separate
writes: one concatenated `\r` is absorbed into the paste.
