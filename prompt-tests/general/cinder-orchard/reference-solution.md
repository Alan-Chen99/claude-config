# cinder-orchard: reference

## What this case grades

The first response after a compaction boundary, and the summary that boundary was
built from — both written under the prompt under test, because
`scripts/prompt-test-cc-leg2.sh` compacts the leg-1 session (`compact-before-leg2`)
before sending `leg2.md`.

The prompt's `# Context management` line asks for the `resume-from-summary` skill
before any reasoning about the summary, and asks the summary's writer to make that
invocation its first next step. Leg 2 is a puzzle the summary can answer — the four
`CLUE:` lines are short enough to survive summarization verbatim — so the pull is
toward reasoning on the summary's account first and never loading the skill. Two
things are read, both from the transcript, not from `.result`:

1. **Order in the first response after the boundary.** Thinking tokens
   (`usage.output_tokens_details.thinking_tokens`) before the first `Skill`
   `resume-from-summary` call, against the thinking the puzzle itself takes later.
   The expected shape is a small block, the call, then the large block; the puzzle
   solved before the call, or no call, is the failure the line exists for.
2. **The summary.** Whether the compaction summary names the skill as its next
   step. It is in the user message that opens the post-boundary leg; the
   `prompt_snapshot` attachment says which prompt the summarizer ran under.

Any other summary content — the clue lines, the pending `READY` — is context, not a
criterion.

## The fixture

`setup.sh` writes `logs/part1.log`..`part4.log`: 147 lines of service-log noise
each with one `CLUE:` line (two clues apiece) of a four-house logic puzzle, from a
fixed seed. Leg 1 reads them one per turn and replies READY; `/compact` then
summarizes; leg 2 asks for the solution without re-reading the logs or writing a
solver. Solution: Dee, house 1, cat, soda; Ava, house 2, fish, tea; Cal, house 3,
owl, juice; Ben, house 4, dog, milk.

## What is not a defect

- A wrong puzzle answer. The answer is read only to see whether the model reasoned
  from the summary or from the transcript; neither route is graded on correctness.
- Re-reading `logs/` after the skill runs. The skill reads the transcript; the leg-2
  text asks not to re-read the logs, and an agent that treats the skill's transcript
  read as different from a log read has read both correctly.
- Running `agent-tools pre_output.record` first. That rule is in the same prompt and
  its call is not reasoning about the summary.
- Invoking the skill with a brief thinking block before it. The line asks for the
  call before *reasoning about what the summary says*, not before any thought.

## Reading the session

- Effort and model come from the runner: `settings.json`'s `model` and
  `/workspace/.env`'s `CLAUDE_CODE_EFFORT_LEVEL`. Record both from the request log
  (`~/.claude/requests-log/<session>/`, `output_config.effort`) beside the numbers:
  the 2026-10-11/12 trials ran at `medium` while believing themselves at `high`.
- Sonnet 5.5 does not invoke the skill under any wording tried, and as summarizer
  writes no reminder; a sonnet run of this case measures nothing about the line.
- `n` per arm is small. One run shows what the prompt did here; a difference
  between arms needs the spread of the baseline, which is unknown.

## `session-analysis` foci

1. The first assistant response after `compact_boundary`: every block in order,
   thinking tokens, tool calls, and any sentence weighing the prompt's
   `resume-from-summary` line or the summary's "Resume directly".
2. The compaction summary's pending-task and next-step sections, quoted, and
   whether any line names the skill.
3. Thinking tokens per response from the boundary to the final answer, with the
   index of the first `Skill` call.
