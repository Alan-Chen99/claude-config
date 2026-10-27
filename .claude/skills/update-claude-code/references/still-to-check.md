# Still to check — as of 2026-10-25, Claude Code 2.1.310

Open items with what retires each. Delete an entry once closed; add one for every gap you find
rather than leaving it in a session transcript.

## Every upgrade

- **The vendored skills' loaders.** `skilldiff.sh` compares asset bodies, so a loader that gains
  a placeholder, prefix or substitution changes what the built-in says while the copies stay
  byte-identical. Re-read both: `artifact-design`'s as of 2.1.310 is in the script's header,
  `artifact-diagramming`'s (2.1.289: `trimStart()` only) is unread. Never retires.
- **The resume-from-summary override, a decision held on a Claude Code defect.** Why the user
  keeps it, and the mod test to re-run: `skills/resume-from-summary/README.md`, "After a Claude
  Code upgrade". Once an interactive `/compact` reaches `session.append` and the plugin API
  leaves `EARLY ACCESS`, put the decision back to the user.

## Open decision

- **Defer `Artifact` instead of removing it.** A plugin's `tool.describe` hook (`isDeferred`)
  can move a built-in behind ToolSearch, keeping `Artifact` one deferred line away and the
  built-in `artifact-*` skills; against it, the plugin API is early access, and it trades a
  settings key for a plugin. Decide, or record the decision not to.

## Measurements the source cannot settle

- The 2.1.269 measurement in `REPORT_BUDGET`'s doc comment, against the 10,000-character
  persistence ceiling. Retire with a `PostToolUse` command hook emitting 10,500 characters of
  `additionalContext` and a read of what the next turn sees: a `<persisted-output>` stub, or the
  text.
- `worker_permission_prompt` has never fired through this config (wired 2026-10-05). Retire by
  watching one worker permission push.
- `claude agents` sessions are inferred, not measured, to get `SessionStart` rather than
  `SubagentStart`; read one transcript.
