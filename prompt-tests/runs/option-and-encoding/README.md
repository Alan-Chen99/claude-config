# Probe: the `# Doing tasks` docs order, on a tree that cannot hide its docs

Written before the runs. Iteration 28.

## What is under test

`sys_prompt/alan-default-next.md:15`, all three sentences:

> Always update docs when you modify code or system state. Search for references
> across the entire codebase. After making a new file or making edits, check if
> project CLAUDE.md needs an update.

- **arm a** — the prompt as shipped.
- **arm b** — line 15 deleted, nothing replacing it.

Two runs per arm. The candidate under trial is the **deletion** of the whole
line.

## Why this fixture

Iteration 27 measured the third sentence alone and could attribute nothing: a
blind reader grouped its four trees on whether the session's *first* listing
happened to show the `.md` files, a split cutting across the arms. Here the
auto-loaded `CLAUDE.md` names every doc file in its `## Files` table, so no arm
can miss them by accident and search breadth stops being the dominant variable.
The table is an index, not an order: nothing in the fixture says to update
anything.

The task names no document. It falsifies documented facts in three characters —
a prose claim with a worked `jq` command behind it (`README.md`), a structural
description and the design entry that argues for it (`docs/layout.md`), and a
switch table that is merely incomplete (`docs/commands.md`) — and it leaves two
headings that solicit prose nothing has falsified: `## Design Decisions` in
`docs/layout.md` and `## Conventions` in the auto-loaded `CLAUDE.md`, where an
addition becomes a standing rule only a human removes.

## The reading, fixed here

One blind reader, told the trees come from one task and differ in a system
prompt, told neither which arm is which nor what is being tested. Per tree:

1. Which statements in any `.md` does the delivered code make false?
2. Which sentences were added to any `.md` that the change did not falsify, and
   under which heading?

Call a tree **R** when no statement survives false, and **G** when at least one
sentence was added that the change did not falsify.

Where the two trees of one arm disagree on an axis, that axis is reported as
that arm's spread and no effect is read from it.

## Outcomes, and what each does to the candidate

1. **Both arms R.** The order is saturated where the auto-loaded `CLAUDE.md`
   names the docs; what produced the maintenance is the index, not the prompt.
   Candidate lives — delete line 15.
2. **arm a R, arm b not-R.** The order is load-bearing. **Candidate dies**, the
   line gets its first justification, and DEC-035's "untested" is replaced.
3. **Both arms G.** Growth in this genre is not caused by this order, and no
   wording of this line reaches the user's top priority. The growth paragraph
   iteration 27 left in `sys_prompt/CLAUDE.md` then describes no prompt line and
   is deleted from that file.
4. **arm a G, arm b not-G.** The order itself drives the growth. Strongest case
   for deleting it, and the one that answers the top priority directly.

Outcomes 1/2 and 3/4 are independent; both halves are read.

## What deletes this directory

The commit that records the result, per `.claude/skills/prompt-tests/SKILL.md`.
