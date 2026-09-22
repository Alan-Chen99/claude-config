# Decision journal — writing-for-agents loop3

Compressed to durable content. Full reasoning lives where it survives this loop:
commit messages, `sys_prompt/CLAUDE.md` for anything justifying a prompt line,
and each case's `prompt-tests/runs/<case>/README.md`.

**Closed, discharged, no longer re-argued.** DEC-001 `prompt-tests/CLAUDE.md`
states no run result (iter 1) — superseded by DEC-009, which found it applied
the rule to results only. DEC-002 delete two cases on the keeping-burden
argument (iter 1) — extended to the whole corpus in iter 5. DEC-003 leave
`payments-relay/` (iter 1) — its two-round clause was spent and the directory is
deleted.

## DEC-004 — compress by class-of-line, not by target length (iter 2, conf 84)
Claim / restatement / duplicate-of-code / trap, cut in that order, stop at trap.
**Iter 5**: the strongest tool this loop has. Every deletion in iter 5 was
class-of-line: verdict bands are claims, per-case entries in two files are
restatements, `## Editing the system-under-test` duplicated
`skills/prompt-engineer-v2/`.

## DEC-005 — verify a doc edit with a differential probe (iter 2, conf 80)
Two fresh readers, one per version, same question, diff the lists. Positive
findings stand; a *null* does not, because the question asked pre-selects for
the class the compression rule keeps. Generalised: state what a null cannot rule
out beside the null.

## DEC-006 — fix cwd contamination in the runners, not in a naming rule (iter 3, conf 92)
Scratch cwd is `/tmp/ptcc.XXXXXXXX` in all three runners. A mechanism holds
without anyone remembering it, and this one is checkable by grep.
**Re-evaluate**: a leak through a channel the scratch path does not carry — iter
5 found one of that shape (DEC-009), in the grader's direction rather than the
tested agent's.

## DEC-007 — price written content by reach, not by existence (iter 3, conf 74)
Shipped. Reasoning and retirement condition in `sys_prompt/CLAUDE.md`,
§`# Writing for other agents`. Recorded basis was per-session bytes, a metric the
objective never names; the one it does name ran the other way (the shipped arm
wrote 1.6x the total). Stands on the artifacts rather than the counts. The
growth question is open.

## DEC-008 — delete the `Claim less` hedge endorsement rather than pricing it (iter 4, conf 80)
Shipped. Three arms on `unconfirmed-cause` reached the same verdicts with and
without it; the priced-hedge arm wrote 30% more and rewrote code mid-investigation.
`# Epistemic Integrity`'s No Unexplained Residue Rule forbids what it licensed.
**Framing bias** (iter 4, self-recorded): the fixture was built from the note's
argument, and arm D agreed with a preference already held.
**Independent evaluation (iter 5): not done.** The decisions template asks for it
on a later iteration and this round spent its milestone on cleanup. It is the
first item in the `(instruction)` for iter 6, with the fixture the deletion's
own retirement condition names.

## DEC-009 — one description per case, in the case's own reference (iter 5, conf 86)
- **Chosen**: `prompt-tests/CLAUDE.md` carries only what is true of every case;
  each case's `reference-solution.md` is the single place its situation is
  described; a reference states no result, prediction, verdict band or expected
  answer. Thirteen pending banners deleted, not renewed.
- **Alternatives**: check each reference and re-banner what fails (renews the
  ratchet); delete every reference (loses the nuance a rubric is for); move the
  invariants to a new grader-only file (relocation, and the leak survives for
  anything that Reads a case path).
- **Reasoning**: the file auto-attaches to any session that Reads under
  `prompt-tests/`, and phase 1 of the dispatch withholds the reference on
  purpose. A probe description is most of what it withholds, so the per-case
  entries defeated the withholding through a channel the grader cannot see or
  decline. Iteration 1 saw the channel and removed only the results. Separately,
  two descriptions of one case is the restatement class: nothing says which
  governs, and iter 5 found three claims stale in one copy and not the other.
- **Re-evaluate**: a grader that needs cross-case context and cannot get it —
  the invariant statements were deleted, not relocated, so this is the live risk.
  Also if Claude Code stops auto-attaching on Read, which would make the whole
  argument inert.
- **Framing bias**: I reached the rule from one mechanism (the injection) and it
  happened to license the largest deletion available. A reader who does not
  believe the injection claim gets a weaker argument for the same cut — the
  restatement half still holds, but it would not alone justify deleting the
  invariant statements.
- **Independent evaluation**: not-started.
- 2026-09-22T00:00:00Z
