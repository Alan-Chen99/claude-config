# halve-the-runbook: reference

Guidance for a grader, under `docs/prompt-testing-design.md` and
`.claude/skills/prompt-tests/SKILL.md`. It is **not a key**. The tested agent
never saw this file, so nothing in it is something that agent should have done;
anything below that is satisfiable only by a reader of this file is defective as
written, and saying so is part of the grader's job.

## What this case grades

Whether a runbook still **works** after being compressed to half its length.

Not whether it retained any particular content. The fixture is not a reference
document and nothing downstream looks a fact up in it. It is a procedure, and the
only question about a procedure is whether following it produces the right
actions.

## The fixture, and why it is the one it is

`fixture/SKILL.md` is this repo's own `.claude/skills/update-claude-code/SKILL.md`
verbatim, taken at `34a81cec` (4,664 words). `changelog.py` and `citecheck.sh`
sit beside it because they do in the real skill directory; nothing asks the agent
to touch them.

It exists because of a specific failure. Asked to re-check this repo after a
Claude Code upgrade with no skill in hand, an agent missed things, and the user
had to push it through check after check. The skill is the write-up of that
session. Its purpose is that the next upgrade **just works and does not create
bugs** — not that questions about Claude Code can be answered out of it.

That purpose sets the floor and the ceiling of the grading:

- **Floor: having no skill at all is correct.** An agent with no runbook
  rediscovers the same checks, slowly. So a compression that prescribes *less*
  than the source has lost efficiency, not correctness, and must not be priced as
  a defect. "It could have kept more" is not a finding.
- **Ceiling: what a skill adds is claims, and claims are what can be wrong.**
  Everything the compression asserts — an order, a place to run something, a
  sufficiency — is a way for the delivered runbook to be worse than nothing.

## What a defect looks like here

Four shapes. They are recognitions, not a checklist, and a run can exhibit one
the list does not name.

**1. A step that is now wrong.** Following the delivered text produces an action
the source would not have produced. The fixture's sharpest examples are steps 5
and 14: both repoint installs shared with every other session on the machine, and
both are marked for the canonical checkout only. A compression that drops the
"canonical checkout only" / "**there only**" qualifier delivers a runbook that
causes the breakage the source exists to prevent. This is the most expensive
thing available in this fixture and the cheapest to do by accident, because the
qualifier is four words attached to a long row.

**2. A step left unrunnable.** The compression removed what made the step
executable. Calibration matters here, because the intended kind of cut looks
similar: turning

> `agent-tools/src/hook_input.rs:13-35` | `session_id`, `tool_name`, …

into *"check that the hook still works"* is a **good** compression — the field
list is re-derivable by opening the file, and the instruction is still runnable.
Losing the *file* would not be. Likewise a step reduced to "re-pin env-context"
with no script named and no `--update` is unrunnable; reduced to
`./scripts/check-env-context.sh`, read the diff, then `--update` is not, whatever
else went with it.

**3. Order destroyed, or its dependency dropped.** The source opens §1 with
"Ordering is load-bearing" and each row says why it sits where it does. The one
that costs most is step 2 — re-extract the decompile — because steps 4, 7 and 8
read that tree, and run before it they *pass vacuously*. A compression that
reorders, renumbers, or drops the dependency has made the rest of the runbook
produce false greens, and a false green is the failure the whole skill is
against. Note this is not "a fact was lost": the delivered procedure now returns
a wrong answer.

**4. A claim the source denies.** Chiefly sufficiency. The source's core
principle is "a check that cannot fail is not a check", and §2 exists to say what
each green result is blind to — it calls that table "the point of the skill".
A delivered runbook that lists the checks and stops has not merely dropped a
section: it licenses its reader to conclude the repo is fine when the source says
that conclusion is unsupported. **That is the one drop that goes below the
floor**, because no-skill does not tell anyone the checks were sufficient
either. Grade it as a wrong claim, not as a missing section — and if the
compression carries the blind-spot warning in two sentences instead of a
thirteen-row table, that is a success, not a loss.

## What is not a defect

Say so explicitly when the output does these; a grader that files them as costs
is reading fidelity, which this case does not grade.

- Dropping a fact, a field name, a `chunk-*.js:LINE` citation, a version number,
  or an expected-output string. All of it is re-derivable from the file or
  command named. It costs a re-read.
- Dropping §4 ("still to check") wholesale. Those are dated open items; a runbook
  without them is a correct runbook with less memory in it.
- Collapsing several rows into one, or a table into prose.
- Being shorter than the target, or spending words unevenly.
- Rewriting rather than deleting — the task says cut, not excise.

## Length

Source 4,664 words; the task asks for about 2,300. Whether the doc can reach
that without losing correctness is this case's **open question**, not a stated
premise, and a run is evidence about it. If an arm lands at the target with all
four shapes clean, the answer is yes for that arm. If every arm that reaches the
target does so by taking one of the four, record that: it is a finding about the
task, and it is the sort of thing a grader should reach through the
*undiscoverable from the agent's position* outcome rather than by charging the
agent.

Ignoring the target outright is a separate matter and belongs in the judgement as
what it is — the user asked for half and did not get it.

## Stage 2: the downstream reader

`downstream.md` puts the delivered runbook in front of a reader that has to act
on it, on stock Claude Code with no repo: *give the exact sequence of commands
and where to run each, and say what still has to be checked by hand once they all
come back green.*

The two halves are deliberate. The first reads out order and place — shapes 1 and
3. The second reads out sufficiency — shape 4. The reader is an instrument, not a
session under test; record its answer verbatim beside the judgement and do not
analyse it.

## Reading the session

The grader reads the whole session, per `SKILL.md` "Grader dispatch". Two things
specific to this fixture are worth watching for and are **not** gradeable
criteria on their own:

- Whether the session went looking for the original outside the scratch cwd —
  any path under a `claude-config` checkout, or `/repos/claude-code-decompiled`.
  Reading a `prompt-tests/` path is contamination and invalidates the run. The
  others are not, but they change what the run measures: an agent holding the
  repo can see which details are load-bearing, and an agent holding only
  `SKILL.md` cannot. Report it either way.
- Whether the agent treated the doc as something a reader will act on, or as
  text with a word count. The task says neither.

## `session-analysis` foci

Changed wholesale on 2026-09-18 with the fixture; nothing stored under
`prompt-tests/runs/halve-the-runbook/` was taken under them, and none of it is
comparable to a run of this case — it all measures the payments-relay fixture
this case carried until that date. It is kept because
`docs/prompt-testing-design.md` and `notes/` cite it as evidence for claims about
grading, which remain true of the runs they were taken from.

1. Every point at which the agent decides what to cut and what to keep, quoted —
   in particular any block weighing something it then removed.
2. Whether the agent read the file back after rewriting it, and whether anything
   changed as a result.
3. Whether the agent reasons about what the runbook is *for* — an upgrade going
   right — as against what it *contains*.
4. What the agent told the user about the cut: a bare word count, a list of what
   went, or a named judgement call.
