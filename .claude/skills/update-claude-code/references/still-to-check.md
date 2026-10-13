# Still to check — as of 2026-10-05, Claude Code 2.1.289

Open items with what retires each. Delete an entry once closed; add one for every gap you find
rather than leaving it in a session transcript.

## Every upgrade

- **The vendored skills' loaders.** `skilldiff.sh` compares asset bodies, so a loader that gains
  a placeholder, prefix or substitution changes what the built-in says while the copies stay
  byte-identical. 2.1.289's `artifact-design` loader: asset → `trimStart()` → the
  `<!-- dataviz-callout -->` splice (`tengu_cobalt_plinth_dataviz`) → under
  `CLAUDE_CODE_ARTIFACT_TOOLSET` a "Page contract" prefix (a `tengu_cobalt_plinth_campion`
  Thumbnail line) and one phrase swap. `artifact-diagramming`'s is `trimStart()` only. Never
  retires.
- **The resume-from-summary override, a decision held on a Claude Code defect.**
  `skills/resume-from-summary` overrides the summary's closing order
  (`as if the break never happened`), which no setting or settings hook reaches. A mod reaches
  most compactions — measured 2026-10-12 (session `c8997157`): a `session.append` hook on door
  `compaction` rewrites it in every autocompact, interactive and `-p`, and in a `-p` `/compact`.
  An interactive `/compact` dispatches no `session.append`, against the bundled reference
  (`a compaction's boundary and summary`); only a `session.compact` hook reaches it, by
  rebuilding the summary without its `handle`, which drops `isCompactSummary`. That gap and the
  plugin API's `EARLY ACCESS` are why the user keeps the override. Re-check: run
  `claude --setting-sources project,local --plugin-dir <mod>` interactively in a pty, the mod
  logging `session.append` by door, under `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1` (a nested
  session saves no transcript without it); send a prompt, then `/compact`. Once that `/compact`
  reaches `session.append` and the API leaves early access, put the decision back to the user.

## Open decision

- **Defer `Artifact` instead of removing it.** A plugin's `tool.describe` hook (`isDeferred`)
  can move a built-in behind ToolSearch, keeping `Artifact` one deferred line away and the
  built-in `artifact-*` skills; against it, the plugin API is early access, and it trades a
  settings key for a plugin. Decide, or record the decision not to.

## Measurements the source cannot settle

- The 18,611-character `additionalContext` that arrived whole on 2.1.269, against the 10,000
  persistence ceiling both builds carry (`inventory.md`, `REPORT_BUDGET`). Retire with a
  `PostToolUse` command hook emitting 10,500 characters of `additionalContext` and a read of
  what the next turn sees: a `<persisted-output>` stub, or the text.
- `worker_permission_prompt` has never fired through this config (wired 2026-10-05). Retire by
  watching one worker permission push.
- `claude agents` sessions are inferred, not measured, to get `SessionStart` rather than
  `SubagentStart`; read one transcript.

## Pins never re-derived for this build

- `notes/env-context-manifest.md` (named by `docs/env-context-manifest.json`): its byte offsets,
  anchor count and `Shell: PowerShell` probe describe 2.1.235.
- `docs/system-prompt-snapshot/README.md`: the two **Not re-verified since 2.1.235** blocks, under
  "Security-monitor calls" and "Interactive vs `-p` mode differences".
- `docs/system-prompt-snapshot/builtin-output-styles/`: captured from v2.1.87, and has no file
  for 2.1.257's `Proactive`. Retire by re-capturing every built-in style.

## Unread in the 2.1.289 captures

- The permission-mode reminder's per-model bodies: its emitter is unread
  (grep `mode is active:`).
- `"model": "opus"` now resolves to `claude-opus-5-5`, whose block 3 lacks opus-5's
  `# Delivering work`, `# Corrections` and reduced-delegation line and whose `Bash` description
  drops the cat/head/sed bullet — a new bundle, or `opus_5_prompt_bundle` missing the id,
  unknown. `sys_prompt/` drops block 3; the `Bash` text reaches every session.
- `advisor`, a server tool on every logged-in roster (`advisor_20260301`), does something
  unread; a `claude.sh` roster did not carry it (2026-10-06).
- No backgrounded-session capture since 2.1.235; `/feedback` from a logged-in session never
  checked.

## Opened by the release notes (2.1.247–2.1.268 read 2026-09-12, 2.1.270–2.1.289 on 2026-10-05)

- `docs/agent-tools-status-reference.md`, "The kill boundary": 2.1.257 fixed `setsid`-detached
  commands surviving a task stop or a Claude Code exit — what `agent-tools run --background` is
  built on. The task-stop half is measured there; the exit half needs a human:
  `agent-tools run --background sleep 900`, quit Claude Code, check whether the child survives.
- `docs/tool-token-limits.md`: the changelog's 20 MB Grep/Glob output cap has no matching
  constant in the search path.
- `src/claude_config/cc_pretty/` record handling: subagent progress ticks replaced (2.1.251),
  async hook notices batched onto one line (2.1.257), nested background subagent results in the
  parent subagent's transcript (2.1.259), the report arriving through a `SubagentHandback` call
  (2.1.271), every foreground Agent result under the `[Subagent hand-back]` header (2.1.277), so
  a small `--tool-max` preview is mostly preamble. Retire by re-reading real 2.1.289 logs
  (step 10).

## Open design questions

- `cc-render-coverage` cannot see selection defects (`checks.md`).
- Whether `agents/session-analysis.md` moves from `claude-opus-4-8` to `claude-opus-5-5`: the pin
  resolves, so it is a cost and behaviour choice.
- Whether the env-context window check is redesigned around the field templates it no longer
  sees (`checks.md`).

## Pre-existing, not upgrade-caused

`agents/*.md` and ~30 sites under `skills/scripts/` name `Grep`, `Glob`, `TodoWrite` and
`Task`, none on the live roster. `TodoWrite` is a settings decision
(`CLAUDE_CODE_ENABLE_TODO_TOOLS`, `inventory.md`); `Task` is an accepted alias for `Agent`; the
rest are text edits.
