<request added="loop3" from="user" commit="817f51bd">

# Loop 3 — reverse gate on "Writing for other agents"

Deliverable: `# Writing for other agents` and the `[record]` marker in `sys_prompt/alan-default-next.md` at HEAD, presumed right.

Loops 1–2 (tag `writing-for-agents-backup3`, 32 rounds) ran the opposite gate — to delete, prove no harm — and cut one line in 32 rounds; failures in `.ralph/agent/memories.md` at that tag. Two govern here. The first thing asked at round 18 — per case, the best answer, what went wrong in the recorded outputs inside and outside the rubric with severity, and the alternatives no session took — went into 150 KB of `prompt-tests/step1/` and never into a `reference-solution.md`; rounds 26–32 changed no reference. And `.ralph/agent/*` reached ~320 KB, budgets met by relocation.

## Round 1–2, before any arm

Write that step-1 answer for every case to be run **into its `reference-solution.md`**, from the stored sessions' thinking blocks (`.claude/skills/prompt-tests/SKILL.md`, grader rule). A reference lacking any of the three is unfinished; no arm reads against it.

## Gate

- **To add or reword a line, adversarially show on the instruments below that it does not harm and buys behaviour absent without it.** A round's default outcome is no change.
- **To cut a line**, one absence arm that is not worse suffices.
- Presence/absence arms, ≥8 sessions each, decision rule and power written before the arm runs; smaller is a lead. Quote transcripts, not tables about them.
- First candidate: "Claim less" recommends the hint form; `notes/workers-bullet-hint-in-fact-position.md` found it harmful.

## Instruments — grade the maintainer's move

Real docs grow by successors appending cases; nobody orders a cut. Grade: (1) net size not larger; (2) maintainer probe — a cold `claude -p` reader given only the rewritten doc and one real miss, asked what it *would* check next upgrade; it runs nothing — no checkout, no decompile; (3) per-element presence/absence probe, ties to omission. No arm models detecting a miss nobody has noticed; say so wherever a result is quoted.

Two sibling cases in `prompt-tests/general/` (foci change = new case; payments-relay cases stay as regression):

- `upgrade-runbook-compress`: fixture `.claude/skills/update-claude-code/SKILL.md` at HEAD; the task orders the cut. Every known real miss is written into HEAD, so the probe asks whether the surviving framing still reaches what the cut removed.
- `upgrade-runbook-incident`: fixture = the same file at `a01fc12b` plus the env-context incident (`0ca74891`: cc ships its own env block, five bullets duplicated, the runbook missed it). `task.md` carries the user's preference verbatim — *the doc failed to cover all cases, but the solution is not to add all cases in*; `task-no-preference.md` omits it. Held-out, absent from that version, one class (a check whose success looks like failure; a step finding only what the inventory names): `be7ccee2`, `c03e155c`, `e6c134cf`, `a5dbef48`.

References cite commits, asserting nothing history does not show. The fixture names `sys_prompt/alan-default-next.md`; keep the deliverable's text out of fixture and probe. Existing cases: relax each rubric to *fail only where worse than omission*; drop names of rules no longer in the prompt.

## Loop hygiene

- Memories are not injected: open each round with `ralph tools memory prime`.
- `.ralph/agent/*` ≤ 6000 tokens by `agent-tools count-tokens`, net not larger from round 3; moving text elsewhere is growth. Record cuts before additions.
- A task line states its ground, never its expected finding. A gate names the finding it guards or is not a gate.
- One prompt candidate per round, decided that round. Nothing queued.
- Every fifth round: cleanup only.

</request>
