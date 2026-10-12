# resume-from-summary

## Trigger

`sys_prompt/alan-default-next.md` names the skill, at the end of `# Context
management`. The description alone does not reach the main case: Claude Code
2.1.289 does not re-send the skill listing after a compaction. In the eight
compacted sessions on this machine on 2026-10-11, every `compact_boundary` is
followed by an `invoked_skills` attachment and no `skill_listing`, so no
description is in context to match. A resume does re-send the listing, yet in
one trial (2026-10-11, effort `high`) the description alone did not fire: the
model answered from the summary. Sessions without that prompt (background
sessions, other launchers) have only the description.

The line names two things a bare "invoke it first" lacks, and that wording
did not fire after an automatic compaction (one trial). That compaction landed
mid-task and kept the last three messages verbatim after the summary
(`compactMetadata.preservedMessages`), so the model resumed from a tool result
rather than from the summary. And the summary ends "Resume directly — do not
acknowledge the summary …", which pulls against any detour. The current
wording invoked the skill first in 3 of 3 automatic compactions, each also
mid-task, and in 2 of 2 resumes after `/compact` (2026-10-11, effort `high`).
Both clauses changed at once, so which one does the work is unmeasured.

A `SessionStart` hook (matcher `compact`, plus `resume` gated on the transcript
holding a boundary) was the first trigger built: in a test run it put the skill
first after each of four automatic compactions and on a resume. The prompt
line replaced it as the simpler mechanism; go back to the hook if the line
stops firing.

## Sizes

`cc-pretty` shows only the last leg by default, and after a compaction that leg
opens with the summary, so `--compact-all` is what makes the skeleton worth
reading. On five compacted sessions here it ran 30k–104k local tokens
(114–368 KB), against the Bash tool's 30,000-character inline cap: hence the
file. The `grep` for user messages, `AskUserQuestion` answers and boundaries
gave 3–48 lines on the same five; one session held 9 answers given only through
`AskUserQuestion`.

A recovery added about 21k tokens in the test run. At the schema's minimum
`autoCompactWindow` (100,000, so compaction near 67k) that refilled the context
enough to bring on the next compaction twice in a row; at `settings.json`'s
400,000 (compaction at 367k) it is about 6%. The skill's "Stop once you can
act" line is aimed at that.

## After a Claude Code upgrade

Re-check on a fresh compaction: the summary still names the transcript (`read
the full transcript at:`); whether a `skill_listing` now follows the boundary,
which would let the description trigger the skill without the prompt line.
