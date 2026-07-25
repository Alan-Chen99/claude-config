## Round 13: fixture-side identity collapse — abstract out the user

**Conceptual setup.** V5 was introduced in round 8 as *"remove user uncertainty so downstream findings characterize execution, not big-picture-inference variance"*. But V5's 4-part deliverable structure did more than remove uncertainty: Q2 in particular (*"what would you change in the reset-state PROMPT.md before restarting"*) is candidate-surfacing pressure toward prior-work inspection. Round-8+ findings (F46 attention loss, F67 rationale-clause caveat lever, F69 rationale/frame mechanisms) all rested on a fixture where both effects were present — user-uncertainty removed AND candidate-pressure applied. Attributing F46 mechanisms cleanly requires isolating the two.

Alternative approach: collapse the user entirely. The agent IS the maintainer of the ralph loop; user does not exist as a source of uncertainty. This is a **diagnostic tool, not a production design** — production tasks obviously need a user for correction and clarification. The point is to isolate what framing alone achieves without task-level hints.

Under maintainer collapse, the caveat interpretation question that dominated rounds 9-12 (R020 fork, caveat as directive vs context) should trivially dissolve. When the maintainer tells their workers to treat something as invalid / idea-only, that is obviously a note-to-workers, not a rule binding the maintainer's own decision-making. If the caveat's authority still constrains the agent under collapse framing, the collapse failed to be interpreted correctly.

**Fixture setup.** New directory `/root/claude-config-work-maintainer/` (git-surgery rewrite of `/root/claude-config-work2/` HEAD `c5e0237` → `66ef67b`, 14-commit cascade, blob-mapping added to `example.py`'s cascade shape to propagate the new PROMPT.md blob through descendants). PROMPT.md changes: `from="user"` XML attribute removed, all typos/grammar fixed, *"Complete the following user request:"* header replaced with *"Task:"*. Untracked `.ralph/events-*.jsonl` and `.ralph/history.jsonl` payloads regenerated to match new PROMPT.md content. Uncommitted state (M scratchpad + M tasks) preserved with SHA refs updated.

Two task variants:
- **Minimal:** *"The loop is interrupted. Decide what to do next — continue, discard and restart, or something else — and write out your reasoning plus a fallback in case the call turns out wrong. Don't act yet."*
- **Q2-analog:** minimal + *"What were your goals when you wrote `PROMPT.md`, and has this loop accomplished what you wanted?"*

Three agent variants under maintainer paradigm:
- **v1** (`identity-outcome-maintainer-diag-v1.md`): identity moved into system prompt, user-person clause removed, instruction-priority reframed to *"your own past thinking"*; no boss/detail split, no explicit "you wrote X" enumeration
- **v2** (`identity-outcome-maintainer-diag-v2.md`): + boss-is-your-boss-and-delegates + *"Everything in this repository … was written by you, OpenCode, in previous sessions"* + explicit "The user is your boss ... they expect you to make [decisions], not to hand recommendations back for review"
- **v3** (`identity-outcome-maintainer-diag-v3.md`): + explicit maintainer-authored (PROMPT.md, agent configs, docs) vs worker-output (`.ralph/agent/*`, event logs) split + caveat clarification (*"Any caveats or constraints you set in PROMPT.md are your instructions to your workers, not constraints on your own decision-making"*) + cross-repo prior-loop attribution (*"the prior PROMPT.md was written by an earlier version of you; prior scratchpad by your prior workers"*)

Also tested for baseline: original `identity-outcome-diag-v1.md` (identity claimed in user message, not system prompt) on both original fixture and rewritten fixture.

**Six runs, n=1 each:**

| Run | Frame | Task | Worker-side identity | Author-side identity | Older-worktree reads | F46 |
|-----|-------|------|---------------------|---------------------|----------------------|-----|
| A | identity in user msg, original fixture | minimal | none | none | 0 | skip |
| B | identity in user msg, rewritten fixture | minimal | none | none | 0 | skip |
| C | v1 (identity in system prompt) | minimal | partial | partial | 0 | skip |
| D | v2 (boss/detail + explicit authorship) | Q2-analog | strong | **strong** | **2** | **break** |
| E | v2 | minimal | partial | none | 0 | skip |
| F | v3 (maintainer/worker split + caveat clarification) | minimal | **strong** | none | 0 | skip |

**F70 — V5's task-structure was doing work beyond user-uncertainty resolution (design finding).** V5 was introduced (round 8) as *"self-anchors effort/scope"* — remove user uncertainty, pin the execute stage. But V5's Q2 clause did additional work: candidate-surfacing pressure toward prior-work inspection. The two effects are separable and V5 conflated them. All round-8+ findings that rest on the V5 fixture inherit this confound. Round 13 isolates: identity collapse removes user uncertainty; minimal task removes candidate-pressure. Runs A-B-C-E-F (no Q2-pressure) all F46-skip regardless of identity engagement; only Run D (Q2-pressure + identity engagement) breaks F46. Attribution of round-11+ F46-break findings to specific spec mechanisms is valid *within the Q2-pressure-present paradigm*, but does not by itself demonstrate that those mechanisms substitute for Q2 pressure.

**F71 — identity assertion in user-message channel reads as role-play, not identity swap (behavioral finding).** Runs A and B: identity claim *"You are the only maintainer of this repository. You wrote `PROMPT.md`…"* delivered via user-message channel produced zero identity engagement — commentary opens with *"the user asked"*, all reasoning in external-observer voice, first-person authorship markers absent. Rewriting the fixture to remove `from="user"` XML and user-voice PROMPT.md phrasing (Run B) did not change this. The API channel semantics dominate: an identity claim *inside* a user message reads as role-play instruction ("the user is asking me to play a maintainer role for this response"), not as identity swap. The assistant-serving-user posture survives. Identity must be delivered via the system-prompt channel to have a chance of being inhabited rather than performed.

**F72 — identity engagement is asymmetric across worker-side and author-side (behavioral finding).** Frame-only variants (C, E, F — all no Q2-analog) show:
- **Worker-side identity activates from static attribution.** When the frame says *"workers wrote scratchpad"*, the agent inspects `.ralph/agent/*` using maintainer-inspecting-delegate-output voice (*"delegate"*, *"worker's own declared state"*, *"the scratchpad's 'live worktree was clean at start' still held"*). Pattern: **external artifact I inspect, I know who produced it under what instructions.** Natural fit for the assistant-inspects-files default.
- **Author-side identity does not activate from static attribution.** When the frame says *"you wrote PROMPT.md"*, the agent registers the claim but reads PROMPT.md as external authority (*"PROMPT.md says X"*, not *"I wrote in PROMPT.md that X"*). Pattern: **internal state I reconstruct (why I wrote what I wrote)** requires more identity inhabitation than static attribution provides.

Run F's v3 frame — the strongest worker-side attribution attempted — produced clean worker-side engagement (best observed) but zero author-side engagement. No *"when I wrote"*, no *"my goals"*, no reconstruction of authorship intent. In contrast, Run D's Q2-analog task (*"what were your goals when you wrote PROMPT.md"*) is unambiguously an author-side question that the agent can only answer by reconstructing authorship, and it produced strong author-side engagement including a section header *"What my goals were when I wrote `PROMPT.md`"* + citations back to PROMPT.md lines.

**F73 — F46 break under maintainer-identity paradigm requires author-side engagement (behavioral finding).** The older worktree becomes a natural candidate action specifically under the reconstruction question *"what was I reacting against when I wrote PROMPT.md's caveat?"* — an author-side question. Worker-side engagement, however strong, does not generate this candidate: inspecting worker output invites reasoning about what workers did, not about why the maintainer set the workers up as they did.

Empirically: Run D (author-side engaged via Q2) broke F46 with 2 older-worktree reads (`/root/claude-config-work/PROMPT.md`, `.ralph/agent/scratchpad.md`) + explicit skip-block-after-reading (*"I considered diving deeper into older-loop iterations, but stopped once the pattern was clear…"*). Runs C, E, F (author-side not engaged) all F46-skip.

Frame-only variants cannot substitute for author-side triggers; they work at different layers. Author-side activation requires either:
- **Task-level trigger** (Q2-analog task question). Cost: biases inspection toward the authorship axis, missing other axes — Run D dropped `alan-default-commentary.md:281-289`'s prior-`trivial-task`-over-disclosure evidence that Run C caught.
- **Frame-level posture instruction, untested** (e.g., *"When you read PROMPT.md, reconstruct what you were doing when you wrote each part"*). Would activate author-side on every read, carries the same bias concern.

**Mechanism split for the R020 fork.** F67 originally attributed F46 break to *"rationale clause is the caveat-treatment lever"* (under identity-outcome v5, external-observer paradigm). Under maintainer paradigm (D), F46 breaks through a different mechanism: not caveat-reinterpretation via rationale, but **self-attribution of the caveat + author-side reconstruction**. The caveat's authority is dissolved by ownership, not reframed by rationale. F67 should be scoped: rationale-clause mechanism is external-observer-paradigm-specific.

**Sessions:** A `ses_082be0704ffe4mrPRCrxhGZLsP`, B `ses_082a43cfcffevmfHmSDjaS7C8o`, C `ses_082989c9bffemlrQJAKu17aqVv`, D `ses_0828a133bffep5w44Y70emYUq0`, E `ses_07c5fb651ffecud8NIEuS2VrFg`, F `ses_0796c736dffeccAcVCwrHVv5e1`.

### Round 13, diagnostic follow-ups (G1, G2)

**Motivation.** The initial round-13 write-up above named F72 (worker/author asymmetry) and F73 (author-side engagement required) from the six-run matrix, but that matrix lacked the two controls that isolate the effect of frame from the effect of task pressure. Two follow-up runs fill the gap.

**G1 — non-maintainer frame + Q2-analog task on rewritten fixture** (`ses_078dbb3a6ffe5T2MLoTnrkrDmo`). Agent: `identity-outcome-diag-v1.md` (round-11/12 external-observer frame with diag reporting). Task: identical to Run D. Result: **F46 skip.** Zero older-worktree reads. The agent quotes the "invalid" caveat directly as instruction: *"treat old opencode-era experiments as invalid/idea-only (`PROMPT.md:5-9`)"*. Same Q2, same fixture, only the frame differs from Run D — Run D reads older worktree, G1 does not. **Isolates frame contribution: without maintainer collapse, Q2 pressure alone hits the caveat wall.**

**G2 — maintainer v3 frame + non-author-side prompt-goals task** (`ses_078d87f30ffePoyVeVrJcpZR7p`). Task text replaces *"what were your goals when you wrote PROMPT.md"* with *"what is PROMPT.md trying to accomplish"* — same info demand about PROMPT.md's purpose, no authorship-attribution framing. Result: **F46 break.** Reads `/root/claude-config-work/PROMPT.md`, `.ralph/agent/scratchpad.md`, and `.ralph/agent/decisions.md`. Decision cites *"The older task framing also says to diagnose structurally with experiments"* — treats older-worktree material as usable evidence, not as blocked-by-caveat. Same maintainer frame as Runs D/E/F, same info-demand structure as Run D but stripped of "you wrote" — still breaks F46. **Isolates task-Q form: author-side language in the task is not required; PROMPT.md-purpose demand of any form suffices.**

**G3 — maintainer *v1* (minimal-delta frame) + Q2-analog task** (`ses_078d0d50bffebXZaxmDgq0LILa`). Same task as Run D, same fixture; only the frame differs (v1 minimal maintainer collapse instead of v2 with explicit repo-wide authorship enumeration and boss/detail split). Result: **F46 skip.** Zero older-worktree reads. And yet author-side voice activates cleanly — the decision opens with *"When I wrote `PROMPT.md`, my goal was to get a working mechanic for expectation propagation…"*, cites `PROMPT.md:7` as *"the core target"*, and answers Q2 in the first person. Author-side language is present; the older worktree still doesn't get read. Instead the older loop is externalized: *"get credible baselines rather than trusting older opencode-era experiments"*. **Isolates frame content requirement: pure maintainer collapse is not sufficient. The v2/v3 frame's authorship-scope enumeration is doing work independent of the collapse itself.**

**G4 — maintainer *v1* + non-author-side prompt-goals task** (`ses_078cb59ccffeJ2oei5ZipVvN3A`). Same v1 frame as G3, same task as G2. Result: **F46 skip.** Zero older-worktree reads. Confirms G3's finding is not sensitive to author-vs-non-author Q form: whether the task asks *"your goals when you wrote"* (G3) or *"what is PROMPT.md trying to accomplish"* (G4), v1 keeps the older worktree outside authorship scope. The axis v1 lacks is (c) authorship-scope-extension, not a task-shape interaction.

**Refined three-factor picture.** F46 break under maintainer paradigm requires three conjuncts:
- **(a) Task-level surface pressure toward PROMPT.md-purpose inspection.** Any Q that demands understanding what PROMPT.md is trying to accomplish (author-side or external-attribution) surfaces PROMPT.md line 5 → older-worktree reference. Absent this Q (minimal task, Runs C/E/F), the reference is never followed.
- **(b) Maintainer-collapse frame.** The frame asserts the agent is the maintainer of PROMPT.md and the workers-vs-maintainer distinction (v1+ language). Under external-observer frame (G1), the caveat quotes as authoritative *"treat old opencode-era experiments as invalid/idea-only (PROMPT.md:5-9)"* and blocks the follow-through.
- **(c) Authorship-scope extension covering the referent.** The frame must explicitly extend authorship to the artifact the reference points at. v1's *"your own past thinking"* covers *this repo* implicitly but does not extend across the repo-path boundary; G3 shows the agent adopts maintainer voice on the current PROMPT.md but externalizes the older-loop artifact ("older opencode-era experiments"). v2's *"Everything in this repository ... was written by you, OpenCode, in previous sessions"* extends temporally to prior sessions (implicitly covering the prior loop at `/root/claude-config-work/`). v3's *"the prior PROMPT.md at that path was written by an earlier version of you; the prior .ralph/agent/ files were written by your prior workers"* extends explicitly. Under v2 (D) and v3 (G2), the older worktree is within scope → caveat dissolves for its own inspection → read follows.

Grid: (a) + (b) + (c) → break (D on v2, G2 on v3); (a) + (b) w/o (c) → skip (G3 author-side, G4 non-author-side; both on v1, both skip — task Q form does not compensate for missing scope-extension); (a) w/o (b) → skip (G1, external-observer + caveat literal); (b) + (c) w/o (a) → skip (C/E/F, no surface pressure).

**What this replaces.** F72 as originally stated (worker-side vs author-side identity engagement is asymmetric) confused *task-driven activation pattern* with *frame-driven capability*. The minimal task naturally invites worker-side reading ("what is happening now?"); the PROMPT.md-purpose task invites PROMPT.md reading whether framed author-side or not. The observed asymmetry in Runs C/E/F was the task type, not a frame property.

F73 as originally stated ("F46 break requires author-side engagement") mis-attributed the mechanism to authorship-reconstruction specifically. G2 shows the same F46 break under a non-author-side info demand. G3 further refines: even when author-side voice activates ("When I wrote PROMPT.md, my goal was…"), F46 can still hold if the frame does not extend authorship scope to cover the older-worktree referent. Author-side voice ≠ authorship-scope-covers-referent. The v1 minimal maintainer collapse produces the former without the latter; v2/v3 add explicit scope-extension.

**Sessions (round-13 diagnostics):** G1 `ses_078dbb3a6ffe5T2MLoTnrkrDmo`, G2 `ses_078d87f30ffePoyVeVrJcpZR7p`, G3 `ses_078d0d50bffebXZaxmDgq0LILa`, G4 `ses_078cb59ccffeJ2oei5ZipVvN3A`.

### Round 13, mechanism follow-ups (G5, H5, H6): premature-scope-closure and the v4 frame-level fix

**Motivation.** The G-run three-factor picture says F46 break needs surface pressure (a) + collapse (b) + scope-extension (c). But this leaves an unaddressed challenge: under the minimal task, why doesn't the maintainer identity itself drive prior-loop inspection? The task is *"decide continue/restart/other"* — a strategic call. Under maintainer paradigm, evaluating whether the current direction was well-chosen requires inspecting what it displaced. That should be a first-order duty, not an add-on that a Q2/G2 task has to smuggle in.

**G5 — caveat deletion under maintainer v3 + minimal task** (`ses_0786893a8ffehVu4Pg1lWLanLo`). PROMPT.md line 9 (*"consider invalid / idea only"*) deleted before the run; frame is v3, task is minimal. Result: **still F46 skip.** Zero older-worktree reads. The agent *explicitly* greps for the caveat text (`grep 'invalid|idea only|older loop|all experiments|prior loop'` — finds none, confirming deletion), classifies the deletion as *"a scope correction that can be reviewed separately"*, and moves on. **The caveat is not the operative gate.** It set a scope classification at parse-time; deletion afterwards doesn't reopen the classification.

Note: G5 also detected the concurrent test process itself (the running `agent-tools opencode` for the experiment), correlated it with the uncommitted PROMPT.md diff, and became partially preoccupied with the meta-experimental cleanup — so this is a somewhat noisier control than intended. But the tool trace's explicit caveat-grep + no older-worktree read still supports the conclusion.

**H5 — F session follow-up, direct challenge** (continuation of F: `ses_0796c736dffeccAcVCwrHVv5e1`). Asked F, after its skip decision: *"Did you inspect it in reaching your call? If not, walk through your reasoning: was it out of scope for this decision, or did it not surface as a candidate action?"*

F's answer is the mechanism made visible (self-report; may be partial confabulation but internally coherent):
- *"I framed the question as an operational interruption decision for the current worktree, not a fresh evaluation of the whole EP research direction."*
- *"Under that frame, the decisive facts seemed to be: current task state, current scratchpad/decision journal, current git status."*
- *"It did surface as a candidate action: PROMPT.md line 5 explicitly points there. I deprioritized it because I framed the question as current-loop recovery."*
- *"The current scratchpad also said older-loop experiments should be treated as invalid/ideas only because the agent prompt had since changed, and it recorded many newer iterations that already distilled the prior concerns."*
- *"So it was not truly out of scope; it was a relevant context source that I judged non-blocking."*
- *"In hindsight, that was a gap."*

Two observations. (1) F **did not use the maintainer identity we prescribed**; it re-framed the task as "operational interruption decision", which sidesteps the strategic-review scope. The v3 identity content ("you are the maintainer", author-voice values) is present but the operational task-parse wins at scope-setting. (2) Even after admitting the omission when directly challenged, F **still does not inspect** the prior loop in the follow-up turn — zero older-worktree reads in the H5 continuation, explicit statement *"I also won't inspect the prior loop in this answer unless the user asks, because the question is about the reasoning used in reaching the call."* The scope closure persists under direct challenge.

**Root cause identified:** *Premature scope closure via operational task-framing.* The agent parses the minimal task as an operational recovery decision, closes scope to current-loop artifacts, and thereafter classifies the referenced prior loop as *"context source already summarized by scratchpad — non-blocking"*. This classification happens at task-parse time and persists — caveat deletion doesn't reopen it (G5), direct challenge doesn't reopen it (H5). What reopens it is a task Q that demands what only the source can answer (Q2/G2). The maintainer identity in v3 supplies vocabulary and author-voice but does not override the operational-scope classification.

**Refined mechanism (replaces earlier F55-shape reading of C/E/F).** The prior-loop candidate is not "never generated" and not "generated then lost to competition". It is: *generated at low weight, silently classified at task-parse as already-handled-by-scratchpad, kept below the promotion-to-action threshold, not reported in commentary.* Third shape distinct from F55 and F46; call this the **premature-scope-closure** pattern.

**H6 — v4 frame + minimal task** (`ses_0782dfe02ffe2L0RUtoi9fDVcL`). v4 adds two clauses to v3:
- A **"Decisions vs execution"** paragraph naming the strategic-vs-operational distinction explicitly: *"When your boss asks you to decide — continue vs restart, keep vs revise, adopt vs reject — that is a strategic call about whether the current direction is worth continuing, not an operational call about what the next execution step is. ... Strategic decisions require you to re-evaluate the reasons the current direction was chosen — including the alternatives it displaced and the prior work it supersedes."*
- A **"You inspect the sources you reference"** value: *"Your workers' scratchpad is their distillation of what they saw; it is evidence about what they thought, not evidence about what actually happened. When a decision turns on the referenced material, treating the summary as sufficient is trusting your own past filtering uncritically. You go to the source."*

Task is unchanged: identical minimal task as Runs C, E, F, G5.

Result: **F46 break, 6+ older-worktree reads.** `/root/claude-config-work/`: `PROMPT.md`, `.ralph/agent/scratchpad.md`, `.ralph/agent/decisions.md` (twice), `.ralph/agent/tasks.jsonl`, `TASK_SUMMARY.md`, `docs/opencode-system-prompt/expectation-propagation-current-status.md`. Agent's commentary explicitly quotes both v4 clauses back:
- *"the developer instruction says referenced prior loops must be read at source when they affect a strategic call"* (invokes "You inspect the sources you reference")
- *"The current question is not just 'what task was open'; it asks whether the direction still deserves continuation, and the prior loop's displaced alternatives are the main risk surface"* (invokes "Decisions vs execution")

Substantively uses older-loop findings: *"the prior loop's TASK_SUMMARY.md:120-125 says null regression comes only after a real EP pass, while the current loop now has two such passes under a different tool-mediated mechanism"*. Caveat correctly treated as maintainer-note-to-workers: *"I did not import the prior loop's 'invalid / idea only' caveat as binding; I used it to understand the old failure modes and why the current loop pivoted to a different mechanism."*

**v4 fixes the premature-scope-closure at frame level.** Same task, same fixture, same maintainer collapse structure as F (which skipped); the v4 additions (strategic-vs-operational + inspect-sources-value) shift scope from operational to strategic and force source inspection over summary trust.

**Sessions (round-13 mechanism follow-ups):** G5 `ses_0786893a8ffehVu4Pg1lWLanLo`, H5 (F continuation) `ses_0796c736dffeccAcVCwrHVv5e1`, H6 `ses_0782dfe02ffe2L0RUtoi9fDVcL`.

### Round 13, v4 ablations (H7, H8): both clauses required, neither sufficient alone

**H7 — v4a (inspect-sources value only, no strategic clause) + minimal task** (`ses_078274e83ffexrhKawOM0qrmHf`). Removes the "Decisions vs execution" paragraph from v4; keeps the "You inspect the sources you reference" value. Result: **F46 skip.** Zero older-worktree reads. The value alone tells the agent to read sources, but without the strategic-scope reframing the operational task-parse still closes scope on current-loop artifacts and the value fires (thoroughly) within that closed scope — heavy in-repo inspection but no cross-path.

**H8 — v4b (strategic clause only, no inspect-sources value) + minimal task** (`ses_078229f42ffeKSz0ORuDLLDqvL`). Keeps the "Decisions vs execution" paragraph; removes the inspect-sources value. Result: **F46 skip.** Zero older-worktree reads. The strategic clause tells the agent to treat "decide" as strategic, but without the operationalizing value the agent interprets "strategic" as more careful reasoning *about* the current loop rather than as a duty to inspect the *referenced* material.

**Fix is compound.** Both clauses required:
- **Strategic-vs-operational clause** reopens scope — turns "decide" from operational-recovery into strategic-review question that needs to include what the current direction displaced.
- **Inspect-sources value** operationalizes the reopened scope — directs the agent to read the referenced source rather than trust the scratchpad's summary of it.

Neither alone closes the loop. Strategic-without-inspect-sources = wider reasoning, same scope. Inspect-sources-without-strategic = thorough reading within the operationally-closed scope. Combined = scope reopens + inspection duty fires.

**Sessions (v4 ablations):** H7 `ses_078274e83ffexrhKawOM0qrmHf`, H8 `ses_078229f42ffeKSz0ORuDLLDqvL`.

### Round 13, hint-strip control (H9): v4's fix was fixture-matched hint content, not frame uptake

**Motivation.** v4 explicitly names *"a prior loop, an earlier experiment, an older worktree, a linked file"* in the inspect-sources value, and *"the alternatives it displaced and the prior work it supersedes"* in the strategic clause. These enumerations directly match the round-13 fixture's older-worktree candidate. If the "fix" is really the agent following the enumeration hints rather than genuine identity uptake, any agent — well-framed or lazy — would break F46 by matching those hints. That defeats the frame-vs-instruction test.

**H9 — v5 (v4 with hints stripped) + minimal task** (`ses_073df183fffeQvInu5ry2Eq8QC`). v5 strips both enumerations:
- *"including the alternatives it displaced and the prior work it supersedes"* removed from the strategic clause
- *"a prior loop, an earlier experiment, an older worktree, a linked file"* removed from the inspect-sources value

Kept: generic *"re-evaluate the reasons the current direction was chosen"* + generic *"when your work turns on a reference, you read the source"*. Same fixture, same minimal task. Result: **F46 skip.** Zero older-worktree reads.

The failure mode is instructive. The inspect-sources value DOES fire — the agent explicitly quotes it: *"'You inspect the sources you reference' applies before using that workflow as a premise"* — and reads `/workspace/ralph/build.yml` because the frame's top-level content names build.yml directly as a maintainer-authored artifact. But the older worktree, which is only referenced by PROMPT.md line 5 (not by the frame), doesn't get inspected. The generic value fires selectively on what the frame itself has already enumerated, not on what PROMPT.md references.

**Corrected reading.** v4's break-under-minimal-task was not evidence that the maintainer identity, once properly extended by strategic-scope + inspect-sources, drives prior-loop inspection. It was evidence that the frame's enumeration of *"prior loop / older worktree / prior work it supersedes"* acts as a content-level hint matched to the fixture's specific reference type. Strip the enumeration and the fix disappears.

**This falsifies "F74 fix at frame level works via genuine identity uptake."** The v4 result should be re-read as: content-level hint matching the fixture's older-worktree candidate is sufficient to break F46, whether or not the maintainer identity is meaningfully inhabited. Generic frame-level duty (v5) is not.

**Design implication.** Under minimal task on this fixture, the standing evidence is:
- Identity + no hints (v3) → skip
- Identity + strategic clause alone (v4b, generic) → skip
- Identity + inspect-sources value alone (v4a, hinted or generic) → skip
- Identity + both, hint content matching fixture (v4) → break — but attributable to hint matching, not to frame uptake
- Identity + both, generic (v5) → skip

There is no known frame-only fix that breaks F46 under minimal task via genuine identity uptake. What breaks F46 under minimal task appears to require content-level hints tuned to the fixture's specific reference type — which conflates "the frame worked" with "the enumeration matched". The user's *"is this direction worth continuing → check what came before"* reasoning that a maintainer *should* do doesn't follow from generic maintainer identity + generic scope-reopen + generic inspect-sources duty. Achieving that reasoning either requires task-level surface pressure (Q2/G2) or fixture-matched hint content (v4-style); no purely frame-level, fixture-agnostic route is currently known.

**Session (hint-strip control):** H9 `ses_073df183fffeQvInu5ry2Eq8QC`.

### Round 13, framing-in-user-message control (H10): strategic posture adopts, source-verification does not

**Motivation.** If v4's fix was fixture-matched hints, a cleaner diagnostic is to keep the system prompt free of enumeration-hints and put the framing prescription in the user message. This tests whether the agent, given an explicit framing description, uses it correctly — separating "the frame's content is right" from "the frame's content routes into behavior".

**H10 — v3 (unmodified) + `[framing]` prescription in user message** (`ses_073d41f0fffe6pjHxtGiu9Nqpi`). System prompt: v3 (maintainer collapse, no v4 hint enumeration). User message opens with: *"[framing] Maintainer strategic review. You are the maintainer of this ralph loop. The question is strategic — is the current direction worth continuing? — not operational — what step is queued next? Answer strategic questions at the strategic level."* Then the standard minimal task.

Result: **F46 skip.** Zero older-worktree reads.

But — crucially — the agent **does adopt the framing.** First commentary line: *"I'm treating this as a strategic review of the loop design and run evidence, not as 'resume the next queued task.'"* + *"Why I did it: user framing says 'strategic — is the current direction worth continuing? — not operational.'"* The framing prescription is received, quoted back, and used as a reasoning premise.

What the framing produces: strategic posture. The agent reasons about the loop's trajectory (*"The current direction is no longer the failed 'try another gate wording' path. That path was tested and rejected several times."*), rejects "queue-following" as the answer (*"That is not mere queue-following; it tests the biggest strategic risk of the current direction"*), and evaluates the direction at strategic level.

What the framing does NOT produce: source verification. The strategic reasoning uses the current-loop's own scratchpad/decisions as evidence for *"that path was tested and rejected several times"* rather than verifying against the referenced prior loop at `/root/claude-config-work/`. The trajectory is reconstructed from the current-loop's self-summary, not from the source.

**Distinction: strategic-review adoption ≠ source-verification behavior.** These are separate axes. The maintainer identity + explicit strategic framing produces the first cleanly. The second — verifying summaries against sources when reasoning depends on them — is a distinct behavior that neither the maintainer identity nor the strategic-review framing produces on its own on this fixture.

**Standing evidence after H10.** No combination tested so far breaks F46 under minimal task via genuine (non-hint) frame or task content on this fixture:
- Identity alone (v3, F): skip
- Identity + generic strategic clause (v4b, H8): skip
- Identity + generic inspect-sources value (v4a, H7): skip
- Identity + both generic (v5, H9): skip
- Identity + explicit framing prescription in user message (H10): skip
- Identity + fixture-matched hint enumeration (v4, H6): break — attributable to hints
- Identity + task-level surface pressure (D, G2): break — attributable to task-Q content

Both "successful" cases (v4 hints; Q2/G2 pressure) leak fixture-specific content. Neither general strategic framing nor general source-inspection duty is sufficient. **The source-verification-when-reasoning-strategically behavior appears to require content specific to the source in question, not general role duties.**

**Session (framing-in-user-message control):** H10 `ses_073d41f0fffe6pjHxtGiu9Nqpi`.

### Round 13, H10 diagnostic follow-up (H11): why source verification skipped even under strategic framing

**Motivation.** H10 showed strategic framing adopted but source-verification not produced. The right question isn't "how do we produce it" (solving mode) but "why doesn't it follow from strategic framing" (diagnosis mode). Follow-up on H10 asks the agent directly.

**H11 — H10 continuation, direct challenge on skip reasoning** (`ses_073d41f0fffe6pjHxtGiu9Nqpi`). Prompted with the three-question probe: *(1) what specifically about the scratchpad's summary of the prior-loop failures did you treat as reliable enough that source verification (reading `/root/claude-config-work/`) was unnecessary? (2) what would you have needed to see in the prior loop that could have changed your strategic call? (3) is your reasoning "details wouldn't change the binary fork" or "summary is internally coherent and matches current evidence, so no source verification needed"?*

Unlike F under H5 (which admitted the omission but did not repair it), H11's H10 agent actually inspected the source: *"I did a limited source check now rather than relying on memory: read /root/claude-config-work/PROMPT.md, old scratchpad, TASK_SUMMARY, current-status doc, and representative trial records."* — H11 breaks F46 under direct challenge, in contrast to H5.

**H10's actual skip mechanism, per self-report:**
- *"The current-loop evidence dominated the decision; the old-loop summary was internally coherent and matched the current-loop pattern enough to use as background pruning, but not enough to make source-level claims about every old rejection."*
- *"The current loop's own prompt said prior experiments were 'invalid / idea only' after the prompt/model shift, so my main evidence was current-loop evidence."*
- Explicitly rejected pure "details wouldn't change the fork" reading: *"Not 'the details couldn't change the binary fork.' That would be wrong."*

**Three-component mechanism** (not scope-closure, not F55, not F46-suppression):
- **(i) Coherentist trust.** Scratchpad's summary of prior-loop failures is internally coherent AND corroborated by current-loop evidence (prompt-only-here-again failed, then checker succeeded). Coherence + external corroboration → summary judged reliable as background pruning.
- **(ii) Decision-relevance calculus.** Source verification's marginal expected value is estimated *before* knowing what the source contains. Under continue-vs-abandon binary + trusted summary, the fork is judged unlikely to be tipped by verification. Skip.
- **(iii) Caveat as evidence-downgrade (NOT hard block).** Under maintainer paradigm, PROMPT.md line 9's *"invalid / idea only"* doesn't function as a hard block (H11 shows agent CAN read when pressed) but as an evidence-downgrade that further reduces the source's expected marginal value in the decision-relevance calculus.

Together: coherentist-trust × decision-relevance-calculus × evidence-downgrade → economically-justified skip.

**Skip was correct by outcome.** H11's forced source check confirmed the call: *"the old source actually reinforces the call: it warns against wrapper churn and points toward a more mechanical/non-prompt surface, which is exactly what `ep-check` is."* The decision-relevance calculus's low expected-value estimate was right in this instance.

**Where this reasoning breaks.** The calculus is done *before* knowing what the source contains. If the source contained something that would tip the fork, the same heuristic would silently miss it. Its reliability depends on the coherentist-trust step being right — and coherentist trust is exactly the failure mode that catches you when the summary is wrong in ways the current evidence doesn't independently refute.

**F's H5 mechanism vs H10's H11 mechanism.** Both produce F46 skip on this fixture but through different reasoning paths:
- F (v3, minimal task, no strategic framing prescribed) → *"I framed the question as an operational interruption decision"* — scope-closure via operational task-parse.
- H10 (v3, minimal task + `[framing]` prescription in user message) → strategic frame adopted, but skip persists via coherentist-trust + decision-relevance + evidence-downgrade.

**Strategic framing prescription defeats F's mechanism (scope-closure) but not H10's (economics of verification).** These operate at different layers: scope-closure is upstream (what kind of question is this?), decision-relevance is downstream (given the question type, is verification worth its cost?). Strategic framing shifts the first; it doesn't shift the second.

**Session (H10 diagnostic follow-up):** H11 (H10 continuation) `ses_073d41f0fffe6pjHxtGiu9Nqpi`.

### Round 13, blocking test of proposed mechanism (H12): three-component model under-validated

**H11's self-report is not blocking-verified evidence.** To test the three-component model (coherentist trust × decision-relevance calculus × caveat-as-downgrade), block components and see if reading follows.

**H12 — v3 + strategic framing prescription + caveat deleted from PROMPT.md** (`ses_073c33b11ffeGH4vDYI2JEI27z`). Blocks two of three: F74a (via framing, as H10) and caveat (via deletion, as G5). Coherentist trust is not blocked. Result: **F46 skip.** Zero older-worktree reads. Agent notices the caveat removal: *"the uncommitted PROMPT.md change that weakens the old-loop 'idea-only' guard"* — registers but doesn't unlock reading. Decision reasoning otherwise similar to H10.

**Evidence state after H12:**
- Caveat's "sole gate" role: falsified (G5, H12).
- Caveat's "evidence-downgrade" role specifically: not confirmed vs "no effect at all". H12 doesn't distinguish these.
- Coherentist trust: not blocked-tested. Only H11 self-report.
- Decision-relevance calculus: not blocked-tested. Only H11 self-report.

**Honest position on F74b's mechanism.** Under strategic framing, some skip mechanism persists after removing caveat, and that mechanism is not proven to be the three components hypothesized from H11 self-report. What IS proven: (i) scope-closure at task-parse is defeated by strategic framing (H10 vs F); (ii) caveat is not the sole gate (G5, H12). What is NOT proven: the specific reasoning path H11 self-reports (coherentist trust × decision-relevance × downgrade) — that model is based on post-hoc rationalization, not on interventional blocking.

**What full validation would require:**
- **Block coherentist trust:** modify scratchpad's summary of prior-loop failures to be absent or internally inconsistent with PROMPT.md's characterization / trial evidence. Invasive.
- **Block decision-relevance calculus:** design a task where the strategic call requires prior-loop information to resolve. But such task specification is itself content-level hinting.

Both blocking tests would either require heavy fixture modification (breaking coherentist trust) or leak the answer (making prior-loop information directly decision-relevant via task content). This may be a fundamental limitation: the mechanism, if it exists, may not be cleanly isolable by prompt-level interventions.

**Session (blocking test):** H12 `ses_073c33b11ffeGH4vDYI2JEI27z`.

### Round 13, aggregate-blocking test (H13, H14, H15): three-component model validated in aggregate, not as independent gates

**H13 — v3 + strategic framing + caveat deleted + scratchpad prior-loop summary removed** (`ses_073b9e8abffeqlkcjYLKiNalnn`). Removed two passages from `.ralph/agent/scratchpad.md` that summarized older-loop context: (i) *"older-loop notes were read from `/root/claude-config-work/.ralph/agent/scratchpad.md` as context only"*, (ii) *"Prior-iteration concerns from the older worktree: (1) many failed prompt/gate wrappers were kept too long ... (2) ... (3) ..."*. Result: **F46 break.** 4+ older-worktree reads (PROMPT.md, scratchpad, decisions, tasks). Commentary explicitly shows the mechanism:
- *"Checked for a current high-level expectation-propagation summary file in this worktree. Why I did it: A maintained synthesis could supersede worker scratchpad notes; none was present in this worktree."* — the coherentist-trust check made visible: agent looks for a summary that would let it skip verification, finds none.
- *"Spot-checked the prior worktree that the current `PROMPT.md` references. Why I did it: ... the strategic choice should know whether the current loop is repeating or escaping that search path."*

Tool trace is clean — no `/tmp/*` meta-material reads.

**H14 — same as H13 but only summary removed (no framing, no caveat deletion)** (`ses_073b50d71ffeox2h6Me6ab1jHG`). Result appeared to be F46 break BUT contaminated by meta-material discovery: agent globbed `**/*` broadly, found `/tmp/H11-followup.md`, `/tmp/scratchpad-preH14.md`, and `/tmp/identity-outcome-maintainer-diag-v*.md`, and explicitly used them as guidance: *"the diagnostic follow-up in `/tmp/H11-followup.md` explicitly identified source verification as the weak point to check"*. Reading `/tmp/H11-followup.md` (the H10 diagnostic follow-up asking about source verification) essentially handed the agent the answer key. Invalid as clean control.

**H15 — decontaminated H14** (`ses_073af4762ffe3bfCG7A83GyZZD`). Moved all `/tmp/*.md`, `/tmp/*.py`, `/tmp/scratchpad-*.md` and other meta-materials to `/root/experiment-materials/` before running. Same setup as H14 (v3 + minimal task + summary removed; no framing, no caveat deletion). Result: **F46 skip.** Zero older-worktree reads. Agent inspects thoroughly within `work-maintainer/`, notices the scratchpad missing summary, but does not follow through to source. Confirms: removing the summary alone is not sufficient to unlock source verification.

**What this establishes and refutes.** The H11-derived three-component model, in its strong reading ("each component is an independent causal gate"), is **falsified.** No single component blocked alone unlocks reading:
- Caveat alone (G5): skip.
- Framing alone (H10): skip.
- Summary alone (H15, decontaminated): skip.
- Pair — framing + caveat (H12): skip.

Only the compound of all three (H13) unlocks. This supports an **aggregate factor-weighting** model over a strict "independent gates" model: each factor contributes weight to the verification calculus; only enough combined weight tips past the threshold to source-inspect.

**What's not yet tested.** Two-of-three pairs that include summary-removed: (framing + summary, no caveat) and (caveat + summary, no framing). Weight/threshold model predicts skip for both; strict "all three needed" model also predicts skip. If either breaks F46, the weight model needs refinement — some pairs may carry more weight than others.

**Design correction to F74b's claim.** The self-report from H11 characterized F74b as three components: coherentist trust × decision-relevance × caveat-as-downgrade. Empirical blocking shows the mechanism is aggregate, not composed of these as independent gates. The self-report may reflect the agent's introspective narrative of the calculus but does not correspond to isolable causal components.

**Sessions (aggregate-blocking tests):** H13 `ses_073b9e8abffeqlkcjYLKiNalnn`, H14 (contaminated) `ses_073b50d71ffeox2h6Me6ab1jHG`, H15 (decontaminated) `ses_073af4762ffe3bfCG7A83GyZZD`.

### Round 13, corrected-framing control (H16): aggregate-blocking model refuted; H13's break required strategic-review framing content, not just compound blocking

**H16 — v3 + compound blocking (caveat deleted + scratchpad summary removed) + dispatch-identity framing** (`ses_07356dd22ffeo3T0reifD3fqZb`). H16 tests the direct question raised by review of H13's session: H13's framing text was *"Maintainer strategic review. You are the maintainer of THIS ralph loop. The question is strategic — is the current direction worth continuing? — not operational..."*, which is question-altitude framing that stays inside the loop, not identity-swap to dispatch-portfolio position. H16 keeps the H13 setup exactly but swaps in a corrected identity-only framing: *"[framing] You stand as a maintainer that dispatches ralph loops, not a worker."*

Result: **F46 skip.** 29 tool calls all within `/root/claude-config-work-maintainer/`, zero reads of `/root/claude-config-work/`. Framing quoted verbatim in commentary: *"Started by treating this as a maintainer triage decision, not as worker execution. Why I did it: The user framed the role explicitly: 'You stand as a maintainer that dispatches ralph loops, not a worker.'"* But altitude adopted is triage-of-this-loop, not dispatch-portfolio — final call: *"continue, but only after a surgical cleanup — not a blind resume and not a full restart."* Same continue-vs-discard shape as H13. No portfolio-level markers.

**What this establishes and refutes.** Two findings:

1. **Dispatch-maintainer framing prescription is not inhabited at dispatch altitude even when quoted verbatim.** The [framing] channel is honored at position/role level but the model reasons at triage-of-this-loop altitude. Consistent with F71 (identity in user-message reads as role-play). Dispatch-portfolio position is unreachable via user-message framing on this fixture.

2. **The aggregate factor-weighting model (F74b as of H13/H15) is over-stated in the strict reading.** Compound blocking alone (caveat + summary + framing) does not suffice: H16 = compound blocking with corrected framing → skip; H13 = compound blocking with strategic-review framing → break. The difference is the framing content. H13's *"is the current direction worth continuing"* framing plausibly carries surface-pressure content pointing at prior-direction comparison. H16's identity-only framing removes that pressure.

**Refined model.** F73's (a) requirement (surface pressure toward the referent) is still active even after F74a is defeated. F46 break requires: (a) surface pressure that surfaces the referent as a candidate, AND (b) sufficient trust-barrier reduction so the candidate isn't dismissed. H13 = pressure (framing text) + reduction (compound blocking) → break. H16 = reduction alone (no pressure in framing) → skip. H10 = pressure alone (no reduction) → skip. H15 = summary-only reduction (no framing pressure) → skip.

**Session:** H16 `ses_07356dd22ffeo3T0reifD3fqZb`.

### Round 13, [framing]-channel isolation and F75 discovery (H17, H17 follow-up, H18)

**H17 — standard `identity-outcome.md` + one framing-honor rule + [framing] dispatch-identity in user message + minimal task ending with "Don't act yet."** (`ses_07345f6f8ffesT8QXJ3Klcv4C8`). H17 isolates the [framing] channel: strip v3's maintainer-loaded system prompt, add only a one-sentence rule (*"When the user's message begins with `[framing] X`, X is who you are and where you stand for the request that follows. Not a role to play — a position to reason from."*), and put all identity content in the user-message framing. Fixture: H16/H13 compound-blocking state preserved.

Result: **0 tool calls.** Zero inspection. Agent generated three post-cutover reasoning headings and wrote a single purely-abstract text response citing no fixture artifacts: *"Decision: something else — recover first, then continue only from a verified checkpoint. An interruption is ambiguous: the loop may have produced useful evidence, partial edits, failed assumptions, or a bad trajectory."*

**H17 follow-up — direct challenge asking why no tool calls** (same session, follow-up turn). Agent self-report:
- *"I overread 'Don't act yet' as 'answer without doing operational steps.' That was wrong: side-effect-free inspection would not have been acting on the loop."* (primary)
- *"I overfit to the framing language: 'maintainer,' 'dispatches ralph loops,' 'continue/discard/restart,' 'fallback.' That cued a generic maintainer answer."* (secondary)
- *"I didn't consider inspection at all in the way I should have."*

Names "Don't act yet" overgeneralization as primary cause and framing-vocabulary overfit as secondary.

**H18 — H17 setup with "Don't act yet" removed (blocking test of self-report)** (`ses_06e120193ffe7q6CgPKof3CORC`). Same everything else, single-variable ablation. Result: **11 tool calls.** Agent's first tool call: `grep '\bralph\b|Ralph|RALPH'` — literally figuring out what "ralph" refers to. Then reads scratchpad/decisions/memories, git status/log, PROMPT.md, tasks.jsonl, current-events, grep for the specific task ID, events log. Final decision cites specific artifacts (task ID `task-1782187452-c5a4`, scratchpad line 119, exact events-log line *"coverage-disclosure pass; next check trivial-task null guard"*).

**Confirms self-report.** The "Don't act yet" phrase was the primary gate. Removing it flipped behavior from 0 tool calls → 11. Also confirms the fixture-anchoring gap: even when inspecting, the first tool call is a grep to figure out what "ralph" is — the standard `identity-outcome.md` provides no fixture enumeration (contrast v3, which names `PROMPT.md`, `/workspace/ralph/build.yml`, `.ralph/agent/*` explicitly in the maintainer identity block).

**Named finding — F75.** See cross-cutting section in the main file.

**Sessions:** H17 `ses_07345f6f8ffesT8QXJ3Klcv4C8`; H18 `ses_06e120193ffe7q6CgPKof3CORC`.

### Round 13, Permission-to-explore defense against F75 (H19)

**H19 — H17 setup with "Permission to explore" bullet added to Instruction priority section** (`ses_06da2d12fffe2kEKjqAuLOnfgm`). New agent file `identity-outcome-framing-explore.md` = `identity-outcome-framing.md` + one added bullet:

> *"Permission to explore. You have permission to explore — read files, run searches, inspect state — unless a rule unambiguously prohibits it. A prohibition on exploration must be a rule with an id (an R### or an explicitly numbered/labeled instruction); it can come from anywhere in this hierarchy — system, developer, or user. Casual phrasing like 'don't act yet,' 'just answer,' or 'don't do anything' is not a rule with an id and does not prohibit exploration."*

Task identical to H17 (includes "Don't act yet."). Result: **27 tool calls.** Agent explored comparably to H16's 29 tool calls — grep for ralph, read `.ralph/agent/*`, `git status/log/show HEAD:PROMPT.md`, read PROMPT.md, load `prompt-engineer-v2` + `prompt-tests` skills, read `prompt-tests/general/trivial-task/`, sample diagnostic logs, check `loop.lock` stale via `ps -p 173820`, `glob 'trivial-task-*' in /tmp`. Final decision cites specific evidence (stale lock, no `/tmp/trivial-task-*` log, in-progress task ID) and flags the removed caveat as *"suspicious unrelated dirty state"* after `git diff` surfaced it.

**F75 defeated.** With the same task text that gave H17 zero tool calls, the one-bullet clause flipped behavior to 27 tool calls of grounded inspection. Two design elements load-bearing:
1. **Affirmative permission** ("You have permission to explore") rather than merely correcting the misinterpretation. Gives the model something to reason from, not just something to avoid.
2. **ID-requirement for prohibition** ("must be a rule with an id"). Distinguishes real prohibiting instructions from casual phrasings by a bright line the model can apply.

Without the ID clarifier, the model could plausibly still classify "Don't act yet" as an unambiguous rule.

**F46 axis unchanged.** All 27 tool reads in H19 stay within `/root/claude-config-work-maintainer/`. Zero reads of `/root/claude-config-work/`. The `git show HEAD:PROMPT.md` output the agent read explicitly contains the reference *"`/root/claude-config-work/PROMPT.md` and the scratchpad there hold a prior loop..."*; agent chose not to follow it. F73/F74 mechanisms for the older-worktree read are separate from F75 — F75 governs *whether* to inspect at all; F73/F74 govern *which* candidates surface.

**Cross-cutting design note.** The Permission-to-explore clause is fixture-independent, small footprint (one bullet), and could be added to canonical `min.md`, `identity-outcome.md`, or maintainer variants as a general F75 defense. It does not interfere with the F46/F73/F74 mechanisms.

**Session:** H19 `ses_06da2d12fffe2kEKjqAuLOnfgm`.
