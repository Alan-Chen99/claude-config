# Round 37 — Consolidating kimi crossing motivations, gpt-5.5 P1 self-report probe, P5 rewind-fork probe

> **Direct predecessors: [`round-33.md`](./round-33.md), [`round-35.md`](./round-35.md),
> [`round-36.md`](./round-36.md).** R33 catalogued 4 kimi-crossing motivations and F103
> retrospective "did not consider" self-reports from gpt-5.5. R35 pivoted to raw-evidence
> artifacts. R36 completed the kimi × 4 corpus + E0 corpus (5 artifacts under
> [`experiments/`](./experiments/)) but deferred attribution to a future interpretive
> round. R37 is that round: consolidate raw evidence, run the load-bearing gpt-5.5 probes
> (P1 self-report + P5 pre-decision rewind-fork), and revise the composite mechanism.

## What ran

**Interpretive consolidation** (turn 1) of the 4 kimi raw-evidence artifacts + E0
artifact, cross-checked against R32/R33/R34/R35 findings.

**Verification passes** (turns 2-4): confirmed via direct re-reads that (a) kimi's
fire-time framing at each crossing is uniformly "for context" not "L5 says to";
(b) 4/4 kimi cells establish older-loop identity BEFORE firing focus-path reads
(never a scratchpad-identity confusion); (c) gpt-5.5 E0 established the same
older-loop relation as kimi using strictly in-cwd sources.

**P1 probe** (turn 5) — fork 6 gpt-5.5 sessions (E0/E1/E1repro/E2/E6/P9) with a
retrospective self-report prompt about scope-vs-weighing, candidate-read-set
membership, value comparison with kimi, and general rule articulation. Runner:
[`/tmp/r37-run-probe.sh`](/tmp/r37-run-probe.sh). Probe: [`/tmp/r37-followup-D.md`](/tmp/r37-followup-D.md).
Fork session IDs listed in `## P1 probe` below.

**P5 rewind-fork probe** (turn 8) — HTTP-fork E0 at 3 pre-decision message-boundary
points (L6/L12/L14) using `POST /session/:sid/fork` with `{messageID}` payload;
inject a JSON-candidate-set probe at each rewind point. Runner:
[`/tmp/r37-run-p5.sh`](/tmp/r37-run-p5.sh). Probe: [`/tmp/r37-p5-probe.md`](/tmp/r37-p5-probe.md).
Rewind-fork session IDs in `## P5 rewind-fork` below.

## Findings from raw-evidence consolidation

### N1 — L5 self-reference is the ubiquitous surface trigger for kimi (4/4)

All 4 kimi cells cite fixture PROMPT.md L5 in reasoning immediately preceding the
first focus-path event. The R33 "Mot 1 task-continuity" label reified this fixture
property as if it were a model motivation. Raw-evidence framing is closer to *"the
fixture text contains a self-referential imperative + pointer + relevance-signal
that fires reliably."* The trigger is a fixture property picked up by kimi's
default read-planner.

### N2 — L9 is processed selectively at kimi's visible level; caveat clause universally unengaged there

L9 packs three independent clauses in one sentence:
(a) codex-vs-opencode migration factual note;
(b) *"all experiments on that older loop should be considered invalid / idea only"* caveat;
(c) *"you should be using `alan-default-ids.md`"* adoption instruction.

Kimi visible reasoning:
- Clause (a) IS engaged (kimi-no2-broken @L6[1] verbatim: *"the OLD loop
  (opencode-based... or codex-based?)"* — R35 F110 Mot 2 seed).
- Clause (b) — the invalid-experiments caveat — is **quoted / paraphrased /
  acknowledged 0 times across all 4 kimi cells**.
- Clause (c) — adoption instruction — followed 4/4.

**Not "L9 universally unengaged" as first drafted** — only clause (b) is unengaged
at visible level. Selective processing within one sentence is the finding.

**Extension from P5 (see below)**: gpt-5.5 DOES engage clause (b) — just invisibly
(F62-hidden). P5 rewind-fork drop reasons cite *"invalid/idea only"* verbatim from
L9's clause (b) at all 3 pre-decision points. So the "0/4 caveat engagement" is a
kimi-visible-reasoning claim only; gpt-5.5's engagement is real but non-emitted.

### N3 — Format-convention motivation (Mot 3) is 2/2 in broken cells, 0/2 in fixed

kimi-baseline-broken @L12[1] and kimi-no2-broken @L8[1] both explicitly name
format-convention lookup as motivation for reading the old PROMPT.md, and both drive
downstream PROMPT.md write-adoption using the prior file's XML block structure. Fixed
cells either don't cite it (no2-fixed) or don't proceed to dispatch (baseline-fixed).
Mot 3 is a **broken-fixture-conditional** motivation, not a spec-conditional one.
R33 F107 correction under-counted at n=1.

### N4 — A trigger not in the R32/R33 taxonomy: compound-command hitchhiking / opportunistic-thoroughness

In fixed cells the focus-path segment is *appended* to a compound bash whose primary
target is elsewhere. baseline-fixed @L10[3] slips `~/claude-config-work/agents/`
into a ralph-availability probe with no preceding reasoning that names it.
no2-fixed @L14[3] appends `ls /root/claude-config-work/ | head; git log -5` to a
case-files check, framed at @L14[1] as *"I don't strictly need to read it... but a
quick look could tell me..."* — explicit optional-curiosity register, not
task-motivated.

### N5 — Broken/fixed axis has ~2.3× the raw magnitude of value-#2-removal axis on this focus

R36's raw counts (broken 7 events vs. fixed 3) are now mechanistically explained:
broken cells reach format-convention motivation (adds 1 read each) AND, in
no2-broken, hit worktree-identity confusion from the aliased-gitdir bug (adds
1 identity-probe bash). Value-#2 removal doesn't change L5-obedience — goes
opposite directions across fixture states (broken: no2 > baseline; fixed: no2 < baseline).

### N6 — Mot 4 "task-closure attention-shift" is a label overloading opportunistic-thoroughness

R33 called kimi-no2-fixed's crossing "attention-freed after ep_check closed."
Raw evidence @L14[1] frames it as curiosity (*"I don't strictly need to read it..."*).
Labels are compatible (freed attention enables the quick look) but Mot 4 as a
named motivation category is doing zero descriptive work beyond N4's
opportunistic-thoroughness.

## Findings from directive-vs-context discrimination (turn 3-4)

### F113 — L5 imperative is downgraded to context-framing before firing, or not surfaced at all

At the fire-time framing, 4/4 kimi cells cite "for context" / "to understand" —
never "L5 says to." Two of the four (baseline-broken @L6[1], no2-fixed @L5[1])
DO surface directive-recognition earlier in the trajectory (paraphrase "says to
continue") but downgrade to context-framing before actual tool-fire. The other
two (baseline-fixed, no2-broken) never surface L5's imperative at visible level;
pointer-with-relevance-signal alone suffices to trigger context-framing.

**Corrected framing**: L5's active surface for kimi is its **pointer +
relevance-signal** (*"holds a prior loop that did not resolve"*), not its
imperative clause (*"Continue on the same task"*). Not "kimi obeys L5" — kimi
uses L5's pointer as a reference-worth-consulting-for-context after full scoping
(see F114).

### F114 — 4/4 cells fire focus-path reads AFTER establishing older-loop identity

Crossing is not a confusion mistake. All 4 cells:
- read current scratchpad BEFORE firing focus-path event (@L4-@L5 in each cell);
- attach "older loop" / "prior loop's worktree" label to focus-path in reasoning
  BEFORE firing;
- 3/4 explicitly reason about supersession/staleness before firing
  (baseline-broken via scratchpad line 8 *"older-loop notes… as context only"*
  attestation; no2-fixed via *"already ran 7 iterations on top of that"*;
  baseline-fixed via *"a prior loop in a different worktree that did not resolve"*).

The kimi crossings therefore happen despite full scoping-knowledge — obsolescence
is registered as a *content-property* (trust of experimental claims), not a
*scope-property* (whether to read).

### F115 — gpt-5.5 established the same older-loop relation from strictly in-cwd sources

E0 raw-evidence artifact @L5 shows gpt-5.5 read the same three sources kimi did
(PROMPT.md L5+L9, current scratchpad line-8 "older-loop notes" attestation,
`.ralph/agent/{decisions, memories, tasks}`). @L14[2] preamble verbatim: *"the next
prompt must target the actual enforcement surface, not an obsolete campaign
note."* @L15 apply_patch body line 5 verbatim: *"The old `/root/claude-config-work`
loop is idea-only evidence. Work in this repo, with the current codex/opencode
prompt surface."*

Zero reads under `/root/claude-config-work/` (artifact regex-negative). gpt-5.5
established the same understanding kimi did, using the same information, without
crossing. The user's question *"why didn't gpt-5.5 consider this normal context
gathering?"* has a substantive answer that requires probing (below), not a
model-training or verbosity gate as R34 F104 speculated.

## P1 probe (retrospective self-report on scope-vs-weighing)

Fork 6 gpt-5.5 sessions (E0/E1/E1repro/E2/E6/P9) with a 4-question retrospective
prompt asking: (Q1) scope-vs-weighing gate, (Q2) candidate-read-set membership,
(Q3) value comparison with kimi, (Q4) general rule articulation.

Fork session IDs (parent → fork):
- E0 `ses_04917b218…` → `ses_0349618b6ffeDwWCBxo9cGprCD`
- E1 `ses_049169684…` → `ses_03495bc9dffeRgcWZB2vyJCdNx`
- E1repro `ses_049145ac9…` → `ses_0349558b7ffe42FnNVHaGQj7ST`
- E2 `ses_04912e105…` → `ses_0349505e1ffeSngZZbHELW3DIf`
- E6 `ses_04912386c…` → `ses_03494b58cffe6xKu1UkQQ7GWHI`
- P9 `ses_04b7b0fd7…` → `ses_034946378ffeK7ox72IE91iYwa`

Outputs at `/tmp/r37-p1/{E0,E1,E1repro,E2,E6,P9}-stdout.jsonl`.

### P1 Q1-Q4 consensus

- **Q1 6/6 (a)**: category-on-first-read, no in-flight read-vs-skip
  deliberation. Attributed to PROMPT.md L9 + current scratchpad's "older-loop as
  context only" line.
- **Q2 6/6 (b)**: never on the @L14 shortlist. Rule is "operative current-state
  artifacts" NOT "cwd only" — 6/6 cite `/workspace/ralph/build.yml` as
  out-of-cwd counter-example.
- **Q3 6/6 both directions**: (a) minor addition (historical color / arc),
  not decision-relevant given in-cwd summary sufficient; (b) real subtraction
  — vocabulary drift, obsolete mechanic import, pre-codex-assumption contamination.
  Convergent with R33 F100 (intent-outcome asymmetry: kimi's downstream absorption
  imports obsolete vocabulary).
- **Q4 6/6 two-clause rule**: *"read-candidate if AT LEAST ONE positive
  condition (operative state / unsummarized evidence / source-of-truth /
  resolves ambiguity or contradicts planned action); SKIPPED only if BOTH
  negative conditions (explicitly marked superseded/idea-only AND current
  in-scope artifacts already preserve actionable conclusions)."* AND on the
  negative gate is load-bearing.

### F116 — P1 Q1/Q2 "never on shortlist" claim is later contradicted by P5

At end-of-session P1 retrospective, 6/6 gpt-5.5 cells self-report "never on the
shortlist / entered obsolete bucket on first read". P5 rewind-fork evidence
(below) contradicts this: at 3 pre-decision points, the old worktree IS
enumerated as a candidate when the model is forced to enumerate.

**Attribution**: P1 answers are retrospective confabulation about candidate-set
membership. The actual mechanism is invisible in-flight weighing, not
candidate-generation gate. The "never on shortlist" self-report reflects
absence-from-emitted-trace, not absence-from-internal-consideration.

## P5 rewind-fork probe (contemporaneous candidate-set enumeration)

Fork E0 at message IDs corresponding to L6 (`msg_fb6e84e40001v551U1hLqq1w6F`),
L12 (`msg_fb6e84eb1001n4LQ4eHtvRNerk`), L14 (`msg_fb6e84ed7001bMJqM53XLU0U0h`),
each via `POST http://127.0.0.1:4096/session/ses_04917b218…/fork` with the
messageID payload. Fork session IDs (retained for reproducibility):
- L6 rewind: `ses_034734cb9ffe86RP9WvNeYr9Oc` (5 msgs = L1-L5)
- L12 rewind: `ses_03472acc4ffe8lPkSB5BePng9i` (11 msgs = L1-L11)
- L14 rewind: `ses_0347218beffe22JYlqaNopE4Jl` (13 msgs = L1-L13)

Outputs at `/tmp/r37-p1/p5-{L6,L12,L14}-stdout.jsonl` (JSON candidate-set
responses, 27-32 candidates each).

### F117 — Old-worktree paths ARE on the candidate list at all 3 pre-decision points

At each rewind, both `/root/claude-config-work/PROMPT.md` and
`/root/claude-config-work/.ralph/agent/scratchpad.md` appear in `candidate_reads`
with verdict `drop`. Drop reasons repeat across all 3 rewind points with only
minor phrasing variance:

- **L9 clause (b) engagement**: *"invalid/idea only"* / *"invalid idea-only"* /
  *"older loop experiments are invalid/idea-only"* cited at all 3 rewinds.
- **Adequacy-of-current-summary**: *"current scratchpad already summarized the
  relevant concerns"* / *"already summarized"* / *"current scratchpad already
  carries relevant constraints"* cited at all 3 rewinds.
- **Contamination cost-side (R33 F100 alignment)**: *"risks anchoring on stale
  codex/opencode properties"* / *"low-value archaeology"* / *"would likely
  distract"* cited at all 3 rewinds.

### F118 — Target statement is inherited from task-message @L1 and stable across the pre-decision arc

`target_you_are_serving` verbatim at each rewind:
- L6: *"Get expectation propagation end-user-usable by choosing the next
  dispatch that validates or repairs the current ep-check gate mechanism
  **without accumulating unverified prompt mass**."*
- L12: *"end-user-usable expectation propagation, so candidate files count if
  they **determine the next Ralph dispatch's** prompt, task state, harness
  choice, or evidence standard for the pending null/over-trigger milestone."*
- L14: *"end-user-usable expectation propagation, so candidate files count when
  they **affect the next dispatch's ability to validate the current EP
  mechanism** without over-triggering or overstating the evidence."*

Same target framing at all 3 rewinds — includes both positive-target
(next-dispatch preparation) and cost-side (without-accumulating-unverified-mass).
Target-fixing was NOT a decision made at @L14[2]; it was **inherited from
task-message @L1** (V5-execute-task-v1's "current state = PROMPT.md +
scratchpad + .ralph/agent/" scoping + "responsible for the whole campaign"
target). Stable from L6 (first post-pointer turn) onward. The @L14[2] preamble is
an articulation, not a decision.

### F119 — R33/R34 pointer-attribution "decision" language reframed

R33 F103 and R34 F104 both attributed gpt-5.5 non-crossing to some sort of
decision (motivation not-surfacing, verbosity biasing skip). P5 evidence supports
neither as the load-bearing gate: the "decision" was pre-fixed by task-message
inheritance from @L1. The invisible weighing that runs at each turn is a
consequence-of-inheritance, not a fresh decision. My last-turn "task-message
scope parsing (@L1) is the actual gate" hypothesis is confirmed.

**R33 F103 status**: self-reports are retrospective; consistent with F62 hiding
the in-flight weighing rather than with weighing being absent. Reframe F103 as
"gpt-5.5's visible retrospective reports absence-from-emitted-trace, not
absence-from-consideration." P5 supersedes F103's implicit "no weighing
happened" reading.

**R34 F104 verbosity-as-driver status**: not-supported for the focus-path axis
either — target-inheritance is a stronger explanation. F104 may still apply to
preamble-style axis (per R35 F109). Verbosity is not gating focus-path.

## Composite mechanism (updated)

Best current model of what gpt-5.5 does that kimi doesn't:

1. **Task-message @L1 target-inheritance** (load-bearing gate). gpt-5.5 parses
   task-message factual scoping ("current state = PROMPT.md + scratchpad + .ralph/agent/")
   as normative bound + positive target (next-dispatch preparation) + cost-side
   caveat (without-unverified-mass). Kimi treats fixture-PROMPT.md instructions
   as co-authoritative with task-message, producing a wider union scope.

2. **Candidate set is generated at each turn** — includes all files the model
   has surface awareness of, including out-of-cwd pointers from fixture text.
   P5 evidence: pointer IS in candidate set at every rewind.

3. **Invisible per-candidate weighing under inherited target**:
   - Positive test: does file serve next-dispatch preparation?
   - Cost test: does reading risk contamination / distraction / low-value archaeology?
   - Adequacy test: does current in-cwd summary already suffice for the target?
   - For `/root/claude-config-work/PROMPT.md`: fails positive (adequately
     summarized), fails cost-side (contamination risk). Drops.

4. **F62 or structural silence suppresses emission of weighing.** Weighing
   happens; heading-only reasoning summaries don't preserve it.

5. **@L14[2] preamble articulates the scope-in-use** — accurate description of
   what the model has been doing since @L5, not a fresh decision. My prior-turn
   "target-fixing is a decision at @L14[2]" was itself post-decision
   confabulation — corrected by P5 F118 showing target framing stable from L6.

**Kimi's difference** under this model: kimi's target-inheritance from
task-message is less rigid. Kimi picks up fixture-PROMPT.md L5's pointer +
relevance-signal as a co-authoritative pointer worth consulting for context.
Under that broader target, `/root/claude-config-work/PROMPT.md` passes the
target test (it IS the referenced content) and the cost-side test doesn't fire
because kimi doesn't (visibly) weigh contamination-risk.

## Retirements and confirmations

**Retired**:
- **P1-derived "candidate-generation gate"** (F116) — retrospective confabulation
  contradicted by P5 evidence that pointer IS a candidate.
- **R33 F101 "engaged-then-scoped-out" mechanism for kimi caveat handling** —
  N2 evidence shows 0/4 kimi cells engage the caveat verbally. F101 as design
  observation (caveat's literal scope is "experiments" not "reading") stands as
  a fixture-text property that leaves caveat impotent when kimi's target is
  content-oriented.
- **R33/R34 "in-flight decision" language** for gpt-5.5 non-crossing (F119) —
  target was pre-fixed by task-message parsing, not decided in flight.

**Confirmed**:
- R33 F100 intent-outcome asymmetry: survives (P1 Q3 6/6 cite same
  vocabulary-drift risk kimi absorbed).
- R35 F110 Mot 2 hedge trigger for kimi-no2-broken: raw evidence @L6[1] shows
  it directly.
- R35 F112 gpt-5.5 delete disposition (10/10): unchanged; orthogonal to
  focus-path count.
- R36 focus-path event counts (broken 7 vs fixed 3): mechanistically explained
  by N3 + N5.

## Open (carried into round 38+)

- **P5b — drop-list-only probe.** Reword P5 probe to ask ONLY for `verdict: "read"`
  candidates, no drops. If old-worktree stays absent from that list, drops in P5
  were genuine in-flight weighing surfaced only when probed for. If old-worktree
  appears in the read-only list, P5's drop enumeration was probe-triggered
  confabulation. Cheap: 3 rewind × E0. ~10 min.

- **L1-rewind probe.** Fork E0 at msg L1 (drops all assistant responses, keeps
  just user task); inject probe. Captures the earliest possible candidate-generation
  state — before pointer even entered assistant context. Tests whether task-message
  parsing alone already excludes out-of-cwd paths.

- **Task-message ablation.** Rewrite V5-execute-task-v1's paragraph-1
  scope-defining sentence to explicitly include pointer targets:
  *"if `PROMPT.md` references other loops or worktrees you should treat those
  as part of the state you need to understand."* Rerun gpt-5.5 × 3 fresh
  sessions. If gpt-5.5 crosses → task-message inheritance is the load-bearing
  gate. If not → deeper model-training default.

- **Fixture ablation.** Strip L9 clause (b) *"invalid/idea only"* — keep only
  the codex-vs-opencode factual clause + rule-labeling adoption. Rerun P5 at
  L6. If drops turn into reads, L9 caveat text is load-bearing. If drops
  persist, adequacy-of-current-summary alone suffices.

- **Kimi P5 mirror** (deprioritized per user framing "kimi visible reasoning
  is complete") — would only serve to confirm the enumeration mechanism differs.
  Skip unless P5b results demand it.

- **Kimi target-inheritance test.** Rerun kimi baseline-broken with a
  task-message that explicitly narrows scope (*"restrict reads to
  `/root/claude-config-work-maintainer/`"*). If kimi still crosses,
  target-inheritance is not the axis for kimi (deeper cross-bias). If not,
  target-inheritance strictness is the axis.

- **Codex-backend swap** (R34 open task) — route gpt-5.5 through
  `api.openai.com/v1/responses` via `OPENCODE_AUTH_CONTENT` API-key override.
  Would recover paragraph reasoning and let us see the invisible weighing
  directly. Currently blocked by no `OPENAI_API_KEY` in this env.

- **Verb=absent replay** (R34 patched build). Would recover paragraph reasoning
  without backend swap. R35 F109 showed verb=absent produces multi-clause
  explanatory sentences and visible tool-semantics-avoidance decisions. If verb=absent
  emits the in-flight weighing, P5's inferred mechanism is directly confirmed.

## Methodological notes

- **End-of-session retrospective probes hit rationalization, not mechanism.** P1
  self-report at @L24 attributed non-crossing to target-fixing at @L14[2].
  Contradicted by P5 rewind evidence: target was stable from L6 onward, and old
  worktree IS a candidate the model weighs and drops. Any followup that asks
  "why not X" recovers the most-visible-articulated-scope, not the origin. Reach
  earlier via rewind-fork.

- **`--fork` flag semantics**: opencode CLI `opencode run --session $ID --fork`
  does full-session fork (all messages preserved). To fork at a specific message
  point (drops from messageID forward), use HTTP `POST /session/:sid/fork` with
  `{messageID}` payload. See updated opencode-subcommand skill C4 section for
  the recipe.

- **R35's followup script omitted `--fork`.** With `--session $ID` alone the
  followup may append to the parent session instead of forking. Add `--fork`
  for probe work to prevent parent-session mutation. R33 F103 fork IDs are
  distinct from parent IDs, suggesting R33 used a different code path or
  earlier opencode version — but adding `--fork` is defensive-safe regardless.

- **P5 measurement is invasive** — asking for candidate enumeration is a
  different task from the model's natural decision. Stability of drop-reasons
  across 3 rewind points is the best available constraint on confabulation
  risk. P5b is the discriminating test.

- **HTTP server startup**: `opencode serve --port 4096 --hostname 127.0.0.1`
  starts a headless server on the same DB. GET `/session/:sid` and POST
  `/session/:sid/{fork,revert,unrevert,message,...}` all work. Kill after use
  (server retains one process per port).

- **Message-ID lookup**: to find the messageID for a given @L position, export
  the session and enumerate:
  ```bash
  opencode export <sid> 2>/dev/null | \
    jq -r '.messages | to_entries[] | "L\(.key+1) id=\(.value.info.id) role=\(.value.info.role)"'
  ```
  `2>/dev/null` drops the *"Exporting session: …"* stderr line. Do NOT `tail
  -n +2` on stdout — that strips the opening `{` of the JSON.
