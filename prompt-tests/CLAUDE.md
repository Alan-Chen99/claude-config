# prompt-tests/

Runner-neutral prompt evaluation cases. `runs/` holds what runs produced.

**Load `.claude/skills/prompt-tests` before running, grading, or editing
anything here.** It carries the runners, the contamination rules, the grader
dispatch, and how a run is read; `docs/prompt-testing-design.md` carries why.
Neither is repeated in this file, and a second wording of either here would not
say which one governs.

## This file reaches graders by itself

Opening any file under `prompt-tests/` with the **Read** tool makes Claude Code
attach this whole file as a system-reminder — the trigger is the Read/Edit/Write
path, not Bash. A grader cannot notice that its own instructions were enlarged,
and telling it not to read this file does not prevent it.

So this file says nothing about any individual case: not what an arm did, not
how many runs went which way, not what the expected answer is, and not what the
case probes — a description of the probe is most of the answer for a grader
working phase 1 with the reference deliberately withheld. Each case's
`reference-solution.md` is the one place its situation is described, and a grader
receives it when the dispatch hands it over.

**If you add anything case-specific here, you have re-armed the channel.** The
test is mechanical: a sentence naming a case, an arm, a count or an outcome does
not belong here, however useful it looks. A rule that holds for every case does.

Retire this section if Read-path attachment of directory `CLAUDE.md` files stops
happening — check by reading one case's `task.md` with the Read tool in a session
that has not otherwise touched this directory.
