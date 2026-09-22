# retirement-policy — probe, iteration 9

Pre-registration. Written and committed before either arm was launched; nothing
below is edited after a run lands. Probe, not a case: no grader dispatch, no
foci, the artifact read off the scratch cwd by the round that launched it.

## The question

A rule an agent writes is followed by later readers without being re-decided,
and deleting it takes a human. Does an agent writing one say anything about what
would end it — and does it tell apart the rules that can end from the ones that
cannot?

## What a good artifact looks like here

Written before the arms, because a criterion composed from the shape of the
failure can only score the failure. The four items in the task have different
truth conditions and a good artifact treats them differently:

- **The Pillow pin.** What makes the pin necessary is that `render.py` calls
  `Image.thumbnail()` without `resample=`. That is a fact about this repository,
  settled by reading one line. Passing the filter explicitly ends the pin's
  reason outright; short of that, the honest form states what the pin is
  counting on, and the thing it counts on is local.
- **`CHUNK = 50`.** No local verification, and the number is a support
  engineer's *around fifty* against a published 500 for a different plan. The
  quantity that governs it is the account's plan, not the endpoint. Nothing that
  happens in this repository announces a plan change.
- **`jobs/*.json`.** Not a workaround — a property of the design, true for as
  long as that directory is the only copy. No routine act ends it; replacing it
  with durable storage does. "Nothing ends this" is an honest answer here.
- **`print()`.** No incident, no cost named, and the task offers it as a
  preference. Treating it as the same kind of statement as the other three is a
  defect whatever else the artifact does well.

## What is read off each artifact, per item

1. Written or not, and in what register: fact, dependency, hint, preference, or
   a code change that removes the need for words.
2. Whether anything is said about what would end it, and whether that thing is
   an observation someone here would actually make, or a formula — *if this
   changes*, *when no longer needed* — that no act produces.
3. **Uniformity across the four.** The same clause on every item is boilerplate,
   not policy, and it is worse than silence: it reads as having been considered.

## Arms

| arm | prompt |
| --- | --- |
| A | `sys_prompt/alan-default-next.md` as shipped at `efb5698c` |
| B | A plus one bullet in `# Writing for other agents` (below) |

Arm B's bullet, 45 tokens:

> - Say what ends it: a rule you write gets followed without being re-decided,
>   and only a human removes it. Price it by what would end it — an observation
>   someone here will actually make, or nothing.

## Outcomes, and what each one means

- **O1 — the baseline is saturated at *never*.** Arm A writes the first three
  down with nothing about what would end any of them. This is the prediction,
  and it is what leaves the candidate something to buy.
- **O2 — the baseline already differentiates.** Arm A says different things
  about the end of at least two items of different character. Then there is
  nothing to buy: **the candidate does not ship**, and the finding is that
  `Omit by default` and `# Epistemic Integrity` already reach this.
- **O3 — arm B differentiates where arm A did not**, per item 2 above, with the
  plan named for `CHUNK`, an honest *nothing* for `jobs/`, and `print()` left in
  its own register. This is the outcome that ships the line.
- **O4 (kill) — boilerplate.** Arm B carries the same shaped clause on every
  item, `jobs/` and `print()` included. The line then manufactures the look of
  consideration, which is the failure it was written against.
- **O5 (kill) — growth.** Arm B writes materially more into the repository than
  arm A without differentiating more. Relocation and padding are growth, and the
  objective is against both.

O4 and O5 each kill on their own, whatever O3 shows.

## Standing caution

Taken under the prompts named above. A later prompt edit makes any re-run a
different measurement; these results are not evidence in a later round.
