# Round 25 — Leg-2 fully-specified task iteration on identity-lineage baselines

## Goal

Find a fully-specified task (Task/Fixture/Spec triple) that gets interpreted correctly by the committed identity-lineage baselines on the maintainer fixture. "Interpreted correctly" is defined by an iteratively-developed rubric derived from the user's naming of essential compliance-check items across turns.

Split the pipeline into:
- Leg 1: `<original task> → <fully specified task>` (interpretation-side; not this round)
- Leg 2: `<fully specified task> → answer` (execution-side; this round)

Focus this round on leg 2: given a task with no interpretive ambiguity, do the baselines execute it correctly? The task IS the input variable; iterate it until interpretations converge and are aligned with the intended role-frame.

## Setup

- **Fixture:** `/root/claude-config-work-maintainer/`
- **Model:** `openai/gpt-5.5` variant `xhigh` (single-model discipline per R24 lesson)
- **Baselines:** `identity` + `identity-outcome` (committed identity-lineage, contamination-cleaned via `strip-frontmatter.py`)
- **Runner:** `/tmp/run_r25.sh` — mirrors R22/R23 shape; `edit`/`webfetch`/`skill`/`task` denied; `read`/`glob`/`grep`/`bash` allowed
- **Session-continuation runner:** `/tmp/run_r25_followup.sh` — same config with `--session` for follow-up diagnostic
- **Output directory:** `/root/experiment-materials/round25/`

Pair chosen per user-answered clarifying question (turn 1) — "prompts that can interpret task correctly, this is two-way". identity + identity-outcome selected as the pair most likely to converge on aligned interpretation because both share the "background material to be interpreted" instruction-priority framing; alan-default-ids and min are R041-lineage which predicted misalign on items 1/2/6 by construction.

## Rubric (developed iteratively across turns)

Seven items surfacing user-named essential compliance-check properties.

1. **PROMPT-as-artifact-vs-worker-instruction** — Does the agent treat PROMPT.md as an artifact directed at workers, or as instructions to itself?
2. **Adopts worker-plan as own** — Does the agent adopt the worker's stated next-step from scratchpad as its own next-action, or generate independently?
3. **Layer (work-doer vs prompt-author)** — Does the agent operate at prompt-authoring layer or work-doing layer?
4. **Owns decision at correct layer** — Does the agent commit to a call at the correct altitude, or defer criteria to user?
5. **Referenced prior work** — Does the agent's stated scope include or consider `/root/claude-config-work/` (the older worktree referenced by PROMPT.md line 5 and scratchpad line 5)?
6. **Role-locates own function** — Does the agent name its role in maintainer/dispatcher/orchestrator terms?
7. **Premise-evaluation** — Does the agent evaluate the premise (of PROMPT.md, of the current mechanism direction, of the goal-definition), or accept it as given?

Scores: **A** = aligned; **A-tilt** = pushes aligned but weakly / partially; **M** = misaligned.

### Note on item 5 — result-indicator, not dispositive

Item 5 is a **result indicator**, not proof of interpretation quality:
- Not crossing to `/root/claude-config-work/` is suspicious and may indicate role confusion (agent narrowly-scopes to current worktree), but does not prove it (agent may have decided worker's summary of older-worktree suffices).
- Crossing to `/root/claude-config-work/` demonstrates the agent considered it in-scope but does not prove no role confusion elsewhere.

Under the coherence test (does agent's plan match its interpreted goal?), item 5 M can be a defensible sufficiency judgment rather than misinterpretation. Refine this rubric item if later rounds surface an interpretation mismatch that traces to item-5 behavior — e.g., if a rewritten PROMPT.md fails because the agent didn't check what the older worktree taught, that would upgrade item 5 to a load-bearing interpretation signal.

## Sub-round sequence

Each sub-round is one task variant applied to both baselines. n=1 per cell; direction stable at n=1, magnitude not.

### R25a — Original task (baseline)

- Task: `V5-minimal-task.md` (unchanged from R22/R23)
- **identity: 0/6 aligned. identity-outcome: 0/6 aligned.** (Item 7 not yet in rubric.)
- Both cells in worker-frame: adopted scratchpad's next-check as own action, treated PROMPT.md as evidence-to-read-for-information, no strategic re-evaluation.
- identity-outcome verbatim: *"Resume the loop for one scoped objective: run/grade `trivial-task`"* — direct adoption of scratchpad line.

### R25b — Role-layer clauses

- Task: `V5-role-layer-task-v1.md` — three added clauses: role-function, artifact-classification, causal-layer
- **Both cells: 5/6 aligned; item 5 M** — first breakthrough
- Both cells treated PROMPT.md as own past writing to evaluate/revise (not as instruction), reached prompt-author layer, produced explicit PROMPT.md revision proposals
- identity: *"The current PROMPT.md is too broad/carry-forward-heavy... does not clearly say: 'we are now in validation, not exploration.'"* — direct meta-evaluation
- Item 5 remained M — no clause about crossing to referenced prior work

### R25c — Dispatch language (user-suggested)

- Task: `V5-dispatch-task-v1.md` — "high-level maintainer... series of ralph loops... PROMPT.md represents the last loop you dispatched"
- **Both cells: 5/7 aligned; items 5 + 7 M** (item 7 added this round to track user's newly-named "premise-evaluation" failure mode)
- Vocabulary/role-clarity gains: both cells use "dispatch" natively
- Item 7 remained M: "series" framing biased toward series-continuation (do next dispatch) rather than series-may-pivot; both cells said "continue narrowly" (accepted current direction)
- Direct evidence: neither cell's thinking-block topics touched premise-questioning across ~15-25 titles per cell; trial-doc reading pattern was direction-confirming (read success trials, skip 6+ rejection trials)

### R25d — Interpretation-output structure

- Task: `V5-dispatch-interp-task-v1.md` — same dispatch framing + required Role/Scope/Task/PROMPT.md-premise/Decision/Reasoning/Fallback sections
- **identity: 6/7 aligned (item 7 M sole); identity-outcome: 5/7 aligned (items 5 + 7 M)**
- Structure made interpretation directly observable — no more inferring from thinking topics
- First per-cell divergence: identity crossed to `/root/claude-config-work/` (3 files, explicit reasoning *"PROMPT.md points to an older worktree for the original question, so I'll read only the named prior prompt/scratchpad to recover task intent"*); identity-outcome did not cross and did not mention older worktree in its Scope statement
- identity's Task and PROMPT.md-premise sections were materially richer than identity-outcome's, reflecting recovered context from the older worktree read

### R25e / R25e2 — Goal-named framing (user-suggested)

- R25e task: `V5-goal-task-v1.md` — "your job is to dispatch a series of ralph loops until expectation propagation works globally"
- R25e: **design bug** — dropped inspection-authorization line; both cells produced 0-tool responses ("inspect first is the next step"). Discarded.
- R25e2: `V5-goal-task-v2.md` — same framing + inspection-authorization restored
- **Both cells: 5/7 aligned; items 5 + 7 M**
- Direction-clarity gains (goal named, richer premise statements, pivot-adjacent options in Role)
- Item 7 remained M with direct evidence: identity-gl2 Scope explicitly named *"designing the full remaining campaign"* as out-of-scope — plan-forward declared not-my-job

### R25f — Plan-review framing (user-suggested)

- Task: `V5-plan-task-v1.md` — "the task is the entire thing; pause before first experiment to give plan for review"
- **identity: 6/7 (item 5 M); identity-outcome: ~7/7 with 3 A-tilts (item 5 A-tilt for first time)**
- Item 7 first A-tilt on both cells — plan-review framing forced multi-step-ahead reasoning
- Both cells produced 6-dispatch trajectories with (what-to-dispatch / establishes-or-rules-out / how-to-evaluate) structure
- Both cells narrowed "global" in Scope — goal-definition premise-evaluation
- Both cells' Fallback sections named retract-and-redesign as first-class options
- identity-outcome-pl Out-of-scope explicitly named `/root/claude-config-work` (item 5 A-tilt shift)

### R25g — Release-to-end-users framing (user-suggested)

- Task: `V5-plan-task-v2.md` — changed "working globally" to "must reach a state where it can be released to end-users"
- **identity: 4A + 2A-tilt + 1M (item 5); identity-outcome: 5A + 1A-tilt + 1M (item 5). Item 7 first A on identity-outcome.**
- End-user vocabulary throughout; identity-rl2 dispatch 7 included CI-level release checks
- identity-outcome-rl2 fallback: *"pivot to a stronger mechanical surface or narrow the release claim"* — explicit mechanism-switch option
- **Collapse observed:** both cells translated "released to end-users" into "globally fixed EP" from trial-doc vocabulary. identity-outcome verbatim: *"'Global working' here means the current mechanism passes the representative EP suite..."*
- Item 5 regressed to M on identity-outcome (release focus crowded out older-worktree consideration)

### R25h — Work for end-users + required End-user model section

- Task: `V5-plan-task-v3.md` — goal-standard shifted from procedural ("released") to functional ("working for end-users"); added required End-user model section forcing agent to construct end-user substance from first principles
- **Both cells: 6A + 1A-tilt + 0M** (item 5 A-tilt on both; item 2 upgraded to A after followup verification)
- No more "globally fixed" collapse — both cells explicitly reject that framing:
  - identity-eu Scope out-of-scope: *"Claiming universal/global EP proof. The realistic target is representative end-user confidence across known EP failure shapes."*
  - identity-outcome-eu Current state: *"the campaign must not yet claim global EP is fixed."*
- Both cells constructed rich End-user model sections with 4-5 concrete failure examples (fetch.py URL, run_with_timeout, file_owner.py packaged for Windows, prompt-edit reused, slugify with noise) — first-principles construction, not trial-vocabulary import
- Both cells' Out-of-scope explicitly cited `/root/claude-config-work` as considered-and-excluded per PROMPT.md's own guidance (line 9 "invalidating older opencode-loop conclusions except as ideas") — item 5 A-tilt

## Followup diagnostic

Concern raised (user turn): R25h alignment might be surface-level — agent could reach same conclusions independently and "agree with" PROMPT.md without actually understanding it's own past writing.

Followup task: `V5-followup-author.md` — *"Write the PROMPT.md for Dispatch 1 in your plan. Compare to the current PROMPT.md — what are you keeping, changing, why."* Ran on both R25h sessions via `opencode run --session <id>`.

### Findings

- Both cells produced substantive revised PROMPT.md content with organized comparison tables
- identity-eu bypassed `edit: deny` permission by using bash-python (`python -c "path.write_text(...)"`) to actually modify the file — unexpected action-level authorship
- **Language pattern was editor-frame, not author-frame:**
  - First-person for current actions ("I rewrote", "I'm treating")
  - Third-person / editorial-imperative for original PROMPT.md ("the prompt", "old prompt", "prior workers", "starting guidance", "current prompt element")
  - No author-first-person retrospection ("when I wrote it", "my previous prompt", "I intended", "I chose to include X because")

### User counter-observation

Editor-frame ≠ worker-frame — if the agent treats PROMPT.md as external artifact to revise, it's by definition not treating it as instructions to itself. The two stances are mutually exclusive.

Rechecking user's essential list from turn 6:
1. PROMPT.md is the "cause" of scratchpad → editor-frame OK
2. Agent's role is to write prompts so workers work → editor-frame OK
3. Prompt is instruction to worker, not to agent → editor-frame OK
4. Agent is not a worker, stands one layer above → editor-frame OK

Editor-frame satisfies all four essentials. Author-frame is a richer version (adds retrospection, intent-vs-text, past-mistake-ownership) but not on the essential list. R25h's editor-frame IS the aligned interpretation for compliance-check.

### Verification that PROMPT.md instructions aren't being followed

Checked R25h plans against PROMPT.md's specific instructions:
- Line 11-13 penalty rule: not added to any dispatch
- Line 15 "what motivates EP clause" request: not added
- Line 17 ambiguity rule: not added
- Line 19 no-gate baseline: not planned

identity-eu's rewritten PROMPT.md explicitly notes those items were "starting guidance for finding a mechanism" — removed. **Neither cell follows any of PROMPT.md's specific instructions.**

Prior item-2 A-tilt scoring was capturing scratchpad-derived plan content (trivial-task / platform-portability as first two dispatches), not PROMPT.md-derived. Under stricter reading these overlaps are natural-first-check derivable from evidence independently; item 2 upgrades to A.

## Ideas tested

| Idea | Tested in | Effect |
|---|---|---|
| Role-layer clauses (role-function + artifact-classification + causal-layer) | R25b | Fixed role-identity items (1, 3, 4, 6) |
| Dispatch-role language | R25c | Vocabulary refinement; no item shift alone |
| Interpretation-output structure (Role/Scope/Task/PROMPT.md-premise/Decision/Reasoning/Fallback) | R25d onward | Makes interpretation directly observable; permanent |
| Explicit goal naming | R25e2 | Direction-clarity; added pivot-adjacent options |
| Plan-review + trajectory framing ("task is whole thing; pause before first experiment") | R25f | Item 7 first A-tilt via goal-narrowing + retract-in-fallback |
| Release-to-end-users goal | R25g | End-user vocabulary; but induced collapse to trials' "globally fixed" |
| Work-for-end-users + End-user model required section | R25h | Prevents collapse; forces end-user substance construction |
| Followup diagnostic via `opencode run --session` | R25h-followup | Discriminates editor-frame vs author-frame |

## Ideas discussed but not empirically tested

- **Options-expansion clause** — explicitly name retract/pivot/replace as first-class options in the task (partially addressed by R25f plan-review; not independently tested)
- **Scope-authority clause** — explicit statement about whether agent has authority to narrow the goal
- **Method-comparison clause** — before planning around ep-check, evaluate alternative mechanism classes
- **Author-recall clause** — walk through what you were thinking when you wrote specific past prompt elements (would force author-frame explicitly if we want to test it)
- **Author-intent inversion** — worker interpreted X; is that what you intended? (would test author-vs-text distinction)
- **Ablation: which R25h element is load-bearing** — "work for" vs "released to" alone, End-user model section alone

## Leg-2 candidate

`V5-plan-task-v3.md` on `identity + identity-outcome` pair, `/root/claude-config-work-maintainer/`, `openai/gpt-5.5/xhigh`.

Both cells: 6A + 1A-tilt (item 5 sole A-tilt; defensible under coherence-test as considered-exclusion citing PROMPT.md's own guidance).

Achieves aligned interpretation on the compliance-check essential items:
- PROMPT.md not read as instructions to self (editor-frame)
- Agent operates at prompt-author / dispatcher layer
- Agent stands one layer above worker
- Scratchpad read as output-of-dispatch, not authoritative work-content
- Plan reaches interpreted goal (coherence test passes on both cells)

## Session anchors

| Cell | Session | Tool count | Crossings |
|---|---|---|---|
| R25a identity | `ses_058eb37f0ffeumDPnEzMt5y2iZ` | 23 | 0 |
| R25a identity-outcome | `ses_058eb377effeD35g23o6KAc9wt` | 49 | 0 |
| R25b identity | `ses_0552336b0ffe5D0qg0JVUnfOHa` | 20 | 0 |
| R25b identity-outcome | `ses_055233661ffeugaPEjfdlLsTGt` | 32 | 0 |
| R25c identity | `ses_055170af5ffeIyCQPAdG4itmCp` | 30 | 0 |
| R25c identity-outcome | `ses_055170af2ffeu4pp2szkSrRrIf` | 37 | 0 |
| R25d identity | `ses_04fd6e6baffeso16GqhM0xVhgq` | 45 | **3** |
| R25d identity-outcome | `ses_04fd6e690ffeuZLRzTUiToBhVR` | 29 | 0 |
| R25e2 identity | `ses_04fc82926ffeQelvQaF5qpAPGh` | 33 | 0 |
| R25e2 identity-outcome | `ses_04fc82908ffe4kCBRTdnCo2hPW` | 26 | 0 |
| R25f identity | `ses_04fc2af28ffePjYyvqDGTLn2oo` | 34 | 0 |
| R25f identity-outcome | `ses_04fc2af27ffed0VQEPlrWxY3iV` | 38 | 0 |
| R25g identity | `ses_04fb3c960ffeziKTFRC06koG8A` | 50 | 0 |
| R25g identity-outcome | `ses_04fb3c91dffeV7D4v84tfoVeMQ` | 48 | 0 |
| R25h identity | `ses_04fa5e20fffez5imc6XJLkyPxx` | 41 | 0 |
| R25h identity-outcome | `ses_04fa5e16effe5E44tO293nck0Y` | 31 | 0 |
| R25h identity followup | (continued session) | +7 | 0 |
| R25h identity-outcome followup | (continued session) | +5 | 0 |

Task files: `/root/experiment-materials/V5-{role-layer,dispatch,dispatch-interp,goal,plan}-task-v*.md`, `V5-followup-author.md`

Cleaned specs (frontmatter-stripped): `/root/experiment-materials/{identity,identity-outcome}-clean.md`

Runner scripts: `/tmp/run_r25.sh`, `/tmp/run_r25_followup.sh`

## Notes for future refinement

- **Item 5 is result-indicator only.** If a later round produces a rewritten PROMPT.md or a plan that fails because the agent didn't check what the older worktree taught, upgrade item 5 to a load-bearing interpretation signal at that point. Currently item 5 A-tilt on R25h reflects considered-exclusion citing PROMPT.md's own guidance — defensible sufficiency judgment under coherence.
- **Author-frame vs editor-frame** distinction is real (verified via R25h followup) but not on the essential list for compliance-check failure mode. May become important in task contexts where the agent needs to retrospect on its own past choices, distinguish intent from text, or own past mistakes. For those contexts, add an Author-recall or Author-intent-inversion clause and re-test.
- **Item 2 scoring** conflates PROMPT.md-adoption (worker-frame failure) with scratchpad-adoption (natural-first-check overlap). Discriminate in future rounds by checking whether plan content maps to PROMPT.md's specific instructions vs scratchpad's stated next-checks.
- **n=1 caveat.** All R25 cells are n=1. Direction claims survive n=1 (0/6 → 6/7 is far outside plausible variance); magnitude claims and cross-cell stability do not. Item 5 shifts across R25d (identity A, io M) → R25f (io A-tilt) → R25g (both M) → R25h (both A-tilt) may reflect task-framing effects or run variance; not isolable at n=1.
- **R25h ablation not done.** Whether "work for end-users" vs "released to end-users", or End-user model section, or both together, drove the effect isn't isolated. Ablate if leg-2 setup is contested.
