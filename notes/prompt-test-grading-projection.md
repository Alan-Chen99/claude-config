# A grading key cannot see what an output paid off-key

Measured 2026-09-18 on one arm: `halve-the-runbook` `l3r7-presence` (session,
artifact and key from `/root/claude-config-work`, the worktree that ran it).
Two graders, one output.

**Arm A, the practice as it stood.** `runs/halve-the-runbook/grading-l3r7-presence.md`
there: the D1–D7 key applied blind to the source and the output, no session. A
per-class count, two high-severity defects, `Verdict: fail`.

**Arm B, the two-argument dispatch** now in `.claude/skills/prompt-tests/SKILL.md`:
the whole 1.1 MB session plus the arm's own system prompt, the key withheld until
a second phase. Judgements stored beside this file.

## What arm B found that arm A's frame cannot hold

- A report telling the user the remaining length gap "can only come from deleting
  content units" while ~90 words the agent had itself marked as free fat stayed
  in. A source-vs-output key grades the artifact; the false sentence was in the
  report.
- Seven full-file rewrites re-emitting ~120k tokens after the deciding arithmetic
  was already on screen (`@L53`).
- Path-prefix stripping that saved ~0 `wc -w` words and left three delivered steps
  unrunnable — a cost paid for nothing, invisible to a length-vs-fidelity trade.
- One item **undiscoverable from the agent's position**: the fixture held only
  `SKILL.md` and no repository, so the premise the whole compression rests on was
  uncheckable. A fact about the task, not a defect of the agent.

## What the key got wrong, and what it got right

The key caught 1 of arm B's 6 items cleanly, 1 partially, missed 4, and inverted
1. It also contributed 3 findings arm B had filed only as costs — so it earns its
place as guidance about what the caller cares about, which is the role it now has.

**The decisive defect is verdict-flipping.** D1's fifth row pairs a source note
(`extract` empties three directories first) with a breaking compression (an
instruction implying the tree is merged). The output dropped the note and implies
neither. Read down the Source column it is a high-severity D1 and the arm fails;
read the key's own "losing a fact is not a defect" clause and it is clean. Arm A
read it the second way and recorded "D1, all five rows" clean, never registering
that the row decides the headline both ways. Same key, same output, opposite
verdicts.

Runner-up: D6 at its stated sentence unit scores the source itself, and clearing
it per row means lengthening the file the task exists to shorten.

## What this does not support

One arm, one case, one model. It shows the projection loss is real and that the
dispatch finds key defects the practice missed; it does not measure how often, and
it is not evidence that a grader asked to criticise a key will decline when the
key is sound. Reading the key changed arm B's verdict on one item in the agent's
favour, which is the only evidence here that phase 2 is not ceremonial.
