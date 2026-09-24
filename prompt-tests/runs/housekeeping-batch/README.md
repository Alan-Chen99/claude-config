# housekeeping-batch (probe)

## What is under test

`sys_prompt/alan-default-next.md:15`, third clause:

> After making a new file or making edits, check if project CLAUDE.md needs an
> update.

Arm **a** = the prompt at HEAD. Arm **b** = the same prompt with that clause
deleted, leaving `Always update docs when you modify code or system state. Search
for references across the entire codebase.`

## Why this clause

It is a restatement of the sentence before it, narrowed to one file and widened in
trigger: the first sentence fires on *docs that a change made wrong*, which is
checkable against the change; the third fires on *an edit happened*, which is not.
`sys_prompt/CLAUDE.md` has no entry for `# Doing tasks`, so the widening has never
been justified or measured, and `output-styles/alan-default-next.md:70` still
carries the unwidened wording it was forked from.

Three real sessions show the widened trigger firing on an edit-only change:
`27707d1f` ("the reference to sys_prompt/CLAUDE.md still looks accurate, so no
change is needed there"), `cb2b7ffb` ("double-check the repo-root CLAUDE.md
doesn't need updates since it already describes the prompt-tests skill
generically") — both a turn spent on an empty check — and `9c6375c1`, where the
check escalated rather than closing: "The root CLAUDE.md notes/ row is generic
enough that it doesn't need updating for this new file. I'm checking whether
there's a notes/CLAUDE.md index file that should list it."

## The task's three opportunities, differing in character

The task mentions documentation nowhere. Its three items differ in what they do to
the fixture's docs:

1. **Docs become wrong.** TTL 900 → 60 falsifies `feeds/README.md`, which states
   900 seconds and argues for it.
2. **An index becomes stale.** A new `feeds/retry.py` is absent from
   `feeds/CLAUDE.md`'s Files table.
3. **Nothing documented becomes wrong.** The `render/table.py` fix adds no file and
   falsifies no sentence; `render/CLAUDE.md` and the root `CLAUDE.md` stay true.

## Pre-registration

Committed before the arms ran; see the commit that adds this file.

- **Outcome 1 — ship the deletion.** Both arms repair (1) and (2); arm a also
  writes durable text for (3) — touches `render/CLAUDE.md`, the root `CLAUDE.md`,
  or creates a doc — and arm b does not.
- **Outcome 2 — saturated, still delete.** Both arms behave alike on all three,
  (3) included with no doc touched. The clause buys nothing the sentence before it
  does not; deletion is right and the growth in the live case is not attributable
  to this clause. Say so.
- **Outcome 3 — the candidate dies.** Arm b misses (1) or (2): drops the stale
  README, or leaves the index without the new row. The widening is then
  load-bearing and the clause stays, with this probe named as the reason.
- **Outcome 4 — inverted.** Arm b writes *more* durable text than arm a. Unlikely
  and uninterpretable at n=1; report as noise and do not ship.

Decisive reading is a blind reader given both trees and both sessions as A and B,
told neither the arm labels nor the clause.

## Deletion

Deleted by the round that wrote it, in the commit recording the result.
`git checkout <sha> -- prompt-tests/runs/housekeeping-batch` restores it.
