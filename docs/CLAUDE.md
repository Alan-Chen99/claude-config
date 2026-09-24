# docs/

Reference material on Claude Code's own behaviour, on this repo's prompts, and the design
records behind both. Version-pinned files name the Claude Code build they were verified
against; after an upgrade re-verify the claim and keep the label rather than re-pinning
blind — `.claude/skills/update-claude-code` governs.

## Files

| File                                       | What                                          | When to read                                            |
| ------------------------------------------ | --------------------------------------------- | ------------------------------------------------------- |
| `system-prompt-anatomy.md`                 | Simplified overview of system prompt assembly — pinned to cc 2.1.88 source | Quick orientation, understanding prompt structure       |
| `system-prompt-anatomy-source-verified.md` | Detailed anatomy with function references — pinned to cc 2.1.88 source     | Debugging context loading, source-level understanding   |
| `background-sessions.md`                   | How a session moves to the agent view (FleetView), what the fork inherits, disable knobs — cc 2.1.269 | Diagnosing a session that backgrounded itself, or a custom system prompt that stopped applying |
| `subagent-backgrounding.md`                | Which background knob `settings.json` sets, what each alternative costs, and the disjunction that decides an Agent call — cc 2.1.269 | Changing `CLAUDE_CODE_FORK_SUBAGENT`, diagnosing a subagent that backgrounded itself, editing the prompt's foreground rule |
| `tool-token-limits.md`                     | Token counting, truncation, and size limits per tool | Understanding tool output constraints, debugging limits |
| `agent-tools-status-reference.md`          | Full `agent-tools run` status grammar, passthrough differences from bare, and the kill boundary — the exhaustive half of what `sys_prompt/alan-default-next.md` states in brief; pinned to source by `scripts/check-prompt-coupling.sh` | Reading a status line in detail, diagnosing a wrapped run, or editing either side of the prompt/source coupling |
| `env-context-manifest.json`                | Pinned cc version and env-block literal set `agent-tools env-context`'s drift check is pinned to; re-pin with `scripts/check-env-context.sh --update` after a Claude Code upgrade. Byte-offset derivation for the two literal lists: `notes/env-context-manifest.md` | Reviewing or re-pinning after a drift warning |

## Subdirectories

| Directory                  | What                                          | When to read                                            |
| -------------------------- | --------------------------------------------- | ------------------------------------------------------- |
| `system-prompt-snapshot/`  | Captured system prompts, messages, tool definitions, and the full API requests they come from — live capture, cc 2.1.269, keyed by model id because cc serves two different default prompts and picks per model. Its `README.md` carries the capture procedure and every trap; read it before capturing or re-capturing anything | Comparing prompt versions, understanding API parameters, spawning a `claude` child that must authenticate |
| `opencode-system-prompt/`  | opencode prompt notes: `alan-default-commentary.md` (per-delta annotation of `alan-default-ids.md` against upstream codex gpt-5.5 `base_instructions`, from `/repos/codex/codex-rs/models-manager/models.json`), `min-commentary.md` (the diagnostic minimum baseline at `opencode/agents/min.md`), `build-self-reported.md` (session prompt assembly), `trials/` | Investigating opencode prompt behavior, or why a specific clause is present |
| `superpowers/`             | Design records from the brainstorm → plan → execute workflow: `specs/` (18) and `plans/` (12). Dated records of what was decided, not current-state docs — do not rewrite them to match later changes | Understanding why a component is shaped the way it is |
| `prompt-trials/`           | Per-case prompt-trial transcripts kept as evidence for a prompt edit | Reviewing what a prompt edit measured |
