# Decision journal — writing-for-agents loop3

Only decisions still open to re-argument live here, and only the half of each that
`sys_prompt/CLAUDE.md` does not carry: what else was on the table, the framing bias,
whether anyone independent has looked, and the revert. Everything discharged is in the
commit messages. Standing framing bias on every decision here: each fixture was written
from the shape of the line its round meant to test.

**Closed**: DEC-001–031, 035–036, 038–044, 046. Their content is in the commit messages
and in `sys_prompt/CLAUDE.md`; none has an independent evaluation.

## DEC-032 / 033 / 034 / 037 — four shipped-or-deleted lines still open to re-argument

Here only what `sys_prompt/CLAUDE.md` and the commits do not carry.

- **032, keep the self-consequence bullet** (65). Alternative: delete it on the over-reach.
  The blind comparison preferred the *untreated* arm, so the keep is unevaluated. Revert
  `d98c5753`.
- **033, cut the duplicated rationale, not the directive** (75). Both arms delivered the same
  artifact, so nothing was compared; the confidence is in the cut being cheap, not in the
  bullet being load-bearing. Revert `9504b5dc`.
- **034, delete `pre_output.record`'s NEVER-uncertainties rule** (75). Independent evaluation
  disagreed and was overridden on the tool-call indices; the treated arm ran two draws to the
  other's one. Revert `291d3c55`.
- **037, keep `# Writing for other agents`** (70). The arms diverged on depth as well as
  prompt, so volume and investigation moved together. Revert: n/a.

## DEC-045 — the branch's edits do not reach any session here (iter 34, conf 95)

Recorded rather than acted on. `/repos/claude-config` is what `scripts/claude.sh` loads
and it still carries `Omit by default`, `Claim less` and the docs order; nothing measured
in 34 rounds is live. **Alternatives**: merge it, which this worktree is forbidden to do
and the owner has not asked for; keep measuring and say nothing, which leaves every round
after this one free to cite a real session as evidence about a line the session never
had. **Framing bias**: the round found this while checking its own critique and may be
over-weighting it against the round's measured result. **Independent evaluation**: not
started; the fact is a grep and needs none. **Answered 2026-09-25**: "i may choose to merge
myself, but you shoudl not do that." So the branch stays unmerged by the loop, the alternative
"merge it" is closed, and a round's product remains an edit to `alan-default-next.md` that no
session here runs — which is a fact every round states rather than a defect it repairs.
**Revert**: n/a.

## DEC-047 — the scope wording is decided and not shipped (iter 36, conf 80)

Measurement in `997a5c02`; claim and hypothesis in `sys_prompt/CLAUDE.md`. **Alternatives**:
ship it on the blind reader's narrow preference for the treated tree, which prices a repair
the pre-registration did not ask for and ignores a false sentence it did; hand it forward a
third time, which the contract forbids. **Framing bias**: the round wrote the wording it
judged, which is why the ship condition was fixed before the runs; it was not met. The
fixture is the one 35 elicited the failure on, so it says nothing about trees that do not.
**Independent evaluation**: done, blind, both trees; the two decisive facts were re-verified
by hand. **Revert**: `git checkout 3c5bec5e -- sys_prompt/CLAUDE.md`.

## DEC-048 — what "public-ready on your parts" covered, and what it left standing (iter 37, conf 85)

The owner's #96 asked for `staging`'s public-ready pass on this branch's additions. Taken as:
repair claims this branch falsified, sweep links and citers, change nothing else.
**Alternatives**: read it as the full spec — a README section for the loop's own ideas, which
asserts an idea the loop has not shipped; or move `PROMPT.md` out of the root the way
`staging` moved the two stray analyses, which breaks `/workspace/ralph/build.yml:17`.
**Reverted inside the round**: rows indexing `PROMPT.md` and `.ralph/` in the root
`CLAUDE.md`. #98 — *"ralph loop files will be intentionally kept in git history, but a commit
will remove them before merge"* — makes those rows two lines a later commit must also remove,
and nothing reads them: the scratchpad and `PROMPT.md` are injected, not looked up. That is
the ratchet this objective names, added by the round studying it. **Framing bias**: the round
chose the reading it could finish inside a merge-only instruction. **Independent evaluation**:
not started. **Revert**: `git revert e8589613` takes the README repairs with it.
