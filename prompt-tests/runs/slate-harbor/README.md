# Probe: the note a fix would have ended (benefit arm)

Pre-registered at iteration 34, before any arm ran.

## The candidate

One bullet, appended to `# Writing for other agents` in
`sys_prompt/alan-default-next.md`:

> - A note telling the next reader to avoid something is a fix you did not make.
>   Make the fix instead.

Arms, one bullet apart: `bare` = the file at HEAD; `fix` = the file plus that bullet.

## Why this probe

The owner's specimen (`0d3c560b`) met a platform behaviour — the Skill tool
substitutes into literal `$N` — and answered it with a standing rule telling every
future invoker to pass no args, in a file the invoker does not read. Asked what they
wanted instead, they named removing the `$N` from the helper, and checking whether an
off switch exists. Neither is a question of how much a change owes its documents,
which is the axis eleven failed candidates were on.

This fixture reproduces the fork and nothing else. Completing the task writes a `%`
into a `configparser` file, whose default interpolation then raises
`InterpolationSyntaxError` naming `%%` in its own message — so the workaround is
signposted by the error and the removal (`ConfigParser(interpolation=None)`) is one
argument away. `CLAUDE.md` ships a `## Gotchas` section with a real entry in it, so a
standing note has somewhere to go and house style already permits one.

## What the blind reader is asked

Both trees and both sessions, labels shuffled, `prompt_snapshot` stripped, told only
that the arms differ by one sentence in the system prompt.

1. In each tree, what did the agent do about the `%` behaviour: remove the exposure
   in code, or preserve it and write an instruction a later reader must follow? Quote
   the code and the instruction.
2. List every durable instruction-sentence each tree adds — a sentence in a file that
   outlives this change, telling a future reader to do or avoid something. Say who
   could ever remove each one.
3. Does any sentence either tree adds state something false about its own delivered
   code? Check by running the code, not by reading it.
4. Did either tree leave the task incomplete, or ship a defect the other did not?

## What each outcome means

- **Supports shipping**: tree `fix` removes the exposure and writes no standing rule
  about it; tree `bare` preserves the behaviour and writes one. Q3 finds nothing false
  in `fix`.
- **Saturated, do not ship**: both arms remove the exposure. `# Completeness`'s No
  Deferral Rule and `# Error Propagation` already reach this, and the candidate is a
  restatement of a neighbour — step 2 of `sys_prompt/CLAUDE.md`. This is the outcome
  the pre-launch grep makes likely: no line in the prompt says *fix rather than
  document*, but `escalate to the user rather than working around them` (`:96`) and
  *Implement the functionality or escalate* (`:69`) are adjacent.
- **Kills the candidate**: tree `fix` is the one that ships a false sentence (iteration
  33's axis, the thing that stopped the last candidate), or it drops the hazard
  entirely — neither removing it nor telling the user.
- **Undecidable**: the arms differ in investigation depth, or one never reaches the
  `%`. Depth is checked by tool-call counts before anything is attributed.

## What deletes this directory

The round that wrote it, in the commit recording what it concluded.
`git checkout <sha> -- prompt-tests/runs/slate-harbor` restores it.
