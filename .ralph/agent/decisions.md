# Decision journal — writing-for-agents loop3

Only decisions still open to re-argument, and only the half `sys_prompt/CLAUDE.md` does not
carry: what else was on the table, the framing bias, whether anyone independent looked, the
revert. Everything discharged is in the commit messages.

**Closed**: DEC-001–031, 035–036, 038–044, 046. Content in the commit messages and in
`sys_prompt/CLAUDE.md`; none has an independent evaluation.

## DEC-032 / 033 / 034 / 037 — four shipped-or-deleted lines still open to re-argument

Reverts, with what leaves each unevaluated: `d98c5753` (032, keep the self-consequence bullet —
the blind comparison preferred the *untreated* arm); `9504b5dc` (033, cut the duplicated
rationale — both arms delivered the same artifact, so the confidence is in the cut being cheap);
`291d3c55` (034, delete `pre_output.record`'s NEVER-uncertainties rule — the independent
evaluation disagreed and was overridden). 037, keep `# Writing for other agents`: no revert, and
the arms diverged on depth as well as prompt.

## DEC-045 — the branch's edits do not reach any session here (iter 34, conf 95)

Mechanism and verification in `mem-1790273746-2aa1`. Answered 2026-09-25: *"i may choose to merge
myself, but you shoudl not do that."* So a round's product remains an edit no session here runs —
a fact every round states rather than a defect it repairs. **Revert**: n/a.

## DEC-047 / DEC-048 — two closed-but-revertable rounds (iter 36, 37)

047, the scope wording: decided and not shipped, measurement in `997a5c02`; the round wrote the
wording it judged and its own ship condition was not met. **Revert**:
`git checkout 3c5bec5e -- sys_prompt/CLAUDE.md`. 048, *public-ready on your parts*: read as
*repair claims this branch falsified, sweep citers, change nothing else*. **Framing bias**: it
chose the reading it could finish inside a merge-only instruction. **Revert**:
`git revert e8589613`, which takes the README repairs too.

## DEC-049 / DEC-050 — the one shipped line, and its harm case (iter 38, 39; conf 85)

One line under `# Completeness`; claim, cost and retirement condition in `sys_prompt/CLAUDE.md`,
probes at `git checkout f75aceb6 -- prompt-tests/runs/partial-regeneration` and
`git checkout a247868e -- prompt-tests/runs/spend-window`. 39 ran its harm case, did not refute
it, and shipped **no** wording for the new cost it found (*what a session escalates, it cements*)
— the alternative being an invented clause on one positive reading, which the contract now
forbids. **Framing bias**: 38 wrote the wording it measured; 39 had an interest in its
predecessor's line surviving. Both mitigated by pre-registered outcomes and a blind decisive
reader, not removed. **Independent evaluation**: done, blind, both transcripts, both rounds.
**Revert**: `git revert f75aceb6` plus the `sys_prompt/CLAUDE.md` paragraph it replaced.

## DEC-051 — `sys_prompt/CLAUDE.md` is bounded by its shape, not by a size (iter 40, conf 90)

Superseded in mechanism by DEC-052; the principle stands. **Revert**: `git revert 98aff4c5`,
which also restores the 2,882 tokens that round cut.

## DEC-052 — the shape rule is a script, or it is not a rule (iter 41, conf 90)

40's bound was unfalsifiable (scratchpad C1), so it is replaced rather than patched:
`scripts/check-prompt-rationale.sh` requires each rationale section's heading to quote prompt
text verbatim, and `.github/workflows/ci.yml` runs it. **Alternatives**: a token ceiling on the
file at the prompt's size — measured, and it forces a 26% cut into paragraphs carrying live
retirement conditions, which is the *cut the qualifying clause* failure 33 already measured; a
per-paragraph ownership check — tested, and it both false-positives on short literals (`haiku`,
`, and `) and false-negatives on legitimate continuation paragraphs; keep the bound and add the
check later, which is the deferral the contract forbids. **Framing bias**: a round that finds its
predecessor's rule unfalsifiable has an interest in replacing it with its own, and a structural
finding flatters a round with no measurement to report — mitigated by the check being watched to
fail, by the two faults it named being ones this round did not plant, and by C3's growth numbers
being recomputed from git rather than inherited. **Not covered**: the file's ~3,500-token
upstream-rebase half owns no prompt line, so the check does not reach it; #115 asks the owner
before cutting it. **Independent evaluation**: none. **Revert**: `git revert 2836b36a`.
