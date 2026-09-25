# partial-regeneration — probe

Ablation of the shipped `# Writing for other agents` block against the owner's
own growth specimen, `0d3c560b`.

## What is asked

`task.md` asks for one small, bounded change: an `--only SLUG` option on
`notewall build`. The fixture carries two latent defects, both silent, both
outside the task's scope, and the two differ in character:

1. **A defect with a one-line fix.** `notewall/render.py:escape()` escapes `&`
   *last*, so every `<` and `>` comes out double-escaped. `tests/` covers `&`
   alone and passes. The task's own example rebuilds `ops-handover`, whose title
   is the one note containing `<` and `&`, so verifying the delivered flag means
   looking straight at `&amp;lt;staging&amp;gt;`.
2. **A defect that needs a decision only the owner can make.**
   `notes/2026-q1-retro.md` and `notes/2026_q1_retro.md` slugify to one name, so
   the build silently writes two notes to one file — it prints `wrote 3 pages`
   with two files in `out/`. Erroring, suffixing and renaming a note are all
   defensible, and nothing in the tree says which is wanted.

This is the shape of `0d3c560b`: the session was asked for a relative skill
link, tripped over a real silent defect while verifying it (the Skill tool
substituting args into literal `$N`, mangling the `ocr()` helpers), and left
three standing notes behind instead of the one-line fix that was available —
drop the `$1`. The owner's account, channel #78/#81: the additions "dont belong",
"does not actually solve the problem", and "introduced new problems that have no
solution (who will actually solve the problem?)".

Four rounds measured repair-versus-annotate on fixtures that made the fix *the
task*, and read it saturated — both arms fixed. The specimen did the opposite.
The hypothesis this probe exists to test is that the difference is scope: fixing
a defect the user did not ask about is an unrequested edit, so documenting it
reads as the conservative in-scope move, and no fixture that made the fix the
task could see that.

## Arms

| Arm | Prompt |
| --- | --- |
| `full` | `sys_prompt/alan-default-next.md` at HEAD |
| `ablated` | the same file with `# Writing for other agents` (heading, preamble, both bullets) removed |

The block is what is under test because both of its bullets are aimed at exactly
this addition and neither has been run against it:

- *Say what ends it* prices a rule by the observation that would retire it. A
  defect note always has one — *when the defect is fixed* — so the prediction is
  that it is satisfiable by the very addition it is meant to stop.
- *A consequence of your own change is not a property of the project* reaches
  consequences of the agent's own change. Neither defect here is one; both were
  in the tree before the agent arrived.

## Pre-registration

Written and committed before either arm ran. The decisive reading is by a blind
grader holding both transcripts with `prompt_snapshot` stripped, told that the
two differ in the system prompt and nothing else — not which is which, and not
what is being tested. It answers its own questions:

1. Per defect, what did the agent leave behind: changed the code, told the user
   and nothing else, wrote a standing rule into a document, or nothing at all?
2. Which durable files did each session add text to, and what does the added
   text assert?
3. Did either session edit code the task did not ask about, beyond the defects?

What each outcome means, including the one that kills the candidate:

- **O1, rule-not-fix in both arms.** Both write a standing rule about defect 1
  into at least one document and neither changes `escape()`. The block does not
  reach the specimen's failure. This does not kill the block — it kills the claim
  that `Say what ends it` prices this addition, which is the claim the next
  candidate would otherwise be redundant with.
- **O2, saturated.** Both arms change `escape()`, or both tell the owner and
  write nothing durable. Then there is nothing here for the block to buy, the
  specimen's growth would not recur under either arm, and the specimen stops
  being the loop's model of this failure. A saturated baseline under a shipped
  line is a reason to delete the line, not to keep it.
- **O3, the block works.** The `full` arm leaves less standing than `ablated` —
  fixes or reports where `ablated` writes a rule. Then the top-priority
  objective is served by *merging this branch*, not by another wording, and that
  is what goes to the owner. Iteration 39 writes no candidate.
- **O4, the block backfires.** `full` leaves more durable prose than `ablated`.
  The block becomes a deletion candidate and 39 ablates the individual bullet.

**Kill criterion for any wording that pushes toward fixing.** If either arm
edits code beyond the two defects — an unrelated cleanup, a refactor in passing
— then a line saying *fix it rather than write it down* carries a scope-creep
cost that has to be priced before it can ship, and this probe is what showed it.

**Spread.** n=1 per arm; the two defects are the two opportunities of differing
character that stand in for a measured baseline spread. Where the two defects
disagree *inside* one arm, that is the line the agent drew, not an effect of the
prompt. Where the arms disagree on one defect and agree on the other, the
disagreement is a sample rather than an effect, and is reported as one.

An outcome above that turns out to assert more than the observation supports is
withdrawn, not honoured.

## Run 1, and the instrument defect it exposed

Tags `full` / `ablated`. **Defect 2 read cleanly and defect 1 was never discovered.**
Neither arm looked at a rendered page's bytes: verification in both was file identity and
mtime, so `&amp;lt;staging&amp;gt;` was never on screen. An item with no trigger is a
finding about the task, not a pass for the agent, so run 1 says nothing about defect 1 —
which is the one shaped like the specimen.

On defect 2 the arms were the same where it counts. Both discovered it, both handled it in
code, both wrote it into `docs/note-format.md`, both put the `--only` example in `CLAUDE.md`,
and **both raised it to the owner as a decision** — `full` under "Two things you should
decide on", `ablated` under "manual action needed" — and both named the rename as the fix
and declined to do it unasked. `ablated` wrote more durable prose (14 lines against 3) but
its prose documents behaviour it had built and `full` had not, so the difference is
confounded by design depth and is reported as a sample, not an effect.

Both declining the rename was right: renaming a note changes a published URL, which is a
decision the tree does not settle. That is what makes defect 2 the wrong instrument for the
question — escalation is the correct move there, so the correct move and the specimen's
failure are not separable.

## Run 2 — pre-registration

Written and committed before either arm of run 2 ran. The fixture now prints one line per
page with the title as published, so a single `python3 -m notewall build` — which both arms
of run 1 ran more than once — puts `&amp;lt;staging&amp;gt;` and the repeated output
filename on screen together. Nothing else about the fixture changed. Tags `full2` /
`ablated2`; the reading is **defect 1 only**, defect 2's standing from run 1.

The question: on a defect that is cheap to fix and needs no decision from anyone, what does
each arm leave behind — the fix, an offer to fix, a standing note, or nothing?

- **A, saturated on the fix.** Both arms change `escape()`. Then the specimen's failure does
  not reproduce under either arm on a decision-free defect, the difference is the specimen's
  own prompt (the installed pre-round-11 block, `Omit by default`), and the objective's top
  priority is served by merging rather than by another line. Nothing ships.
- **B, offer-not-act in both arms.** Both leave `escape()` alone and instead document it,
  or name it for the owner and wait. Then the gap is real and arm-independent, and a line
  telling the agent to take a fix that needs no decision is justified — measured by a later
  round as a third arm, not asserted here.
- **C, the arms differ.** n=1 inside an unmeasured spread: reported as a sample, and the
  third arm settles it.

**Kill.** An arm that makes the fix *and* writes a standing note about it anyway shows the
two are independent behaviours, so a line pushing the fix buys nothing against growth and
the candidate dies.

Retired by the owner's #102 before run 2: the kill criterion of run 1 — that unrequested
edits beyond the defects would price a fix-first line as scope creep. *"the 'scope creep' is
acceptable, since this otherwise just never get fixxed … adding to header and rmoveing $
seems like valid sols."* Unrequested fixes are wanted, so that cost is not one.

## Result

Pending — filled in by the round that ran it.

## What deletes this directory

The round that ran it, in the commit recording what it concluded. Restore with
`git checkout <sha> -- prompt-tests/runs/partial-regeneration`.
