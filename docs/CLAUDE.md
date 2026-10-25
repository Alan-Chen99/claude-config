# docs/

Reference material on Claude Code's own behaviour, on this repo's prompts, and the design
records behind both. Version-pinned files name the Claude Code build they were verified
against; after an upgrade re-verify the claim and keep the label rather than re-pinning
blind — `.claude/skills/update-claude-code` governs.

## Files

| File                                       | What                                          | When to read                                            |
| ------------------------------------------ | --------------------------------------------- | ------------------------------------------------------- |
| `codex-prompt-capture.md` | Live Codex greeting capture, complete API token reconciliation, source map and reproduction | Investigating Codex prompt costs or refreshing its snapshot |
| `system-prompt-anatomy.md`                 | Simplified overview of system prompt assembly — pinned to cc 2.1.88 source | Quick orientation, understanding prompt structure       |
| `system-prompt-anatomy-source-verified.md` | Detailed anatomy with function references — pinned to cc 2.1.88 source     | Debugging context loading, source-level understanding   |
| `prompt-rebase.md`                         | Rebasing `sys_prompt/` on a cc release: reading both sides, the pins, the deliberate divergences | After a Claude Code upgrade; when `scripts/check-prompt-upstream.py` fails |
| `background-sessions.md`                   | How a session moves to the agent view (FleetView), what the fork inherits, disable knobs — cc 2.1.289 | Diagnosing a session that backgrounded itself, or a custom system prompt that stopped applying |
| `subagent-backgrounding.md`                | The two background knobs `settings.json` sets so `-p` matches interactive, what each alternative costs, what a subagent loses at its turn end, and what outlives a `claude -p` turn end (agent, background task, foreground call, `Monitor`, `Stop` hook) — cc 2.1.289 | Changing either knob, diagnosing a subagent that reported "waiting" or a `-p` run that stopped waiting, editing the prompt's wait-turn exception, deciding how a `-p` session waits |
| `prompt-testing-design.md`                 | Why prompt testing here works as it does: what a run's result is, why a rubric cannot be written in advance, the two-argument grader and its two guards, and what none of it measures | Before changing a rubric, a grading dispatch, or `.claude/skills/prompt-tests/SKILL.md` |
| `tool-token-limits.md`                     | Token counting, truncation, and size limits per tool | Understanding tool output constraints, debugging limits |
| `agent-tools-status-reference.md`          | Full `agent-tools run` status grammar, passthrough differences from bare, and the kill boundary — the exhaustive half of what `sys_prompt/alan-default-next.md` states in brief; pinned to source by `scripts/check-prompt-coupling.sh` | Reading a status line in detail, diagnosing a wrapped run, or editing either side of the prompt/source coupling |
| `env-context-manifest.json`                | Pinned cc version and env-block literal set `agent-tools env-context`'s drift check is pinned to; re-pin with `scripts/check-env-context.sh --update` after a Claude Code upgrade. Byte-offset derivation for the two literal lists: `notes/env-context-manifest.md` | Reviewing or re-pinning after a drift warning |
| `total-tokens-reminder-trial.md`           | Pre-registration for the randomized `off` vs `padded-countdown` trial `scripts/claude.sh` draws per interactive session: the frozen candidate-outcome list, the gating manipulation check, arm recovery, and what invalidates a session — cc 2.1.269, clamp re-derived on 2.1.289 | Before analysing the trial, before adding an outcome to it, and after any Claude Code upgrade that touches the reminder |

## Subdirectories

| Directory                  | What                                          | When to read                                            |
| -------------------------- | --------------------------------------------- | ------------------------------------------------------- |
| `system-prompt-snapshot/`  | Captured system prompts, messages, tool definitions, and the full API requests they come from — live capture, cc 2.1.310, keyed by model id because cc serves two different default prompts and picks per model. Its `README.md` carries the capture procedure, the three credentials and every trap; read it before capturing or re-capturing anything. What the captured prompt says for this build is `what-the-model-gets.md` plus eight `notes/cc-2.1.269-*.md` records | Comparing prompt versions, understanding API parameters, spawning a `claude` child that must authenticate |
| `opencode-system-prompt/`  | opencode prompt notes: `alan-default-commentary.md` (per-delta annotation of `alan-default-ids.md` against upstream codex gpt-5.5 `base_instructions`, from `/repos/codex/codex-rs/models-manager/models.json`), `min-commentary.md` (the diagnostic minimum baseline at `opencode/agents/min.md`), `build-self-reported.md` (session prompt assembly), `trials/` | Investigating opencode prompt behavior, or why a specific clause is present |
| `superpowers/`             | Design records from the brainstorm → plan → execute workflow: `specs/` (22) and `plans/` (15). Dated records of what was decided, not current-state docs — do not rewrite them to match later changes | Understanding why a component is shaped the way it is |
| `prompt-trials/`           | Per-case prompt-trial transcripts kept as evidence for a prompt edit | Reviewing what a prompt edit measured |
