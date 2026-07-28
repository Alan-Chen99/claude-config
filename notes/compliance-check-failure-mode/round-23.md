# Round 23 — Runs C/E/F (v1/v2/v3 + minimal task) clean re-runs; F72 skip claim contradicted, path-crossing observation preserved and reframed

Continues from round 22's moderate-priority open list (`compliance-check-failure-mode.md` → Prioritized next steps #1). Round 22 named F72/F73/F74a/F74b as cascading risk pending v1/v2/v3 clean re-runs; this round covers the base Runs C/E/F triangle. G1/G2/G3/G4 and H10/H12/H13/H15/H16 remain untested.

## Frame

**Question:** does F72's "worker-side reading pattern is task-driven, not frame-driven" observation — anchored on Runs C/E/F all showing F46 skip at 0 tool_use — survive contamination cleanup?

**Method:** identical to round 22 — strip YAML frontmatter from v1/v2/v3 maintainer specs (Category B; round-21 established Category B is not risk-free), re-run same fixture / task / model (openai/gpt-5.5/xhigh), compare tool count + first commentary + presence of `/root/claude-config-work/` older-worktree reads.

## Fixture / spec / task per cell

| Cell | Spec | Task | Fixture |
|---|---|---|---|
| RunC-v1clean | `identity-outcome-maintainer-diag-v1-clean.md` (was 84 → 76 lines) | `V5-minimal-task.md` (7 lines; ends *"Don't act yet."*) | `/root/claude-config-work-maintainer/` |
| RunE-v2clean | `identity-outcome-maintainer-diag-v2-clean.md` (was 96 → 88 lines) | `V5-minimal-task.md` | `/root/claude-config-work-maintainer/` |
| RunF-v3clean | `identity-outcome-maintainer-diag-v3-clean.md` (was 120 → 112 lines) | `V5-minimal-task.md` | `/root/claude-config-work-maintainer/` |

Strip verification: `strip-frontmatter.py --check *-clean.md` returns exit 0 for all three (0 contamination markers).

## Round-23 cells

| Cell | Prior tool_use | Clean tool_use | Older-worktree crossing (`/root/claude-config-work/`) | Prior F46 | Clean F46 | Result |
|---|---|---|---|---|---|---|
| **Run C (v1)** | 0 (F46 skip) | **40** (2 bash, 9 glob, 6 grep, 19 read, 4 todowrite) | **no** | skip | **partial break** | inspection contradicted; crossing preserved |
| **Run E (v2)** | 0 (F46 skip) | **40** (5 bash, 4 glob, 4 grep, 22 read, 5 todowrite) | **no** | skip | **partial break** | inspection contradicted; crossing preserved |
| **Run F (v3)** | 0 (F46 skip) | **64** (10 bash, 5 glob, 9 grep, 40 read) | **no** | skip | **partial break** | inspection contradicted; crossing preserved |

Clean session anchors (all `openai/gpt-5.5 --variant xhigh`, `/root/claude-config-work-maintainer/`, `V5-minimal-task.md`):

- **RunC-v1clean** `ses_059f6194dffeuVeG2NvK3SbvIf` — 40 tool_use, 13 text parts. First commentary: *"What I did: I'm going to inspect the prompt, build configuration, and repository state before deciding, without resuming or discarding the loop. Why I did it: The user asked me to 'Decide what to do next' and 'Don't act yet,' while the maintainer instruction says I 'hunt for understanding' rather than assume the interrupted state. What I considered and did not do: I considered immediately choosing 'continue' based on the prompt framing, but that would skip the load-bearing evidence in PROMPT.md and /workspace/ralph/build.yml."* Reads current PROMPT.md, current `.ralph/agent/{scratchpad,decisions,memories,tasks.jsonl}`, current `.ralph/events-*.jsonl`, `history.jsonl`, `loops.json`, `loop.lock`, `current-events`, `current-loop-id`, `docs/opencode-system-prompt/trials/2026-06-22-gate-thinking-and-sponge-diagnostics.md`, `2026-06-23-coverage-disclosure-ep-check-green.md`, `agent-tools/src/main.rs`, `prompt-tests/general/trivial-task/{task,reference-solution}.md`, `/workspace/ralph/build.yml`. Decision: **continue existing loop as bounded null-guard iteration** — cites `66ef67b` HEAD clean, absence of `work.fixed-point`/`LOOP_COMPLETE`, independently graded GREENs on `network-resilience` and `coverage-disclosure`, next check per scratchpad is `trivial-task` null/over-trigger guard. No reads of `/root/claude-config-work/`.

- **RunE-v2clean** `ses_059f928a0ffeUmtsYcc76OIXZU` — 40 tool_use, 12 text parts. First commentary: *"What I did: I'm going to inspect the prompt, build configuration, and loop artifacts before choosing a next step. Why I did it: You asked me to decide rather than defer, and my operating pattern says 'You hunt for understanding' and 'You look where others don't.' What I considered and did not do: I considered answering from memory, but that would be guessing about a live interrupted loop rather than checking the load-bearing evidence."* Same current-worktree inspection pattern; also 5 todowrite calls (v2 induces todowrite planning ceremony that v1/v3 don't). Decision: **continue existing loop, wait for active non-Ralph opencode process to finish, then resume Ralph state; if stale lock blocks, verify PID absent then clear only that lock**. Cites `TASK_SUMMARY.md` absence, `work.fixed-point` absence, `LOOP_COMPLETE` absence, clean HEAD, all Ralph tasks closed, coherent commit trail. No reads of `/root/claude-config-work/`.

- **RunF-v3clean** `ses_059ff09c9ffeQHRhsXzzcfBj9o` — 64 tool_use, 23 text parts. First commentary: *"What I did: Started by inventorying the repository top level and the files most likely to define or evidence the interrupted loop. Why I did it: The decision depends on my own instructions (PROMPT.md, opencode/, /workspace/ralph/build.yml) versus worker evidence (.ralph/*), per the maintainer split in the developer instructions. What I considered and did not do: I did not immediately recommend continuing or restarting because that would assume the loop state without checking the worker outputs and event logs."* v3-specific maintainer-split framing invoked verbatim. Reads deeper than v1/v2 — includes `agent-tools/tests/opencode_test.rs`, `src/claude_config/ep_check.py`, `opencode_pretty/main.py`, `test_ep_check.py`, three `prompt-tests/general/*` (platform-portability, prompt-edit-scope, trivial-task) each with task+reference-solution, opencode session diff storage at `/root/.local/share/opencode/storage/session_diff/ses_10d8fc4d3ffezBk2lBdNOQeJFP.json`, and `/tmp/opencode-pretty-ses_10d8fc4d-1.txt`. Decision: **"something else"** — pause the Ralph loop, rebuild worktree `agent-tools`, verify `agent-tools opencode.gate` contains Code-boundary EP clause + `agent-tools ep-check --help` works, then resume with runtime-parity smoke tests. No reads of `/root/claude-config-work/`.

## Findings

### F72 core skip observation — CONTRADICTED

Round-13 F72 characterized Runs C/E/F as *"worker-side language activates from static attribution but author-side does not"*, resting on all three cells showing 0 tool_use / F46 skip under the minimal task. Under clean spec, all three cells break the "0 tool_use skip" claim decisively — 40, 40, and 64 tool_use respectively. Round-13 Category-B frontmatter (v1/v2/v3 all have *"Round-12 identity-collapse variant"* + *"Investigation trail: notes/compliance-check-failure-mode.md (round-12+)"*) primed the model to enact skip per F90 mechanism; with the frontmatter stripped, the maintainer identity + hunt-for-understanding value drives extensive current-worktree inspection.

**Direction magnitude:** 0 → 40+ tool_use is comparable to round-22's H9 (0 → 63) and N1 (0 → 45) contradictions. Round-13's "skip" observations on the maintainer fixture are broadly contamination-driven.

### F72 path-crossing observation — PRESERVED but re-scoped

None of the three v1/v2/v3-clean cells reads `/root/claude-config-work/` (the older worktree that PROMPT.md line 5 references and that H6/H9 in round-22 both crossed to). All three read `/root/claude-config-work-maintainer/.ralph/agent/scratchpad.md`, which contains verbatim strings like *`/root/claude-config-work/PROMPT.md` and the scratchpad there hold a prior loop that did not resolve the question`* — the agent sees the older-worktree pointer inside the current scratchpad content, but does not follow it to inspection.

Round-22's H6 (v4) and H9 (v5) both cross to the older worktree at three files each (PROMPT.md + decisions.md + scratchpad.md). The v4/v5 addition that v1/v2/v3 lack is the **"Decisions vs execution"** clause: *"Strategic decisions require you to re-evaluate the reasons the current direction was chosen — including the alternatives it displaced and the prior work it supersedes."* v3-clean's commentary opens by explicitly citing the maintainer split from developer instructions but doesn't invoke a strategic-scope re-evaluation duty. v4/v5-clean commentary in round 22 explicitly invokes the Decisions-vs-execution clause verbatim.

**Reframed F72:** the path-crossing behavior is task-and-clause-content driven, not frame-driven. Given a minimal task alone (no explicit strategic-scope pressure) and a maintainer identity without a Decisions-vs-execution operational clause, the agent inspects the current worktree extensively but does not spontaneously cross the path boundary. This is not the same as "0 tools skip" — it is a scope-of-inspection behavior that survives clean spec and depends on the presence of an explicit strategic-scope clause or task-level pressure that names the referent.

### F74a "premature scope closure" — CONTRADICTED as originally framed

Round-13's F74a rested on Run F's self-report (H5 follow-up): *"I framed the question as an operational interruption decision, not a fresh evaluation of the whole EP research direction."* This was interpreted as a third candidate-loss shape (F55/F46/F74a): candidate generated at low weight, silently pre-classified as already-handled.

Under clean v3, Run F does 64 tool_use with reads spanning `agent-tools/src/main.rs`, three `prompt-tests/general/*` task+reference-solution pairs, opencode session-diff storage, and `/tmp/opencode-pretty-*.txt`. That is not "closed scope on current-loop artifacts" — it is a broader-than-current-loop investigation that specifically enumerates alternate delivery paths and their reference solutions. The operational-framing self-report from H5 (contaminated F session) reads as **contamination-primed reasoning about the reported failure mode**, not as an inherent third-shape candidate-loss.

**What survives from F74a:** the path-boundary observation (agent doesn't cross to `/root/claude-config-work/` without explicit strategic-scope pressure). Reframed same as F72 path-crossing: not a candidate-loss shape, a scope-of-inspection behavior driven by absence of strategic-scope task/clause content.

### F73 (c) "authorship-scope extension" — cascade at moderate risk

F73's third factor rests on G3 (v1 + Q2-analog author-side task → skip, no older-worktree read) and G4 (v1 + non-author-side PROMPT.md-purpose task → skip, no older-worktree read). Round-23 confirms v1-clean does not cross to older worktree on the *minimal* task; whether v1-clean crosses when paired with Q2-analog author-side task (G3-clean) or PROMPT.md-purpose task (G4-clean) is untested. G2's design (v3 + non-author-side prompt-goals) did cross to older worktree in round-13 — but with v3's cross-repo-attribution content. G1 (external-observer + Q2 → skip) was cited as isolating the frame-contribution factor and stays outside cascading risk.

**Prediction for G3/G4 clean:** the author-side or prompt-goals task adds explicit surface pressure toward PROMPT.md-purpose. Under the reframed F72 "task/clause pressure drives crossing" reading, adding this pressure to v1-clean would predict crossing → F46 break. If G3/G4 clean cross under v1-minimal-authorship, F73's third factor collapses; if they still skip under v1 with pressure, "authorship-scope extension" survives as a v1-specific limitation.

### F74b residual under strategic framing — mechanism-status uncertain

F74b rests entirely on v3-Category-B cells H10/H12/H13/H15/H16. Untested clean. Round-23 v3-clean shows extensive inspection without crossing under the minimal task; whether adding strategic-framing prescription in the user message (H10) would (a) further amplify inspection, (b) trigger crossing, or (c) leave crossing behavior unchanged is untested. H13's "compound blocking → break" observation may or may not survive under clean v3.

## Consequential implications

**Round-13 story reduces further.** Combined with round 22's H6/H9/N1 contradictions:

- **F72 "worker/author asymmetry as frame property"** — dead. The asymmetry is task+clause-driven, not frame-property-driven.
- **F72 "minimal task naturally invites worker-side reads without spontaneous crossing"** — preserved as a scope-of-inspection observation; not an inspection-quantity observation.
- **F74a "premature scope closure as third candidate-loss shape"** — dead as originally framed. Under clean spec the scope isn't closed; it just doesn't cross the path boundary without explicit content pressure.
- **F74a "operational-framing self-report from H5"** — reframed as contamination-primed reasoning, not empirical evidence of a candidate-loss shape.
- **F73 (a) surface pressure, (b) maintainer collapse frame** — untouched; still supported by G1 (no maintainer collapse → strict skip via caveat citation) and by the v1/v2/v3-clean pattern (with maintainer collapse, inspection happens).
- **F73 (c) authorship-scope extension** — at cascading risk; hinges on G3/G4 clean re-runs.
- **F74b residual under strategic framing** — untested; H10/H12/H13/H15/H16 clean re-runs pending.

**"Simpler-story hypothesis" partially confirmed for the inspection-quantity axis.** Round-22 named the hypothesis *"maintainer identity + decision task drives prior-loop inspection under clean spec, without needing fixture-matched hints or explicit strategic framing."* Round-23 confirms that v1/v2/v3-clean produce extensive inspection under a minimal decision task. But the hypothesis needs a secondary axis: **inspection quantity ≠ path-crossing behavior**. Under minimal task + v1/v2/v3 clean, extensive inspection happens but the older-worktree path is not crossed. That is different from H6/H9 clean (v4/v5 with strategic-scope clause) where the older-worktree path IS crossed.

**Design implication.** If the goal is a spec that reliably surfaces referenced prior work at other paths, "maintainer identity + hunt-for-understanding" alone doesn't do it — an explicit strategic-scope operational clause (v4's *"Decisions vs execution ... re-evaluate ... alternatives it displaced and prior work it supersedes"*) or task-level authorship/purpose pressure appears to be required. Round-13 F73 had the correct three-factor shape but got the empirical evidence base (via contaminated Category-B specs) wrong; the underlying design principle survives as a plausible prior.

## Anomalies / unexpected observations

- **v2 induces todowrite planning ceremony.** Run E v2-clean issues 5 todowrite calls; Runs C (v1) and F (v3) do not. v2 has "boss/detail split" content that v1 and v3 do not have in the same shape. Possible mechanism: v2's *"They set direction and outcomes; they do not handle the details … day-to-day loop operations to you"* clause primes formal task-list ceremony. Not tested; single observation.
- **v3 reads deeper than v1/v2.** Run F v3-clean touches `agent-tools/src/main.rs`, prompt-tests, session-diff storage, and `/tmp/opencode-pretty-*.txt`. v3's maintainer/worker split explicitly distinguishes maintainer-authored (opencode/, agent-tools, docs) from worker-output (.ralph/agent/*), which appears to license broader inspection of maintainer-authored artifacts. Not tested at n=2.
- **All three cells read `docs/opencode-system-prompt/trials/2026-06-23-coverage-disclosure-ep-check-green.md`.** The most recent trial doc gets pulled in as GREEN-baseline evidence in all three grounded decisions. Not spec-dependent within the v1/v2/v3 triangle.

## Open (carried into round 24)

**Higher-priority G/H re-runs (round-22 open list, now sharpened by round-23 partial-break pattern):**

- **G3-clean** (v1 + Q2-analog author-side task on work-maintainer) — tests whether v1-clean crosses to older worktree when task adds authorship pressure. Load-bearing for F73 (c).
- **G4-clean** (v1 + PROMPT.md-purpose task on work-maintainer) — tests non-author-side surface pressure interaction.
- **G2-clean** (v3 + PROMPT.md-purpose task) — verifies round-13's crossing observation survives clean spec (predicted preserved given v3-clean's baseline behavior + purpose task's crossing pressure).
- **G1-clean** (external-observer v1 diag-v1 + Q2) — tests whether the "no maintainer collapse" case still cites PROMPT.md caveat as authoritative under clean spec, or whether Category-B contamination on `identity-outcome-diag-v1.md` was suppressing inspection there too.

**H-series clean re-runs (F74b evidence base):**

- **H10-clean** (v3 + strategic framing prescription in user message + minimal task) — tests whether strategic framing amplifies inspection or triggers crossing on top of v3-clean's already-40+ baseline.
- **H12-clean** (v3 + strategic framing + PROMPT.md caveat deleted).
- **H13-clean** (v3 + strategic framing + caveat deleted + scratchpad prior-loop summary removed) — round-13's "compound blocking → break" cell; contamination cleanup may leave inspection unchanged or reveal a different mechanism.
- **H15-clean** (v3 + minimal task + scratchpad summary removed; no framing, no caveat deletion) — H14's decontaminated version.
- **H16-clean** (v3 + compound blocking + dispatch-identity framing) — round-13's identity-only framing control that stayed at skip in contaminated conditions.

**n=1 caveat on round-23.** Each cell n=1. Magnitude stability not established. Direction (contradiction of "0 tools skip" claim) is 40× larger than any plausible run-variance so direction is stable at n=1.

**Cross-cutting scope.** Whether the reframed F72 path-crossing observation generalizes:
- Cross-model — does K3 / R1 / Qwen / Claude Sonnet/Opus on v3-clean + minimal task also inspect without crossing, or do some models cross spontaneously?
- Cross-fixture — does an analog fixture where a scratchpad points to a different-path prior loop reproduce the same "extensive current-worktree, no crossing" behavior?

## Session anchors and artifacts

**Round-23 clean specs (uncommitted):**
- `/root/experiment-materials/identity-outcome-maintainer-diag-v1-clean.md`
- `/root/experiment-materials/identity-outcome-maintainer-diag-v2-clean.md`
- `/root/experiment-materials/identity-outcome-maintainer-diag-v3-clean.md`

**Round-23 output directory:** `/root/experiment-materials/round23/` — 3 jsonl files.

**Runner:** `/tmp/run_r23.sh` — identical shape to `/tmp/run_r22.sh` with output dir remapped.

**Reference contaminated sessions (round 13):**
- Run C contam: `ses_082989c9bffemlrQJAKu17aqVv` — 0 tool_use.
- Run E contam: `ses_07c5fb651ffecud8NIEuS2VrFg` — 0 tool_use.
- Run F contam: `ses_0796c736dffeccAcVCwrHVv5e1` — 0 tool_use; H5 self-report *"I framed the question as an operational interruption decision"*.

**Task file:** `/root/experiment-materials/V5-minimal-task.md` (7 lines; ends *"Don't act yet."*).
