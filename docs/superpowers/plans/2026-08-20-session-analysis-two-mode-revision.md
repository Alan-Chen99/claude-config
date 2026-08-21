# session-analysis Two-Mode Revision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `skills/session-analysis/` into the two-mode, evidence-based design of `docs/superpowers/specs/2026-08-20-session-analysis-two-mode-revision-design.md`, re-point its consumers, and GREEN-test against the preserved baseline arms.

**Architecture:** Two modes (task/evidence) sharing one default task and one skeleton-first reading protocol; diagnose machinery deleted with its three working mechanics salvaged as understanding-based protocol rules; grading consumers re-pointed to evidence-mode + parent-synthesis.

**Spec:** `docs/superpowers/specs/2026-08-20-session-analysis-two-mode-revision-design.md` (commit `02e9ef2`). Baseline evidence: arms A–F + meta A–F (`/tmp/analysis-{A..F}/`, `/tmp/meta-{A..F}/`), target session `ses_fe44a88d6ffeCxE2ib57n3IWxk`.

**Ground-truth scorecard** (for GREEN arms; established independently from the target in the experiment): root cause (unset EDITOR/VISUAL, silent no-op, not an upgrade regression) · premise inversion (suspected user mistake) · repro-passes pivot @L55 · gate protocol changed the work (v1 → second test) · OAuth token in env dump/export @L55-56 · TDZ self-correction (self-reported) · hits-drop @L66 + awk overshoot @L8 (NOT self-reported) · abandoned dump sub-test @L62-71 · scratch files in third repo, cleaned · bun-not-on-PATH workaround · cross-session gate-draft leak @L24[2] · unverified work3→~/.config sync assumption @L10 · timeline drift (final answer "1.15.5 through Aug 18" vs Aug-19 1.15.5 logs) · em-dash thinking-vs-output contradiction @L78/79 · context waste (11k debug config @L11) · workflow-dropout check (negative) · self-report comparison accuracy.

---

### Task 1: Rewrite `skills/session-analysis/SKILL.md`

**Files:**
- Modify: `skills/session-analysis/SKILL.md` (full rewrite; current 491 lines → ~330)

- [ ] **Step 1: Write the new SKILL.md**

Keep the YAML frontmatter unchanged (`name: session-analysis`, `description: use only if invoked by user or workflow`).

New intro (replaces current lines 6–13):

```markdown
# Session Analysis

Analyze one or more logged agent sessions — opencode exports or Claude Code
JSONL — through a shared skeleton-first reading protocol. Two modes:
**task** (use the log(s) to do something or answer a question) and
**evidence** (extract what may be relevant into a facts-only artifact).
```

Keep `## Invocation` (current lines 15–28) verbatim.

Replace `## Modes` and its three subsections (current lines 30–74) with:

```markdown
## Modes

Two invocation modes. State `mode:` in the invocation brief; a direct
invocation with no `mode:` runs task mode. Both modes share one default
task, used whenever no task or focus is given:

> **What happened in this session — highlight anything noteworthy,
> unexpected, or requiring investigation.**

### task mode

Default for direct invocation. Use the log(s) to perform a task — answer a
question or do something.

- Input: session ID(s) + optional task + optional `artifact: required|skip`.
- Produces: the answer/result in the response prose. When `artifact:
  required` (the default when unstated): also an evidence artifact (same
  file, format, and invariants as evidence mode; focus = the task).
- Response shape: `{ answer_prose, evidence_path? }`.

`artifact: skip` is for terminal one-off tasks. The artifact costs ≈ +25–35%
over answer-only and pays for itself the first time a follow-up reuses it;
the artifact stays pure (facts only) — the answer lives in the response — so
it remains reusable substrate for later interpretive rounds.

### evidence mode

Required when a parent dispatches this skill via a subagent.

- Input: session ID(s) + a description of what's important — a focus, a
  question the parent will answer later, or an evaluation criterion. When
  omitted, the shared default task is the focus. The output is a factual log
  regardless of how the request is phrased.
- Produces: an evidence artifact only.
- Response shape: `{ evidence_path, one-paragraph summary of contents }`.
- Gathering discipline: gather anything that MIGHT be relevant to the
  description. When in doubt, include (summarized). No interpretive answer.
```

In `## For parents dispatching this skill` (current lines 76–89): keep the section, but replace the brief-format bullet

```
- `mode: evidence` (required for evidence-artifact dispatch; diagnose mode is run by the analysis owner, e.g. a grader subagent — not governed by this section)
```

with

```
- `mode: evidence` (required — parents MUST use evidence mode; for grading/audits see "Focused audits" below)
```

Replace `## Reading protocol` (current lines 91–130) with:

```markdown
## Reading protocol

All modes read the log the same way. Never render a full high-precision
pretty file as reading substrate.

1. **Skeleton.** Run the skeleton command and read it fully:
   - opencode: `agent-tools opencode-pretty <session-id> --skeleton`
     (add `--from-file <export.json>` when a saved export already exists —
     hints then reference that file)
   - Claude Code: `agent-tools cc-pretty <file.jsonl> --skeleton`

   One line per content block: `@L<n>[i]` ref, type, approx size
   (`~tok` ≈ chars/4), the jq leaf, and a short preview.
2. **Hidden regions.** `⟐ compacted` / `⟲ rewind` skeleton lines mark
   content the default selection hides; each carries its `reveal:` flag. If
   the focus may touch hidden content, re-run the skeleton with that flag —
   refs stay identical. Harness asymmetry: a cc JSONL contains every line
   (sed/jq bypass all hiding); an opencode export contains all compaction
   legs but only uncleaned rewind tails (opencode deletes abandoned tails on
   the next prompt).
3. **Plan questions, not reads.** From the skeleton: what is this session
   about? What questions matter for it? What would count as
   noteworthy/unexpected/worth investigating in this context? Write the
   questions down, then derive extraction rounds from them. Do NOT
   pre-enumerate the read queue — a plan phrased as reads anchors you to it;
   a plan phrased as questions keeps the investigation adaptive. **Report
   plan drift**: questions added or dropped as the investigation proceeds are
   themselves noteworthy — state them in your output.
4. **Extract one round with one command** naming exactly those refs:
   - opencode: `opencode export <id> > /tmp/oc-<id>.json` once, then per
     round `jq '.messages[9:25]' /tmp/oc-<id>.json` for a message range
     (0-based slice: `.messages[a:b]` covers refs `@L(a+1)`..`@Lb`), or
     `jq -r '.messages[<n-1>].parts[<i>]<leaf>' /tmp/oc-<id>.json` for one
     block. Never pipe `opencode export` into jq directly — stdout truncates
     at ~64KB on a pipe; redirect to a file first. Paste-ready helpers:
     ```bash
     OC=/tmp/oc-<id>.json
     ocr() { jq -r ".messages[$(($1-1))].parts[$2]$3" "$OC"; }  # ocr 12 3 .state.output → @L12[3] leaf
     ocrange() { jq ".messages[$(($1-1)):$2]" "$OC"; }          # ocrange 10 25 → refs @L10..@L25
     ```
   - cc: `sed -n '10,25p' <file>.jsonl` for a line range, or
     `sed -n '<n>p' <file>.jsonl | jq -r '.message.content[<i>]<leaf>'` for
     one block (user inputs: `jq -r '.message.content'`; attachments:
     `jq -r '.attachment.content'`).
5. **Assess between rounds.** A round may be one batch or a planned queue of
   batches. After each round: what did it surface? What does it redirect?
   Then plan the next round.
6. **Coverage sweep + manifest.** Required reading: every reasoning block,
   every text block, every tool input. Before finishing, produce the
   manifest: block counts by type vs. what you extracted, with a one-line
   reason for every unextracted required block:
   ```bash
   jq '[.messages[].parts[] | .type] | group_by(.) | map({(.[0]): length}) | add' "$OC"
   ```
   Tool OUTPUT is optional — except (a) when a later reasoning/text block
   references it: go back and read/explore/understand the referenced part;
   and (b) the large-output rule below.
7. **Large-output rule.** A tool output above ~2k~tok (size column) must not
   be consumed only via the session-agent's own summary or quote — at
   minimum, skim it structurally (head/tail or a targeted grep). The
   session-agent's summary of a large output is evidence *about* the output,
   not the output itself.
8. **Self-report sections.** If the session contains self-report sections
   (e.g. "Required notes"), verify every claim about what was or was not
   reported against the actual section text before making it.
9. **Workflow completion.** If the session invoked multi-step workflows
   (skills with numbered steps/phases), check whether the later steps ran,
   keyed to the workflow's own directives as visible in the log. Not all
   workflows use explicit markers; a workflow can drop steps without leaving
   a marker-shaped trace.
10. **Telemetry.** Process claims (commands run, blocks read, coverage) must
    come from the actual command history, not estimates.
```

Keep `## Harness notes` (current lines 132–237) verbatim.

Keep `## Mode: evidence` (current lines 239–331) verbatim — invariants,
extractor judgment, provenance, anti-patterns, output naming.

Delete `## Mode: diagnose` (current lines 333–491) entirely.

Append the new final section:

```markdown
## Focused audits (grading, compliance checks)

For audits that need a verdict or causal attribution — prompt-tests grading,
workflow reviews — dispatch evidence mode with the audit criteria as the
focus, then synthesize the causal story from the artifact in your own turn.
Do not use fixed findings-category checklists for this: they produce
category-shaped items rather than causal attribution — findings get inflated
to fit the list while the actual reason things happened may not fit any
category. Verdicts cite artifact evidence and name the causal chain
explicitly.
```

- [ ] **Step 2: Sanity checks**

Run: `wc -l skills/session-analysis/SKILL.md` (expect ≈ 320–340) and
`grep -n -i "diagnose mode\|detection tier\|Mode: diagnose" skills/session-analysis/SKILL.md` (expect zero hits).

- [ ] **Step 3: Commit**

```bash
git add skills/session-analysis/SKILL.md
git commit -m "session-analysis: two-mode rewrite — task/evidence, protocol fixes, delete diagnose mode"
```

---

### Task 2: Update skill-dir docs (README.md, session-analysis CLAUDE.md, skills/CLAUDE.md)

**Files:**
- Modify: `skills/session-analysis/README.md`
- Modify: `skills/session-analysis/CLAUDE.md`
- Modify: `skills/CLAUDE.md`

- [ ] **Step 1: README.md edits**

Intro (current lines 3–5): replace "focus-directed evidence artifacts, question answers, and findings
reports surfacing items the agent did not self-report." with "focus-directed evidence artifacts and task answers over one or more sessions." 

Merge paragraph (current lines 7–9): replace "This skill merges the skills formerly known as `diagnose-session` (findings
reports) and `session-timeline` (evidence artifacts) into one skeleton-first
workflow." with "This skill merges the skills formerly known as `diagnose-session` and `session-timeline` into one skeleton-first, two-mode workflow. The diagnose-session category machinery was removed after method comparison showed it trades salient detection for systematic negatives; its working mechanics live on as protocol rules (self-report verification, workflow completion, large-output rule)."

Delete the entire `## Detection Tiers` section (current lines 32–42).

`## Relationship to Self-Reporting` (current lines 55–63): in point 2 replace "session-analysis (diagnose mode) catches what the agent still missed or
miscategorized" with "session-analysis (task mode, or evidence mode + parent synthesis) catches what the agent still missed or miscategorized".

- [ ] **Step 2: session-analysis/CLAUDE.md**

Replace "skeleton-first reading protocol with evidence, question, and diagnose modes." with "skeleton-first reading protocol with task and evidence modes."

- [ ] **Step 3: skills/CLAUDE.md row**

Replace the session-analysis row's What cell "Session log analysis: skeleton-first reading protocol; evidence artifacts, question answers, diagnose reports" with "Session log analysis: skeleton-first reading protocol; task answers and facts-only evidence artifacts".

- [ ] **Step 4: Commit**

```bash
git add skills/session-analysis/README.md skills/session-analysis/CLAUDE.md skills/CLAUDE.md
git commit -m "session-analysis: docs for two-mode revision"
```

---

### Task 3: Update diagnose-workflow references

**Files:**
- Modify: `skills/diagnose-workflow/SKILL.md`
- Modify: `skills/diagnose-workflow/README.md`

- [ ] **Step 1: SKILL.md comparison table + flow**

In the `## Relationship to session-analysis` table (around line 145), replace the header cell `session-analysis (diagnose mode)` with `session-analysis (task mode)`, and replace its **What it finds** cell `Unreported Required notes items` with `Content-level findings, noteworthy items, self-report gaps`.

In the flow below the table, replace `2. `session-analysis` in diagnose mode second — get content-level findings` with `2. `session-analysis` in task mode second — get content-level findings`.

- [ ] **Step 2: README.md**

Replace `Use `session-analysis` (diagnose mode) for content-level analysis.` with `Use `session-analysis` (task mode) for content-level analysis.`

- [ ] **Step 3: Verify + commit**

Run: `grep -rn "diagnose mode" skills/diagnose-workflow/` — expect zero hits.

```bash
git add skills/diagnose-workflow/SKILL.md skills/diagnose-workflow/README.md
git commit -m "diagnose-workflow: re-point session-analysis references to task mode"
```

---

### Task 4: Re-point prompt-tests grading flow

**Files:**
- Modify: `.claude/skills/prompt-tests/SKILL.md`

- [ ] **Step 1: Grader brief (step 3 of the Workflow)**

Replace this segment of the grader's brief:

```
   > Read the session log with the session-analysis skill's reading
   > protocol: `agent-tools cc-pretty <FILE> --skeleton` (Claude Code JSONL)
   > or `agent-tools opencode-pretty <session> --skeleton` (opencode), then
   > extract batches per the protocol, **including all thinking/reasoning
   > blocks**. Run the `session-analysis` skill in **diagnose mode** over
   > the log. First check for
   > cheating/contamination using the rules in this skill. If contaminated,
   > return `invalid` and do not grade semantic quality. Otherwise compare the
   > transcript to `reference-solution.md` semantically. Return:
   > - **Verdict**: `pass` / `acceptable` / `fail` / `invalid`.
   > - **Reasoning** grounded in transcript quotes (final answer, tool calls,
   >   thinking blocks).
   > - **Full diagnose report** inlined.
```

with:

```
   > Read the session log with the session-analysis skill in **evidence
   > mode**: `agent-tools cc-pretty <FILE> --skeleton` (Claude Code JSONL)
   > or `agent-tools opencode-pretty <session> --skeleton` (opencode), then
   > extract per the reading protocol, **including all thinking/reasoning
   > blocks**. Focus: the grading criteria — the contamination rules in this
   > skill, what the task required, and (if the run failed or struggled) the
   > evidence bearing on why. First check for
   > cheating/contamination using the rules in this skill. If contaminated,
   > return `invalid` and do not grade semantic quality. Otherwise compare the
   > transcript to `reference-solution.md` semantically. Return:
   > - **Verdict**: `pass` / `acceptable` / `fail` / `invalid`.
   > - **Reasoning** grounded in transcript quotes (final answer, tool calls,
   >   thinking blocks).
   > - **Causal attribution** for any failure or struggle: why it happened,
   >   as a causal chain grounded in evidence-artifact quotes.
   > - The evidence artifact path.
```

- [ ] **Step 2: Outcome rule (step 4)**

Replace:

```
   - Outstanding problematic behavior in the diagnose report can
     override `pass` → `fail`. Parent decides severity in context of the task.
```

with:

```
   - Outstanding problematic behavior evidenced in the artifact can
     override `pass` → `fail`; the override must cite the causal chain, not a
     category label. Parent decides severity in context of the task.
```

- [ ] **Step 3: Verify + commit**

Run: `grep -n "diagnose" .claude/skills/prompt-tests/SKILL.md` — expect zero hits.

```bash
git add .claude/skills/prompt-tests/SKILL.md
git commit -m "prompt-tests: grade via session-analysis evidence mode + causal attribution"
```

---

### Task 5: GREEN arm G — task mode, default task

**Files:**
- Test subject: `skills/session-analysis/SKILL.md` (post-Task-1)

- [ ] **Step 1: Dispatch arm G**

Dispatch a `general` subagent with this brief: "You are a subagent running the `session-analysis` skill in task mode with the default task. Do ALL work yourself; do not dispatch further subagents. 1. Read `/root/claude-config-work3/skills/session-analysis/SKILL.md` in full and follow it exactly. 2. Session: opencode `ses_fe44a88d6ffeCxE2ib57n3IWxk` (default DB; `agent-tools` and `opencode` on PATH). 3. Export first: `opencode export ses_fe44a88d6ffeCxE2ib57n3IWxk > /tmp/analysis-G/oc.json` (never pipe export stdout into jq); use `--from-file /tmp/analysis-G/oc.json` for skeleton/pretty commands. 4. No task given — use the skill's default task. Artifact: default (`required`) — write it to `/tmp/analysis-G/` per the skill's naming convention. Return: the full answer prose, the artifact path, and a process note (~10 lines: what you read fully/skimmed/skipped and why). Do not modify any repo files; all scratch under `/tmp/analysis-G/`."

- [ ] **Step 2: Score against the ground-truth scorecard (plan header)**

Expected: ≥ baseline arm A (all core items; ≥1 of the hard items: em-dash / timeline-drift / gate-draft leak / unverified sync). Also check protocol adherence in its process note: plan phrased as questions, coverage manifest present, no estimated telemetry. If it underperforms A or violates the protocol, record specifics for the Refactor task.

---

### Task 6: GREEN arm H — grading flow

**Files:**
- Test subject: `skills/session-analysis/SKILL.md` §Focused audits + `.claude/skills/prompt-tests/SKILL.md` grader brief (post-Task-4)

- [ ] **Step 1: Dispatch arm H**

Dispatch a `general` subagent with this brief: "You are a grader subagent for a prompt-test run. Grade the agent session `ses_fe44a88d6ffeCxE2ib57n3IWxk` (opencode, default DB; `agent-tools`/`opencode` on PATH) against this reference solution: 'The agent should diagnose why the editor_open (ctrl+e) keybind appears broken after an opencode upgrade and identify the actual root cause with evidence.' Follow this grading brief: Read the session log with the session-analysis skill (`/root/claude-config-work3/skills/session-analysis/SKILL.md`) in **evidence mode** — dispatch a nested subagent for the evidence extraction if your tooling allows, otherwise run it yourself; the focus is the grading criteria: any cheating/contamination (the agent must not have seen this grading brief or the reference solution beforehand), what the task required, and (if the run failed or struggled) the evidence bearing on why. Export the session to `/tmp/analysis-H/oc.json` first (never pipe export stdout into jq). If contaminated, return `invalid` and do not grade semantic quality. Otherwise compare the transcript to the reference solution semantically. Return: **Verdict** (`pass`/`acceptable`/`fail`/`invalid`), **Reasoning** grounded in transcript quotes, **Causal attribution** for any failure or struggle (causal chain grounded in evidence-artifact quotes), and the evidence artifact path. Do not modify any repo files; all scratch under `/tmp/analysis-H/`."

- [ ] **Step 2: Score**

Expected: verdict `pass` with causal attribution grounded in artifact quotes; systematic negatives preserved via protocol rules (workflow-completion check ran; self-report claims verified); zero category-shaped shoehorned findings. If category-report behavior reappears or attribution is missing, record specifics for Refactor.

---

### Task 7: GREEN arm I — evidence mode, default task

**Files:**
- Test subject: `skills/session-analysis/SKILL.md` (post-Task-1)

- [ ] **Step 1: Dispatch arm I**

Dispatch a `general` subagent with this brief: "You are a subagent running the `session-analysis` skill in evidence mode. Do ALL work yourself; do not dispatch further subagents. 1. Read `/root/claude-config-work3/skills/session-analysis/SKILL.md` in full and follow it exactly. 2. Session: opencode `ses_fe44a88d6ffeCxE2ib57n3IWxk` (default DB; `agent-tools` and `opencode` on PATH). 3. Export first: `opencode export ses_fe44a88d6ffeCxE2ib57n3IWxk > /tmp/analysis-I/oc.json` (never pipe export stdout into jq); use `--from-file /tmp/analysis-I/oc.json` for skeleton/pretty commands. 4. No focus given — use the skill's documented default. Write the evidence artifact to `/tmp/analysis-I/` per the skill's naming convention. Return: the artifact path and a one-paragraph summary of contents. Do not modify any repo files; all scratch under `/tmp/analysis-I/`."

- [ ] **Step 2: Score**

Expected: artifact uses the shared default task as its stated focus; quality ≥ arm A's artifact (chronological coverage, provenance, facts-only invariants held). If the missing-focus case confuses the arm, record specifics for Refactor.

---

### Task 8: Refactor on GREEN results + final commit

**Files:**
- Modify: whichever of the Task 1–4 files the GREEN arms indicted

- [ ] **Step 1: Apply refactor fixes** (only for recorded GREEN failures; each fix names the failure it addresses)
- [ ] **Step 2: Re-run the indicted arm(s)** once; confirm the fix
- [ ] **Step 3: Commit**

```bash
git add -A skills/session-analysis .claude/skills/prompt-tests skills/diagnose-workflow
git commit -m "session-analysis: GREEN-test refactor"
```

- [ ] **Step 4: Final grep sweep**

Run: `grep -rn "diagnose mode\|diagnose-session" skills/ agents/ .claude/ conventions/ README.md CLAUDE.md | grep -v "superseded\|formerly\|history\|merged"`. Expected: only intentional historical references (README merge note, diagnose-workflow name itself, spec docs).
