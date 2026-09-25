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
*repair claims this branch falsified, sweep citers, change nothing else*; the two index rows were
withdrawn inside the round on #98. **Framing bias**: it chose the reading it could finish inside
a merge-only instruction. **Revert**: `git revert e8589613`, which takes the README repairs too.

## DEC-049 — one line ships under `# Completeness` (iter 38, conf 85)

Claim, cost and retirement condition in `sys_prompt/CLAUDE.md`; probe and its three
pre-registrations at `git checkout f75aceb6 -- prompt-tests/runs/partial-regeneration`. **Alternatives**: ship
nothing and hand the baseline to 39, the deferral this round deleted from the contract; put the
line in `# Writing for other agents`, where the ablation had just shown the block
arm-independent on this failure. **Framing bias**: the round wrote the wording it measured —
mitigated, not removed, by the fixture being built from `0d3c560b` and committed before the
wording existed, and by the decisive reading being blind. **Independent evaluation**: done,
blind, both transcripts; it declined to name a winner and named the trade, which the owner had
already answered in #102 and #104. Its two unresolved costs are 39's instruction 1.
**Revert**: `git revert f75aceb6` and restore the `sys_prompt/CLAUDE.md` paragraph it replaced.

## DEC-050 — the harm case runs, and no wording ships for what it found (iter 39, conf 85)

The shipped `# Completeness` line gets its adversarial reading; it is not refuted, and its trap
never fired because both arms found the warrant in the project's own docs. The new cost —
what a session escalates, it cements — is measured, and **no wording ships for it**:
`sys_prompt/CLAUDE.md` carries the claim and the hypothesis instead. **Alternatives**: ship an
invented clause (*leave nothing behind that a fix you named would have to undo*) on this round's
positive reading alone, which is the pattern 38 was critiqued for and which the contract now
forbids; or delete the line on the blind reader's preference for the untreated **files**, which
is an artefact of the task sentence that blocked the fix. **Framing bias**: the round chose the
probe that would exonerate a line the previous round shipped, and a round measuring its
predecessor's line has an interest in the line surviving — mitigated by the outcomes being
committed first and by the decisive reading being blind, not removed. **Independent
evaluation**: done, blind, both transcripts; it volunteered the cementing cost and read the
noticing difference as attention rather than instruction. **Revert**: nothing to revert; the
record is `git revert` of this round's `sys_prompt/CLAUDE.md` commit.

## DEC-051 — `sys_prompt/CLAUDE.md` is bounded by its shape, not by a size (iter 40, conf 90)

One paragraph per line the prompt stack carries, one ledger row per dead wording, run narrative
in the commit; applied in the same commit, 12,147 → 9,265 tokens. **Alternatives**: leave the
file and spend the cleanup round on a probe, which is what four cleanup rounds before it did
while the file doubled; set a token ceiling on the file, which is the human-set size limit the
objective rules out; move the narrative to `notes/`, which is relocation and therefore growth.
**Framing bias**: the round chose a target it could both diagnose and fix inside one iteration,
and a structural finding flatters a round that has no measurement to report — mitigated by the
growth curve, the attachment and the token delta all being measured rather than argued, not
removed. **Independent evaluation**: none; the deletions are checkable by grep and the commit
names every check that was run. **Revert**: `git revert 98aff4c5`.
