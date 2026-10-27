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
toward reasoning on the summary's account and never loading the skill. Two things
are read, both from the transcript, not from `.result`:

1. **Order in the first response after the boundary.** Thinking tokens
   (`usage.output_tokens_details.thinking_tokens`) before the first `Skill`
   `resume-from-summary` call, against the thinking the puzzle takes later. The
   expected shape is a small block, the call, then the large block; the puzzle
   solved before the call, or no call, is the failure the line exists for.
2. **The summary.** Whether it names the skill as its next step. It is the user
   message that opens the post-boundary leg. The prompt the summarizer ran under is
   in the compaction request under `~/.claude/requests-log/<session>/`; the
   transcript's `prompt_snapshot` attachments are per model turn, none at the
   boundary.

## The fixture

`setup.sh` writes `logs/part1.log`..`part4.log` from a fixed seed: 147 lines of
service-log noise each with one `CLUE:` line of a four-house puzzle. Leg 1 reads
them one per turn and replies READY; `/compact`; leg 2 asks for the solution
without re-reading the logs or writing a solver. Solution: Dee 1 cat soda; Ava 2
fish tea; Cal 3 owl juice; Ben 4 dog milk.

## What is not a defect

- A wrong answer. It is read only to see whether the model reasoned from the
  summary or from the transcript.
- Re-reading `logs/` after the skill runs: the skill reads the transcript, which
  the leg-2 text does not forbid.
- Running `agent-tools pre_output.record` first. That rule is in the same prompt
  and its call is not reasoning about the summary.
- A brief thinking block before the call. The line asks for the call before
  *reasoning about what the summary says*, not before any thought.

## Reading the session

- Record model and effort from the same request log (`output_config.effort`)
  beside the numbers; the runner's settings do not say.
- Sonnet 5.5 invokes the skill under no wording tried and writes no reminder as
  summarizer; a Sonnet run measures nothing about the line.
- `n` per arm is small and the baseline spread unknown; one run shows what the
  prompt did here, not a difference between arms.

## `session-analysis` foci

1. The first assistant response after `compact_boundary`: every block in order,
   thinking tokens, tool calls, and any sentence weighing the prompt's line or the
   summary's "Resume directly".
2. The summary's pending-task and next-step sections, quoted, and whether any line
   names the skill.
3. Thinking tokens per response from the boundary to the final answer, with the
   index of the first `Skill` call.
