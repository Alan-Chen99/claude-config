# Decision journal — writing-for-agents loop3

Only decisions still open to re-argument live here, and only the half of each that
`sys_prompt/CLAUDE.md` does not carry: what else was on the table, the framing bias,
whether anyone independent has looked, and the revert. Everything discharged is in the
commit messages.

**Closed**: DEC-001–031, 035–036, 038–044, 046. Content in the commit messages and in
`sys_prompt/CLAUDE.md`; none has an independent evaluation.

**Standing framing bias on every entry below**: rounds 33–36 each wrote its fixture from the
shape of the line it meant to test. The contract now requires the fixture to be built from a
named occurrence instead; 38 is the first round under it.

## DEC-032 / 033 / 034 / 037 — four shipped-or-deleted lines still open to re-argument

Reverts, with what leaves each unevaluated: `d98c5753` (032, keep the self-consequence bullet —
the blind comparison preferred the *untreated* arm); `9504b5dc` (033, cut the duplicated
rationale — both arms delivered the same artifact, so the confidence is in the cut being cheap);
`291d3c55` (034, delete `pre_output.record`'s NEVER-uncertainties rule — the independent
evaluation disagreed and was overridden, and the treated arm ran two draws to the other's one).
037, keep `# Writing for other agents`: no revert, and the arms diverged on depth as well as
prompt.

## DEC-045 — the branch's edits do not reach any session here (iter 34, conf 95)

`/repos/claude-config` is what `scripts/claude.sh` loads, and it still carries `Omit by
default`, `Claim less` and the docs order; nothing measured in 37 rounds is live. Answered
2026-09-25: *"i may choose to merge myself, but you shoudl not do that."* So a round's
product remains an edit to `alan-default-next.md` that no session here runs — a fact every
round states rather than a defect it repairs. It also means the owner's own specimen is
evidence about the **deleted** say-less bullets, not about the shipped block. **Revert**: n/a.

## DEC-047 — the scope wording is decided and not shipped (iter 36, conf 80)

Measurement in `997a5c02`, claim and hypothesis in `sys_prompt/CLAUDE.md`. The round wrote the
wording it judged and its own ship condition was not met. 38 retired the hand-forward clause
that kept it alive two further rounds, so it is not a live candidate. Independent evaluation:
done, blind, both trees. **Revert**: `git checkout 3c5bec5e -- sys_prompt/CLAUDE.md`.

## DEC-048 — what "public-ready on your parts" covered (iter 37, conf 85)

Taken as: repair claims this branch falsified, sweep citers, change nothing else, over the full
spec (a README section asserting an idea the loop has not shipped) or moving `PROMPT.md` out of
the root (breaks `/workspace/ralph/build.yml:17`). **Reverted inside the round** on #98: the
rows indexing `PROMPT.md` and `.ralph/` — two lines the pre-merge removal must also remove, and
nothing reads them. The round studying the ratchet performed it. **Framing bias**: it chose the
reading it could finish inside a merge-only instruction. **Independent evaluation**: not
started. **Revert**: `git revert e8589613` takes the README repairs with it.

## DEC-049 — one line ships under `# Completeness` (iter 38, conf 85)

Claim, cost and retirement condition in `sys_prompt/CLAUDE.md`; three pre-registrations and the
probe at `git checkout f75aceb6 -- prompt-tests/runs/partial-regeneration`. **Alternatives**: ship
nothing and hand the baseline to 39, the deferral this round deleted from the contract; put the
line in `# Writing for other agents`, where the ablation had just shown the block
arm-independent on this failure. **Framing bias**: the round wrote the wording it measured —
mitigated, not removed, by the fixture being built from `0d3c560b` and committed before the
wording existed, and by the decisive reading being blind. **Independent evaluation**: done,
blind, both transcripts; it declined to name a winner and named the trade, which the owner had
already answered in #102 and #104. Its two unresolved costs are instruction 1 for 39.
**Revert**: `git revert f75aceb6` and restore the `sys_prompt/CLAUDE.md` paragraph it replaced.
