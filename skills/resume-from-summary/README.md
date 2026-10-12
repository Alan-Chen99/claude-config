# resume-from-summary

## Trigger

`sys_prompt/alan-default-next.md` names the skill at the end of `# Context management`:

> On continuing from a summary of earlier work, invoke the `resume-from-summary` skill first —
> before reasoning about what the summary says, even mid-task; the summary's "Resume directly"
> does not waive it.

The description alone does not reach the main case: Claude Code 2.1.289 does not re-send the
skill listing after a compaction. In the eight compacted sessions on this machine on 2026-10-11,
every `compact_boundary` is followed by an `invoked_skills` attachment and no `skill_listing`, so
no description is in context to match. A resume does re-send the listing, yet in one trial
(Opus 5.5, effort `high`) the description alone did not fire: the model answered from the
summary. Sessions without that prompt (background sessions, other launchers) have only the
description.

Each clause answers a pull seen in a trial. *Even mid-task*: an automatic compaction lands
mid-task and keeps the last three messages verbatim after the summary
(`compactMetadata.preservedMessages`), so a bare "invoke it first" did not fire in one trial —
the model resumed from a tool result rather than from the summary. *The summary's "Resume
directly" does not waive it*: the summary ends "Resume directly — do not acknowledge the summary …
Pick up the last task as if the break never happened." *First — before reasoning about what the
summary says* — the user's direction (2026-10-12), replacing "before your next action": reasoning
done before the skill loads is done on the summary's account, which the skill exists to replace,
and thinking is not an action.

## Measurements

Thinking before the first `Skill` call, counted from the transcript's summarized thinking blocks
(`--thinking-display summarized`) and each response's `output_tokens`. Fixtures are log files
with one planted line each, read one file per turn.

- **Opus 5.5, effort `high`, "before your next action" (2026-10-11).** CODEWORD fixtures: eight
  parts under `autoCompactWindow` 100,000, or four parts, `/compact`, then a resume asking for a
  pre-compaction line number. Skill first in 3 of 3 automatic compactions and 2 of 2 resumes,
  with 121–517 characters of thinking (107–267 output tokens) before the call. The `SessionStart`
  hook arm (below) on the same fixture also put the skill first, after 4.7k–24k characters of
  thinking: the model deliberated over the hook, the summary and the preserved tail.
- **Sonnet 5.5 (2026-10-12).** Fixtures where the first response after the boundary has a puzzle
  to reason about — eight PUZZLE logs under `autoCompactWindow` 100,000; four CLUE logs,
  `/compact`, a resume asking for the logic puzzle's solution "in your head, without running
  code" — and the CODEWORD resume fixture. The skill was invoked in 0 of 12: 5 with the shipped
  wording, 4 with "before your next action", 3 with "you MUST invoke" in front. The model read on
  or solved the puzzle from the summary (585–1,621 characters of thinking on the deep resumes)
  while obeying the prompt's `pre_output.record` rule in every run, so the prompt is read and this
  line is what it skips. Both wordings are thus unmeasured on Opus for the deep fixtures, and the
  clause's effect on pre-skill reasoning is unmeasured anywhere: where the skill fired, the
  reasoning before it was already short. The eight-part PUZZLE fixture compacts under Sonnet; the
  CODEWORD one (`autoCompactWindow` 95,000) does not.

A `SessionStart` hook (matcher `compact`, plus `resume` gated on the transcript holding a
boundary) was the first trigger built: in a test run it put the skill first after each of four
automatic compactions and on a resume. The prompt line replaced it as the simpler mechanism; go
back to the hook if the line stops firing.

## Sizes

`cc-pretty` shows only the last leg by default, and after a compaction that leg opens with the
summary, so `--compact-all` is what makes the skeleton worth reading. On five compacted sessions
here it ran 30k–104k local tokens (114–368 KB), against the Bash tool's 30,000-character inline
cap: hence the file. The `grep` for user messages, `AskUserQuestion` answers and boundaries gave
3–48 lines on the same five; one session held 9 answers given only through `AskUserQuestion`.

A recovery added about 21k tokens in the hook test run. At the schema's minimum
`autoCompactWindow` (100,000, so compaction near 67k) that refilled the context enough to bring
on the next compaction twice in a row; at `settings.json`'s 400,000 (compaction at 367k) it is
about 6%. The skill's "stop once you can act" is aimed at that: with it, recovery took 4–5k
tokens in each of the three prompt-trigger trials, and none compacted again.

`SKILL.md` is 200 tokens under the 200 cap the user set (2026-10-12): the description, the two
commands, and what to recover. Cut to fit: the handoff target, the skeleton's `recover:` header,
and the request to name where the summary and the transcript disagree.

## After a Claude Code upgrade

Re-check on a fresh compaction: the summary still names the transcript (`read the full
transcript at:`) and still says "Resume directly", which the prompt line answers; and whether a
`skill_listing` now follows the boundary, which puts the description back in reach of a session
without the prompt.
