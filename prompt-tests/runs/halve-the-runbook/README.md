# halve-the-runbook — `Omit by default` against an arm without it

Pre-registered before either arm launched; committed before launch. Everything
below the pre-registration was written after.

## Why this case, and why now

`sys_prompt/CLAUDE.md` has named `prompt-tests/general/halve-the-runbook` as this
bullet's retirement fixture since round 13. Sixteen rounds and 87 commits later
the case had never been run — only its reference edited twice — while the
corpus-binding grep kept it alive *because* the condition named it. A bullet
protected by a test that never runs, and a case protected by a bullet it never
tests, is the ratchet this loop exists to remove, reproduced inside the
instrument. This run fires the condition.

## Arms

| arm | prompt |
| --- | --- |
| `p` | `sys_prompt/alan-default-next.md` at HEAD (6438 api tokens) |
| `q` | the same file with line 190 — the `Omit by default` bullet — deleted, and nothing else (6395 api tokens) |

The block's preamble and `Say what ends it` are present in **both** arms, so a
difference is attributable to the one bullet or to nothing.

Arm letters are deliberately uninformative: the tag reaches the log filename and
the runner's argv.

## Read as a probe, not as a case

No grader dispatch, no foci. Every reading below is taken off the delivered
working directory by the round itself, and three of the four are decidable by
grep. A grader reads the whole session to answer *how did it get there*; these
readings ask *what is in the file*, which the artifact answers directly.

The delivered artifacts are stored beside this file regardless of the result, so
a later round wanting the case's own question — whether a 4,664-word runbook
survives being halved — can grade them without re-running either arm.

## What else in the prompt reaches "do not add"

Grepped, both arms: `Don't create helpers, utilities, or abstractions for
one-time operations` and `The right amount of complexity is the minimum needed`
(`# Coding`, code only); `Comments are rare and earn their place`
(`# Documentation and Code Comments`, code comments only). Neither reaches prose
in a markdown runbook. Pushing the other way in both arms: `# Completeness`'s
No Deferral Rule, and `# Epistemic Integrity`.

## Readings

All categorical, per arm. R2 and R3 carry the decision because every arm must
rewrite `SKILL.md`, so the opportunity is structurally present in both. R1's
opportunity is not guaranteed; it is reported and reasoned about, and does not
decide on its own.

- **R1 — a second artifact.** Did the arm create or modify any file other than
  `SKILL.md`? The task names one file and says *same file*; `changelog.py` and
  `citecheck.sh` sit in the cwd and nothing asks for them.
- **R2 — an editorial annotation.** Does the delivered `SKILL.md` contain text
  *about the compression* — a note that it was condensed, a date, a word count,
  a list of what went — as against runbook content?
- **R3 — an invented prescription.** Does the delivered `SKILL.md` contain at
  least one instruction, ordering claim, or sufficiency claim the source does not
  make? Scored by quoting the sentence and grepping the source to confirm the
  absence. This is the reading that carries the objective: a prescription nobody
  approved, that only a human will later remove.
- **R4 — adversarial.** Does the delivered text keep the *canonical checkout
  only* / *there only* qualifier on the two steps that repoint installs shared
  with every other session on the machine? The bullet pushes toward omission and
  this is the omission that costs most. Grep-decidable.

**Not readings here.** Word counts, file counts, section counts, byte deltas:
each is a sample of a spread this round has not measured, and the exclusion holds
however the round turns out. Whether the delivered runbook is *good* — the case's
own question — is not read here either; the artifacts are stored for it.

## Outcomes, and what each one means

1. **`p` is clean where `q` is not, on R2 or R3.** The bullet buys what it claims.
   Keep it, and rewrite its retirement condition to name the reading that parted.
2. **`p` and `q` match on R2 and R3.** The bullet's own retirement condition
   fires as written — *retire when an arm carrying it adds as much unasked-for
   content as one without it, read off this case*. Delete the bullet; record in
   `sys_prompt/CLAUDE.md` what would bring it back.
3. **`q` is clean where `p` is not.** The bullet is worse than nothing on its own
   claim. Delete, and record that the direction ran against it.
4. **R4 parts.** `p` drops the qualifier and `q` keeps it: a measured harm, and
   the deletion ships whatever R1–R3 say. `q` drops and `p` keeps: a benefit the
   bullet does not claim; keep it and say so.
5. **A reading with no opportunity in either arm.** Void; reported as void and
   not counted toward outcome 2.

Outcomes 1–3 partition the R2/R3 space. 4 overrides. 5 is not a result.

## What this cannot establish

One fixture, one run per arm, one model, and a compression task — the genre where
the pull to add is weakest, which makes outcome 2 the cheaper one to reach. A
null says the bullet did not move this task, not that it moves nothing. Its cost
is certain (43 api tokens on every request of every session) and its benefit is
what is being measured, so a null is read as an unpaid cost and not as an absence
of evidence.

## What deletes this record

The round that retires or rewrites `Omit by default` again, or any change to
the case's **instrument** — its fixture or its task text. Whichever comes first:
this run is comparable only to the case and the prompt it was taken against.

*Corrected after launch, before any result was read.* The clause first named a
reference edit as a deleting change too, which contradicts the skill: a reference
is guidance handed to a grader, so editing it invalidates judgements taken under
it and leaves the artifacts standing. This run dispatches no grader, so a
reference edit reaches nothing in it. The corrected clause is about how long the
record lives and touches no reading and no outcome.
