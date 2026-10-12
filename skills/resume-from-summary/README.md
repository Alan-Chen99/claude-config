# resume-from-summary

## Trigger

`sys_prompt/alan-default-next.md` names the skill at the end of `# Context management`:

> On continuing from a summary of earlier work, invoke the `resume-from-summary` skill first —
> before reasoning about what the summary says, even mid-task; its "Resume directly" does not waive
> it. When writing such a summary, make this invocation its first next step.

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
and thinking is not an action. *When writing such a summary, make this invocation its first next
step* — the user's direction (2026-10-12): the compaction request carries this prompt as its system
block (seen in the proxy's capture of every `/compact` here), so the summarizer reads the line, and
cc's compaction instruction ends the summary with a numbered "Optional Next Step" that the resumed
model is told to pick up; a reminder there is nearer the resumed model than the prompt's last line.

## Measurements

Thinking before the first `Skill` call, counted from the transcript's summarized thinking blocks
(`--thinking-display summarized`) and each response's `output_tokens`. Fixtures are log files
with one planted line each, read one file per turn.

Effort is read from the request's `output_config.effort` in `~/.claude/requests-log/<session>/`,
not from settings: the trial launchers unset `CLAUDE_CODE_EFFORT_LEVEL`, and with `settings.json`
saying `high` the requests of every prompt-line trial below carried `medium`. Interactive sessions
here run at `max` (`/workspace/.env`).

- **Opus 5.5, effort `medium`, "before your next action" (2026-10-11).** CODEWORD fixtures: eight
  parts under `autoCompactWindow` 100,000, or four parts, `/compact`, then a resume asking for a
  pre-compaction line number. Skill first in 3 of 3 automatic compactions and 2 of 2 resumes,
  with 121–517 characters of thinking (107–267 output tokens) before the call. The `SessionStart`
  hook arm (below, effort `max`) on the same fixture also put the skill first, after 4.7k–24k
  characters of thinking: the model deliberated over the hook, the summary and the preserved tail.
- **Sonnet 5.5, effort `medium` (2026-10-12).** Fixtures where the first response after the
  boundary has a puzzle to reason about — eight PUZZLE logs under `autoCompactWindow` 100,000; four
  CLUE logs, `/compact`, a resume asking for the logic puzzle's solution — and the CODEWORD resume
  fixture. The skill was invoked in 0 of 19: 7 with the shipped placement clause, 6 with "before
  your next action", 3 with "you MUST invoke" in front, 3 with the summary-reminder clause. Two of
  the "before your next action" runs are the configuration of Opus's 2 of 2 resumes — same fixture,
  wording, effort and harness — and the proxy's captures show each request carrying the line, the
  `Skill` tool and the same `thinking`/`effort` fields as Opus's; the difference is the model. The
  model read on or solved the puzzle from the summary (585–1,621 characters of thinking on the deep
  resumes) and ran the prompt's `pre_output.record` call in 14 of 19 (the other 5, all deep
  resumes, skipped the response template too), so the prompt is read and this line is what it
  skips. As summarizer, Sonnet wrote no reminder into the summary in 3 of 3 runs
  whose compaction request carried the summary-reminder clause. The eight-part PUZZLE fixture
  compacts under Sonnet; the CODEWORD one (`autoCompactWindow` 95,000) does not.
- **Opus 5.5, effort `max`, the shipped line (2026-10-12).** `prompt-tests/general/cinder-orchard`
  through the runners, twice: four CLUE logs, `/compact`, then the puzzle. The summary written under
  the line named the skill as item 1 of its "Optional Next Step" in 2 of 2, and the first response
  after the boundary ended in the `Skill` call in 2 of 2 — after 13,204 and 16,199 thinking tokens
  (`output_tokens_details.thinking_tokens`) in which the model solved the puzzle from the summary's
  clue lines, checked uniqueness, and weighed the response template against "one line per person";
  one run opened its thinking by noting the line and reasoned on, the other closed with "the rule
  is about tool invocation order". The call is first among tools and last among thoughts: at this
  effort the clause does not move reasoning after the skill, and the block before the call is
  50–100× the medium-effort figure above. Recovery after the call took 6–9 responses (one run also
  loaded `session-analysis`) and the sessions cost 1.7–2.4 USD each. Not run: the same case with
  the first clause removed, which is what the clause's retirement condition compares against.

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
transcript at:`) and still says "Resume directly", which the prompt line answers; the compaction
request still carries the session's system prompt and still asks for a next-step section, which
the summary-reminder clause leans on; and whether a `skill_listing` now follows the boundary, which
puts the description back in reach of a session without the prompt. `prompt-tests/general/cinder-orchard`
runs all of it: leg 1, `/compact`, leg 2.
