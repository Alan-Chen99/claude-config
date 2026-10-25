# Still to check — as of 2026-10-25, Claude Code 2.1.310

Open items with what retires each. Delete an entry once closed; add one for every gap you find
rather than leaving it in a session transcript.

## Every upgrade

- **The vendored skills' loaders.** `skilldiff.sh` compares asset bodies, so a loader that gains
  a placeholder, prefix or substitution changes what the built-in says while the copies stay
  byte-identical. 2.1.310's `artifact-design` loader: asset → `trimStart()` → the
  `<!-- dataviz-callout -->` splice → under the split toolset a `## Page contract` prefix and one
  phrase swap. `artifact-diagramming`'s (2.1.289: `trimStart()` only) is unread. 2.1.310: same chain (page contract gated on `CLAUDE_CODE_ARTIFACT_TOOLSET` or `tengu_cobalt_plinth_damson`; Thumbnail line `tengu_cobalt_plinth_campion`). Never retires.
- **The resume-from-summary override, a decision held on a Claude Code defect.**
  `skills/resume-from-summary` overrides the summary's closing order
  (`as if the break never happened`); an interactive `/compact` dispatches no `session.append`
  (against the bundled reference), and the plugin API is `EARLY ACCESS` — why the user keeps it.
  Re-run the mod test (`skills/resume-from-summary/README.md`, "After a Claude Code upgrade");
  once an interactive `/compact` reaches `session.append` and the API leaves early access, put
  the decision back to the user.

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

## Not re-read on 2.1.310

`inventory.md` claims no lookup reached: `statusline.py`'s payload builder, the session file's `entrypoint`, the
sync gate's paths, the skills `enableArtifact` disables, the shadowing rule.

## Unread in the 2.1.289 captures

- `"model": "opus"` now resolves to `claude-opus-5-5`, whose block 3 lacks opus-5's
  `# Delivering work`, `# Corrections` and reduced-delegation line and whose `Bash` description
  drops the cat/head/sed bullet — a new bundle, or `opus_5_prompt_bundle` missing the id,
  unknown (2.1.310: read on `claude-opus-5`'s catalog entry only). `sys_prompt/` drops block 3;
  the `Bash` text reaches every session.
- No backgrounded-session capture since 2.1.235; `/feedback` from a logged-in session never
  checked.

## Opened by the release notes (2.1.247–2.1.289 read by 2026-10-05, 2.1.290–2.1.310 on 2026-10-25)

- `docs/agent-tools-status-reference.md`, "The kill boundary": 2.1.257 fixed `setsid`-detached
  commands surviving a task stop or a Claude Code exit — what `agent-tools run --background` is
  built on. The task-stop half is measured there; the exit half needs a human:
  `agent-tools run --background sleep 900`, quit Claude Code, check whether the child survives.
- `docs/tool-token-limits.md`: the changelog's 20 MB Grep/Glob output cap has no matching
  constant in the search path (2.1.310: `20971520` caps only file, PDF, image and JSON reads).
- `src/claude_config/cc_pretty/` record handling for the 2.1.251–2.1.277 changes (progress ticks, batched hook notices, nested subagent results, `SubagentHandback`, the `[Subagent hand-back]` header): step 10 on 2.1.310 logs retires it.

## Open design questions

- Whether `agents/session-analysis.md` moves from `claude-opus-4-8` to `claude-opus-5-5`: the pin
  resolves, so it is a cost and behaviour choice.
- Whether the env-context window check is redesigned around the field templates it no longer
  sees (`checks.md`).
