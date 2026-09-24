# Decision journal — writing-for-agents loop3

Only decisions still open to re-argument live here, and only the half of each that
`sys_prompt/CLAUDE.md` does not carry: what else was on the table, the framing bias,
whether anyone independent has looked, and the revert. The claim, the hypothesis and
the retirement condition are that file's, stated once; a second copy here would be
two wordings with nothing saying which governs. Everything discharged is in the
commit messages. Standing framing bias on every
decision here: each fixture was written from the shape of the line its round
meant to test.

**Closed**, their content in the commit messages and in `sys_prompt/CLAUDE.md`:
DEC-001–031 (rounds 1–23); 035 (superseded by 036); 036 (upheld at 32 in a second
genre); 038; 039 and 040/041 (restated as contract clauses); 042 and 043 (decided at
33). Independent evaluation: not started for all. DEC-030's stated reason is withdrawn —
the fixture's own pre-existing option carried the mismatch it read as a cost of the line
— and its wording shipped at round 23.

## DEC-032 / 033 / 034 / 037 — the four shipped-or-deleted lines still open to re-argument

Each one's claim, hypothesis and retirement condition are in `sys_prompt/CLAUDE.md`; the
measurement is in its commit. What is here is only what that file does not carry.

- **032, keep the self-consequence bullet** (conf 65). Alternative: delete it on the
  over-reach. Bias: the confidence was set against a contrast 25 showed does not exist.
  Independent evaluation: the blind comparison preferred the *untreated* arm, so the
  decision to keep is unevaluated. Revert `d98c5753`.
- **033, cut the duplicated rationale, not the directive** (conf 75). Alternatives: cut
  the directive; cut neither. Bias: the probe reused the case the bullet shipped on,
  whose `CLAUDE.md` already requires every option documented, so the confidence is in the
  cut being cheap, not in the bullet being load-bearing. Independent evaluation: both
  arms delivered the same artifact, so nothing was compared. Revert `9504b5dc`.
- **034, delete `pre_output.record`'s NEVER-uncertainties rule** (conf 75). Alternatives:
  keep it and cut one of the two wordings agreeing with it; reword it to carry the escape
  branch. Bias: the treated arm ran two draws to the untreated arm's one, and the blind
  reader's preference rested on three statements written before that arm called the tool.
  Independent evaluation: done, and it disagreed; the deletion was taken over it on the
  tool-call indices. Revert `291d3c55`.
- **037, keep `# Writing for other agents`** (conf 70). Alternatives: delete it on the
  volume gap; call it saturated. Bias: the arms diverged on depth as well as prompt, so
  volume and investigation moved together and neither was held fixed. Independent
  evaluation: the blind reader set the questions, and was not asked which arm was better
  placed. Revert: n/a.

## DEC-044 — fix-instead-of-note is decided and not shipped (iter 34, conf 80)

The finding and what would ship a wording here are in `sys_prompt/CLAUDE.md`.
**Alternatives**: ship it on the adversarial null alone, which prices a harm that did not
occur and no benefit that did; hand it forward, which the contract forbids for a line a
second round has measured; widen it to the placement half of the owner's answer, which
would be a different sentence and a different round. **Framing bias**: the round wrote
both fixtures and chose a hazard whose removal is one argument long, which is the easiest
possible case for the bullet and the hardest possible case for a difference — a harder
removal might separate the arms, and nothing here measured one. **Independent
evaluation**: done, and it went further than asked — one blind reader holding both trees
and both sessions of the benefit probe, told neither what was under test nor which arm
was which, found no attributable difference, checked 16 and 27 added sentences against
the running code and found none false in either tree, and traced the prose gap to a
review subagent one arm ran. **Revert**: n/a, no prompt edit.

## DEC-045 — the branch's edits do not reach any session here (iter 34, conf 95)

Recorded rather than acted on. `/repos/claude-config` is what `scripts/claude.sh` loads
and it still carries `Omit by default`, `Claim less` and the docs order; nothing measured
in 34 rounds is live. **Alternatives**: merge it, which this worktree is forbidden to do
and the owner has not asked for; keep measuring and say nothing, which leaves every round
after this one free to cite a real session as evidence about a line the session never
had. **Framing bias**: the round found this while checking its own critique and may be
over-weighting it against the round's measured result. **Independent evaluation**: not
started; the fact is a grep and needs none. Asked on the channel whether the merge is
wanted; unanswered at close. **Revert**: n/a.
