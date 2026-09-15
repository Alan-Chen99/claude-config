# Loop 3 — reverse gate on "Writing for other agents"

Deliverable: the `# Writing for other agents` section and the `[record]` marker in `sys_prompt/alan-default-next.md` at HEAD (`817f51bd`). That text is the baseline and is presumed right.

Loops 1–2 (tag `writing-for-agents-backup3`, 32 rounds) ran the opposite gate — to delete, prove no harm — and got: one prompt cut in 32 rounds; every design taken from a defect, none from what a good writer would have done that nobody did; instruments indexing clauses by name, never asking whether a sentence is true; `.ralph/agent/*` at ~320 KB, budgets met by relocation; arms at n=2 that could return nothing; gates that named no finding; task lines stating the expected finding; an evidence-backed cut refused on a self-made rule.

## Gate

- **To add or reword a line, adversarially show on the instruments below that it does not harm and buys behaviour absent without it.** A round's default outcome is no change.
- **To cut a line**, one absence arm that is not worse suffices.
- Presence/absence arms, ≥8 sessions per arm, decision rule and power written before the arm runs. Smaller is a lead, not a result. Quote transcripts, not tables written about them.
- First candidate: "Claim less" recommends the hint form, which `notes/workers-bullet-hint-in-fact-position.md` and the WORKERS probe found harmful. Test a reword; do not assume it.

## Instruments — grade the maintainer's move, not the doc's coverage

Real docs grow by successors appending cases; nobody orders a cut. Grade what a maintainer does to the doc:

1. Net size not larger.
2. Maintainer probe: a cold `claude -p` reader given only the rewritten doc and a real unlisted miss of the same class, asked what it *would* check next upgrade. It runs nothing — no checkout, no decompile.
3. Per-element presence/absence probe; ties go to omission.

Two sibling cases in `prompt-tests/general/` (read `.claude/skills/prompt-tests/SKILL.md`; a foci change is a new case; the payments-relay cases stay as regression):

- `upgrade-runbook-compress`: fixture `.claude/skills/update-claude-code/SKILL.md` at HEAD; the task orders the cut. Probe: two listed misses (retention), one unlisted (generalisation).
- `upgrade-runbook-incident`: fixture = the same file at `a01fc12b` plus the env-context incident (`0ca74891`: cc ships its own env block, five bullets duplicated, the runbook did not catch it). `task.md` carries the user's preference verbatim — *the doc failed to cover all cases, but the solution is not to add all cases in*; `task-no-preference.md` omits it. Held-out misses, absent from that version, one class (a check whose success looks like its failure; a step finding only what the inventory already names): `be7ccee2`, `c03e155c`, `e6c134cf`, `a5dbef48`.

References cite commits and assert nothing history does not show. The fixture names `sys_prompt/alan-default-next.md`: keep the deliverable's text out of fixture and probe.

Existing cases: relax each rubric to *fail only where the output is worse than omission*; remove references to rule names no longer in the prompt.

## Loop hygiene

- Memories are not injected (`inject: manual`): open each round with `ralph tools memory prime` and `.ralph/agent/*`.
- `.ralph/agent/*` total ≤ 6000 tokens by `agent-tools count-tokens`, net not larger from round 3; moving text elsewhere is growth. Record cuts before additions.
- A task line states its ground, never its expected finding. A gate names the finding it guards or does not exist.
- For every session ask what a good answer would have done that nobody did.
- One prompt candidate per round, decided that round: shipped, refuted or dropped. Nothing queued.
- Every fifth round is cleanup only.
- Commit trailer: `Claude-Session: 0bb263f7-bc63-4c52-8b38-6201d9388caa`.
