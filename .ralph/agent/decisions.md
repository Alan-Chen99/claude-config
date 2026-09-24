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
33); 044 (decided at 34, and its wording's successor decided at 35). Independent
evaluation: not started for all. DEC-030's stated reason is withdrawn — the fixture's own
pre-existing option carried the mismatch it read as a cost of the line — and its wording
shipped at round 23.

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

## DEC-045 — the branch's edits do not reach any session here (iter 34, conf 95)

Recorded rather than acted on. `/repos/claude-config` is what `scripts/claude.sh` loads
and it still carries `Omit by default`, `Claim less` and the docs order; nothing measured
in 34 rounds is live. **Alternatives**: merge it, which this worktree is forbidden to do
and the owner has not asked for; keep measuring and say nothing, which leaves every round
after this one free to cite a real session as evidence about a line the session never
had. **Framing bias**: the round found this while checking its own critique and may be
over-weighting it against the round's measured result. **Independent evaluation**: not
started; the fact is a grep and needs none. The owner acknowledged the provenance point
on the channel; whether the merge is wanted is unanswered at close. **Revert**: n/a.

## DEC-046 — the research candidate is not written, and scope replaces volume (iter 35, conf 85)

The measurement is in `4291d5b4` and the claim in `sys_prompt/CLAUDE.md`. **Alternatives**:
write it anyway on the specimen's evidence, which prices a benefit two legs produced
unprompted; hand it forward a second time, which the contract forbids; widen it to cover the
scope finding, which is a different sentence and iteration 36's. **Framing bias**: the fixture
was built to make *checking* one command and *fixing* one character, which is the easiest
possible case for the behaviour the candidate asks for and therefore the hardest case for the
candidate to earn anything — a costlier check might separate the legs and nothing here
measured one. The pre-registered outcome set assumed some leg would write a note about the
exposure; none did, so that set is withdrawn rather than honoured, and the scope finding is
an unpre-registered observation carried forward as a candidate, not as a result.
**Independent evaluation**: done and it went against the round's own reading — one blind
reader holding three trees and three sessions, told neither what was under test nor which leg
was which, answered "no attributable difference" and preferred the leg that generalised least
on grounds the round had not named (nothing false against its own tree). **Revert**: n/a, no
prompt edit; the three compressed paragraphs in `sys_prompt/CLAUDE.md` revert with
`git checkout 15b6682d -- sys_prompt/CLAUDE.md`.
