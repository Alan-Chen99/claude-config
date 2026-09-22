# retirement-policy — `# Writing for other agents` tested whole

Pre-registered before either arm launched; committed before launch. Everything
below the pre-registration was written after.

## Arms

| arm | prompt |
| --- | --- |
| `r1` | `sys_prompt/alan-default-next.md` at HEAD (6438 api tokens) |
| `r2` | the same file with the whole `# Writing for other agents` block deleted — header, the read-cold sentence, both bullets (6240 api tokens) |

The block is two bullets and one framing sentence, so it is small enough to test
as a unit. Neither bullet has been run against an arm lacking it since round 9.
A difference here does not say which bullet produced it; that is the point of
outcome 4 below.

## What the fixture can and cannot answer

`Say what ends it` readings — its own retirement condition names this fixture by
shape ("items differ in whether they can end at all"), and the case supplies four
that do:

- **R1 per item (4 readings, categorical):** does the delivered text state what
  would end this item? Three of the four can end; row four (`no print()`,
  offered as *I'd rather*) cannot.
- **R2 (categorical):** is an end-condition attached to row four — the
  boilerplate failure `Say what ends it` is most likely to cause, and which
  `sys_prompt/CLAUDE.md` already names as its *sooner* retirement trigger.
- **R3 (categorical):** is row four in a different register from the other
  three, or filed under the same heading as the incidents?

`Omit by default` reading:

- **R4 (categorical, per subject):** does the delivered text cover a subject the
  task did not name? The task names four and says "put whatever a future agent
  needs into the repo", so the invitation is present in both arms and the
  reading is *which* arm accepted it.

**Not readings here.** Row one (the Pillow pin, whose stated cause is false and
checkable from the fixture) is reached by `# Epistemic Integrity` in both arms,
so what either arm does with it is not attributable to this block. Line counts,
file counts and byte deltas are excluded: each is a sample of a spread this round
has not measured, and the exclusion holds however the round turns out.
`Comments are rare and earn their place` sits in `# Documentation and Code
Comments` in both arms and reaches code comments specifically; a difference
confined to comments is not this block's.

## Outcomes, and what each one means

1. **r2 states end-conditions on fewer of the three endable items than r1, or r1
   avoids a boilerplate clause r2 attaches.** The block earns its 198 tokens.
   Ship no deletion; the next round isolates which bullet by running the two
   singly.
2. **r1 and r2 match on R1, R2, R3 and R4.** The block changed nothing a reader
   of the artifacts can see. Deletion becomes the leading candidate and ships if
   a blind comparison — one grader holding both artifacts, told only that the
   prompts differ and what the decisive criterion is — also finds no difference.
3. **r1 attaches an end-condition to row four and r2 does not.** The boilerplate
   failure. The block's own stated *sooner* retirement trigger fires; ship the
   deletion whatever R1 and R4 say.
4. **They differ on one reading and match on the other.** The reading they
   differ on names the surviving half — `Say what ends it` for R1/R2/R3,
   `Omit by default` for R4 — and only if the arm *carrying* the block did
   better on it. A difference favouring r2 is evidence against the block, not
   for it. Delete the half whose reading was null; keep the other and record
   what would end it.

These four partition the space: 1 and 3 decide against and for deletion on the
`Say what ends it` readings, 2 is the joint null, 4 is every split.

## What this cannot establish

One fixture, one run per arm, one model. A null says the block did not move this
task, not that it moves nothing. The block's cost is certain (198 api tokens on
every request of every session) and its benefit is what is being measured, so a
null is read as an unpaid cost rather than as an absence of evidence.

## What deletes this record

The round that retires or rewrites either bullet, or any edit to
`prompt-tests/general/retirement-policy/`. Whichever comes first: this run is
comparable only to the case and the prompt it was taken against.
