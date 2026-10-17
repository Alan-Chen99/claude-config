<!--
This file is documentation for maintainers of the `prompt-engineer-v2`
skill's patch mode. It captures one full run of the 12-step workflow on
a concrete example task, so that anyone editing `steps.md` can see the
*shape* of output each step is expected to produce.

DO NOT copy phrasing, framings, invariants, options, or conclusions from
this file into `steps.md`. The steps.md prompts should be general; the
content below is one specific application. Lifting it into the prompts
would overfit them to this example.

When you change `steps.md`, re-run the workflow on the example task
below and update this file with the new transcript. A diff between the
old and new transcript is a fast way to see whether your prompt edit
actually changed the shape of the output you wanted to change.
-->

# Test Requests

A worked example of the prompt-engineer-v2 patch-mode workflow, as
documentation for people editing this skill. The example task is small
enough to fit in one file but exercises every step.

## How to use this file

- **Reading**: scan the headers; each step shows the kind of output the
  prompt in `steps.md` is asking for.
- **Editing `steps.md`**: after a change, re-run the workflow on the
  example task and replace this transcript. If the diff is empty, your
  edit didn't change behavior on this case — verify it changes behavior
  on the case you actually targeted.
- **Adding a new example**: append another `## Example N: ...` section.
  Don't replace the existing one — older examples are still useful as
  regression cases.

## Anti-overfitting reminder

The invariants, brainstorm ideas, options, regression scenarios, and
final draft below are **specific to this one task**. None of them
should appear verbatim in `steps.md`. If you find yourself wanting to
add "here is an example invariant for prompts that use external
scripts" to `steps.md`, stop — the prompt should describe the *kind*
of thing the agent must produce, not list answers that fit this task.

---

## Example 1: Remove the `pre_output.record` script dependency

### Task as given

> `/repos/claude-config/sys_prompt/alan-default-next.md` uses a pre_out
> script (`/repos/claude-config/src/claude_config/pre_output/record.py`).
>
> We will remove that. Do the equivalent without having a pre-output
> script.

### Context the agent gathered before Step 1

Re-verified against the worktree on 2026-10-17; drift from the
previous run is marked **(drift)**.

- `sys_prompt/alan-default-next.md` lines 205–224 hold `## Before
  response` **(drift: was 204–221)**. Line 207: `IMPORTANT: MUST run
  before responding to user, including follow-ups. NO EXCEPTIONS.`
  The JSON (`turn`, `summary`, `workflow`, `uncertainties`,
  `possible-verification`, `possible-next-steps`) now reaches
  `agent-tools pre_output.record` on stdin through a quoted heredoc,
  not as an argument **(drift)**. Line 222: `If more work turns out
  needed after recording, re-record with the same \`turn\`.` Line
  224: `This should be the last thing you run. If you needed to call
  any tools (including read) afterwards, call \`agent-tools
  pre_output.record\` again.`
- `src/claude_config/pre_output/record.py` no longer discards its
  input **(drift)**. Two jobs: (1) print a `<system-reminder>` with
  **one** rule, `NEVER ask user to read files or run commands that
  you have not already read or run yourself`; (2) validate the JSON
  (object, non-empty `summary`) and write it atomically to
  `/tmp/claude-pre-output-<session>.json`. On bad input it prints the
  reason to stderr and exits 1, and still prints the rule.
- The second rule (`NEVER reply to user if uncertainties remain…`)
  was deleted on purpose **(drift)**: `sys_prompt/README.md`
  `### pre_output.record's RULES` says `# Epistemic Integrity` already
  states it with the escalate branch, and that it bought neither
  verification nor obedience.
- `src/claude_config/ntfy_hook.py` `recorded_summary()` reads that
  file on Stop and sends its `summary` as the "Done" push body;
  `do_cancel` unlinks it on UserPromptSubmit so an existing file means
  "this turn". Without a record it falls back to an OpenRouter-haiku
  summary of the transcript **(new dependent)**. Pinned by
  `tests/test_pre_output_record.py`.
- Other code naming the call: `src/claude_config/env_context/render.py`
  emits hook text telling a resumed session to run the
  resume-from-summary commands "before any other tool call,
  `pre_output.record` included" **(new dependent)**;
  `agent-tools/src/main.rs` (subcommand) and `claude.rs` (comments).
- Docs that assume the call is the turn's last tool call:
  `.claude/skills/prompt-tests/SKILL.md` step 3 and
  `references/grader.md`.
- Same section, out of scope: `sys_prompt/alan-default.md`,
  `output-styles/alan-default.md`, `output-styles/alan-default-next.md`
  **(drift: the old list named `output-styles/*.md` loosely)**.
- `sys_prompt/CLAUDE.md` governs any edit here: every line needs a
  `README.md` section (claim, hypothesis, retirement condition) that
  quotes live prompt text, checked by `scripts/check-prompt-rationale.sh`.

---

### Step 1 — Motivation

**Problem.** Lines 205–224 make every reply end with `agent-tools
pre_output.record`, which bundles three things: (a) a breakpoint —
the agent composes six fields of turn state; (b) the one surviving
rule, re-entering context in the tool result after the work and
before the reply; (c) a per-turn summary file that the ntfy "Done"
push reads. We want (a)–(c) without the script.

**Why the current text failed.** Nothing failed: the change removes a
dependency, it does not answer a misbehaviour. "No instruction covers
this" does not fit either — the section works as written. The nearest
evidence about the text's performance: `sys_prompt/README.md` records
that the deleted sibling rule changed nothing, and
`skills/resume-from-summary/README.md` records line 207's `NO
EXCEPTIONS` being obeyed strongly (14 of 19 resumes ran the call; 17
of 19 summaries restated it) and competing with a skill invocation
for the first action. Whether the surviving rule changes behaviour is
**unverified** — no ablation is recorded. So there is no failing text
to diagnose; the text to replace is lines 205–224 by the task's fiat.

**Cost of inaction.** The prompt needs the `agent-tools` binary and
the `claude_config` package on PATH; the rule a reader of the prompt
cares about lives in a Python constant; every turn pays a subprocess.

**Success criteria.**

- `alan-default-next.md` names no `pre_output.record`.
- The surviving rule still reaches context after the turn's work and
  before the reply, and a later tool call still forces a fresh pass.
- The "Done" push still carries the session's own summary of the
  turn that just ended, never an earlier turn's.
- No new script; any code change is to an existing hook.

**Mode.** `efficiency`.

---

### Step 2 — Invariant Extraction

Each pair was sketch-tested: "the rule is in the prompt" and "a block
of fields exists" both pass a naive option (rule at the top of the
prompt; a block emitted anywhere), so both were re-stated as
relationships.

- **I1 — The rule is read after the turn's work and before the reply
  is composed.** Enforced by: the rule arrives in the tool result of
  the call line 224 makes the last thing run.
- **I2 — Composing turn state precedes the reply.** Enforced by: line
  207 (`MUST run before responding … NO EXCEPTIONS`) and the six
  fields the heredoc requires. `record.py`'s docstring: "the
  argument's content matters less than the act of composing it."
- **I3 — Tool work after the checkpoint invalidates it.** Enforced
  by: line 224's "call … again" and line 222's re-record with the
  same `turn`.
- **I4 — The push carries the summary written in the turn that is
  ending.** Enforced by: `record.py` writes the file;
  `ntfy_hook.do_cancel` deletes it on UserPromptSubmit; Stop reads it.
  Sketch: an option that only emits a summary block passes "a summary
  exists" while the push silently falls back to haiku.
- **I5 — A malformed checkpoint is visible to the agent.** Enforced
  by: `record.py` exits 1 with the reason on stderr when `summary` is
  missing or the JSON is bad.

Per the new Step 2 sentence, I2 and I3 count as enforcement even
though they are prompt lines, and I5 gets no extra weight for being
code.

**At risk.** I1 high: any static placement loses recency. I4 high:
removing the script removes the writer the push reads. I3 medium. I5
medium: nothing replaces validation unless an option adds it. I2 low.

The previous run's loop and no-work-savings pairs are gone: both hung
on the uncertainties rule, which no longer exists. The surviving rule
gains from being anticipated — an agent that reads it before filling
`possible-verification` is the desired outcome.

---

### Step 3 — Brainstorm

Dimensions: timing, actor, mechanism, scope, existing text, plus one
problem-specific: *where the summary reaches the push from*.

1. **(T)** Bash `cat <<'X'` of the JSON with the rule appended; the
   tool result carries both.
2. **(T)** Same, but `cat > /tmp/claude-pre-output-$SID.json`
   writes the record and an `echo` prints the rule.
3. **(T)** One-line `echo` of the rule only; no fields.
4. **(R)** No tool call: the rule moves into the Response template's
   `## Evidence` line, next to the slot it governs.
5. **(R)** ntfy reads the reply's existing `## Summary` line from the
   transcript.
6. **(R)** ntfy reads `"summary"` from the last checkpoint command in
   the transcript (the tool_use input of idea 1).
7. **(H)** PostToolUse hook appends the rule to every tool result.
8. **(H)** Stop hook scans the reply for "please run" and blocks.
9. **(H)** UserPromptSubmit hook injects the rule.
10. **(N)** Delete lines 205–224 and the rule; rely on `# Epistemic
    Integrity` and line 198; push falls back to haiku.
11. **(N)** Keep the section, drop line 207's `NO EXCEPTIONS` force.
12. **(S)** Fold the rule into line 198 (`! <command>`), the existing
    line on asking the user to run commands.

Groups: T 1–3; R 4–6; H 7–9; N 10–11; S 12. No group exceeds three.
The existing-text dimension yielded 10–12; every other idea also
rewrites lines 205–224, because the task already demands it.

---

### Step 4 — Identify Target State & Workflows

**Target state.** After each turn's last tool call and before its
reply, the agent has composed the turn state and read the rule; the
"Done" push carries that turn's own summary; the prompt names no
custom executable.

**Option A — Inline checkpoint that writes the record** (ideas 1, 2).
Work → Bash: `cat > /tmp/claude-pre-output-${SID}.json <<'EOF' {…}
EOF; echo '<rule>'` → result shows the rule → reply. Any later tool
call → run it again.
Restored: I1, I2, I3, I4 (ntfy unchanged). Abandoned: I5 — a bad
JSON or empty summary lands in the file and ntfy logs and falls back.
Failing text: lines 205–224 rewritten in place.

**Option B — Response-borne** (ideas 4, 5).
Work → reply opens with `## Evidence`, whose template line carries the
rule → `## Summary` → Stop: ntfy extracts `## Summary` from the
transcript.
Restored: I4 (turn-scoped by construction: the transcript's last
message is this turn's). Abandoned: I1 (rule is static, read at the
slot rather than after the work), I2, I3 (no checkpoint to go stale),
I5. Failing text: lines 205–224 removed; rule moved into the template.

**Option C — Delete** (idea 10).
Work → reply. Restored: none. Abandoned: I1–I5; the push uses haiku.
Failing text: removed; its rule's content is left to `# Epistemic
Integrity`, which does not state it.

**Distinctness.** A has a tool result between the work and the reply;
B has none but a different summary source; C has neither. Distinct.

---

### Step 5 — Draft Prompt Updates Per Option

**Option A.** Replace lines 205–224 with:

````
## Before response

Last thing before every reply, follow-ups included, and again after any later tool call:

```
cat > "/tmp/claude-pre-output-${CLAUDE_CODE_SESSION_ID:?}.json" <<'EOF'
{ "turn": <int>, "summary": "<≤10 words>", "workflow": "...", "uncertainties": [...], "possible-verification": [...], "possible-next-steps": [...] }
EOF
echo 'Rule: never ask the user to read a file or run a command you have not read or run yourself.'
```
````

- Remove: lines 205–224, including line 207's `NO EXCEPTIONS` and
  both `agent-tools pre_output.record` references.
- Placement: same position, above `## Response template`.
- Trigger: every reply.

**Option B.** Remove lines 205–224. In `## Response template`, change
`Commands you ran (exact), and the output (brief)` to `Commands you
ran (exact), and the output (brief). Anything you ask the user to run
or read is here first.` Code: `ntfy_hook.recorded_summary` reads the
last `## Summary` of the final assistant message.

**Option C.** Remove lines 205–224. No addition.

All three also need `sys_prompt/README.md`'s `### pre_output.record's
RULES` rewritten, or `check-prompt-rationale.sh` fails on a section
quoting no live text.

---

### Step 6 — Context & Conflict Check

| Question | Option A | Option B | Option C |
| --- | --- | --- | --- |
| Reinforce | Line 7: hooks and tool results carry harness text, so a tool result is a familiar place for a rule. Line 222's re-record idea survives. | `## Evidence (REQUIRED)` already asks for "Commands you ran" — the rule is its contrapositive. | `# Epistemic Integrity` covers uncertainty, not punting. |
| Contradict | **Line 155**: `agent-tools run` is "Required for side-effectful … commands" — the `cat >` write is one, so the checkpoint must be wrapped in the very binary we are removing. Line 7 says `<system-reminder>` in tool results comes from the harness; wrapping the echo in it would be false, so it is not wrapped. | Response template is skipped on deep resumes (5 of 19 in resume-from-summary README); the rule would go with it. | Line 198 sanctions suggesting `! <command>` the user runs; with no rule left, nothing bounds that to commands the agent could not run itself. |
| What goes wrong | Prompt now hard-codes `record_path`, which `record.py` calls "the only definition of the path". Unset session id → `:?` aborts. | `## Summary` inside a fenced block (a reply drafting a doc) is taken as the summary. Summary is a sentence, not ≤10 words. | Push loses the session's own summary. |

**Hard constraint.** No checkpoint may have a side effect: line 155
would then require `agent-tools`.

**Revisions.**

- **A → A′.** Drop the write; `cat <<'TURN_STATE'` echoes the JSON
  and the rule. The push takes `"summary"` from that call's input in
  the transcript (idea 6), which is turn-scoped by position like B's,
  so `do_cancel`'s unlink is no longer needed for this source.
- **B:** kept as the static alternative.
- **C:** dropped — fails the task's "equivalent".

---

### Step 7 — Regression Analysis

**A′.**

- *Resumed session.* Current: `env_context/render.py` tells the agent
  to run the resume commands before `pre_output.record`. Risk: after
  the prompt change the hook still names a call the prompt no longer
  teaches; the subcommand still exists, so the agent runs the old
  script and both mechanisms coexist. Mitigation: change the hook
  text in the same change to "before any other tool call, the
  pre-response check included" and re-run
  `check-prompt-coupling.sh`.
- *Other prompts still on the script.* Current:
  `sys_prompt/alan-default.md` and both output styles write the file.
  Risk: if ntfy only reads the transcript, those sessions lose their
  summary. Mitigation: ntfy tries the record file, then the
  transcript checkpoint, then haiku.
- *Heredoc collision.* Current: the delimiter is `EOF`. Risk: a
  summary or uncertainty containing a line `EOF` ends the heredoc and
  the rest runs as shell. Mitigation: delimiter `TURN_STATE`.
- *Prompt-test grading.* Current: the prompt-tests skill says
  "`pre_output.record` is the last tool call". Risk: the statement
  goes stale; the shape (deliverable second-to-last) holds.
  Mitigation: reword those two docs to "the pre-response check".

**B.** Same resume and other-prompt regressions; plus deep resumes
that skip the template now lose the rule as well — today 14 of 19 ran
the call. Accepted only if B is picked.

---

### Step 8 — Pick Best Option & Full Draft

**Pick A′.** It is the only option that keeps I1 (rule after the
work) and I3 (fresh pass after later tool calls) — the reason
`record.py` exists — while meeting the no-side-effect constraint. B
trades I1 for removing a tool call per turn, a measurement question
(Step 11) rather than a design one. Versus the script: the rule is
visible in the prompt, no binary is needed, and the push's source is
turn-scoped by transcript position instead of by a delete-on-submit.

**`sys_prompt/alan-default-next.md`**, replace lines 205–224:

````
## Before response

The last thing you run before every reply, follow-ups included, and again after any later tool call (same `turn`):

```
cat <<'TURN_STATE'
{
  "turn": <int>,
  "summary": "<≤10 words>",
  "workflow": "<skill or workflow> step <n> | none",
  "uncertainties": ["unresolved observations, unverified assumptions, unconfirmed data", ...],
  "possible-verification": ["what should the user do to verify your response", ...],
  "possible-next-steps": ["refactor, update docs", ...]
}
Rule: never ask the user to read a file or run a command you have not read or run yourself.
TURN_STATE
```

If the rule shows more work is needed, do it and run this again.
````

**`sys_prompt/README.md`**: replace `### pre_output.record's RULES`
with `### \`## Before response\`'s \`Rule:\`` — claim: the rule
re-enters at the recency edge; hypothesis: fewer replies that hand the
user an unrun command; retirement: an arm without the section hands
the user unrun commands no more often, on a `prompt-tests/general/`
case to be named (none exists — it stands as a deletion candidate).

**Code (existing hooks, not applied here).**
`ntfy_hook.recorded_summary`: record file, else the `"summary"` of the
last `cat <<'TURN_STATE'` Bash call after the last user message
(`json.JSONDecoder().raw_decode` on the heredoc body), else `None`.
`env_context/render.py`: the wording from Step 7.

---

### Step 9 — Failures Under Perfect Obedience

1. **Crash / silent success.** `cat` of a quoted heredoc cannot fail
   or expand. A JSON typo now succeeds silently (I5 lost); the only
   consumer is the push, which falls back.
2. **Impossible to follow.** Needs Bash. Every session under this
   prompt has it.
3. **When to follow.** "Last thing … again after any later tool
   call" is checkable from the agent's own transcript.
4. **Underspecified.** "Same `turn`" moved to the first line from
   line 222, so a re-run cannot open a new turn number.
5. **Missing context.** None: the rule is in the prompt and the
   result.
6. **Code paired with the prompt.**
   - *ntfy extractor.* Condition: the last `cat <<'TURN_STATE'` call
     after the last user message. Wrong cases: the agent quotes the
     checkpoint inside another Bash command (editing a prompt that
     contains it — exactly this task); the call is earlier than
     `read_transcript_tail`'s 8,000-byte tail when the reply is long;
     a subagent's checkpoint in a sidechain. Revision: match only a
     command that *starts* with the delimiter line; read a larger
     tail; skip sidechain records. The agent never sees the
     extractor's verdict, so no prompt line depends on it; a miss
     costs one haiku-summarised push.
   - *`env_context` hook text.* Its message names the checkpoint; if
     it drifts from the prompt it misleads the agent into a removed
     call. Pinned by adding the new phrase to
     `check-prompt-coupling.sh`.
   - *Removed code.* `record.py`'s validation and loud exit go; the
     prompt never told the agent the script was always right, so
     nothing in the prompt now trusts a check that no longer runs.

**Assumptions.** Bash available; Claude Code JSONL transcripts with
tool_use inputs; `CLAUDE_CODE_SESSION_ID` no longer needed by the
prompt.

---

### Step 10 — Execution Error Check

1. **Misreading (low).** "Last thing you run" vs. "last thing in the
   turn" — same in practice.
2. **Skipping (high).** Deep resumes skipped today's call in 5 of 19;
   dropping `NO EXCEPTIONS` may raise that. Revision: none in the
   prompt — the force is a claim `sys_prompt/CLAUDE.md` says needs a
   rate; measure it (Step 12) before restoring the capitals.
3. **Over-application (low).** Subagents do not get this prompt.
4. **Ordering (medium).** The agent writes the reply, then the
   checkpoint, then a second reply. Line "The last thing you run
   before every reply" already orders it; the risk is unchanged from
   today.
5. **Hallucination (medium).** `possible-verification` listing
   commands not run is exactly what the rule targets; no revision.

---

### Step 11 — Top Concerns

1. **The rule may be cost only.** Likelihood medium, impact low. No
   case measures it; its sibling was deleted for doing nothing. A′
   preserves a mechanism whose value is unverified. Mitigation: the
   README entry's deletion-candidate status.
2. **Self-authored recency.** Likelihood medium, impact low. The
   script's rule was text the agent had not typed; A′'s is text the
   agent copies into its own command. Whether reading it back has the
   script's effect is unmeasured. Mitigation: the testing suggestion
   compares arms.
3. **Two mechanisms during migration.** Likelihood high, impact low.
   Three other prompt files keep the script until the follow-up.
   Mitigation: ntfy reads both sources.

None is ≥ medium on both axes. No revision.

---

### Step 12 — Final Version

**1. Files changed.**

- `sys_prompt/alan-default-next.md` lines 205–224 (from `## Before
  response` through `…call \`agent-tools pre_output.record\` again.`):
  replace with the Step 8 block verbatim.
- `sys_prompt/README.md`: the Step 8 section replaces `###
  pre_output.record's RULES`.
- `src/claude_config/ntfy_hook.py`: `recorded_summary` falls back to
  the transcript checkpoint (Step 8, with Step 9's matching rules);
  `tests/test_pre_output_record.py` gains a transcript case.
- `src/claude_config/env_context/render.py`: "`pre_output.record`
  included" → "the pre-response check included";
  `scripts/check-prompt-coupling.sh` pins the phrase.

**2. The failing text from Step 1.** None was diagnosed. Lines
205–224 are rewritten in place because the task removes their
dependency; line 207's `NO EXCEPTIONS` is dropped as a force claim
with no rate behind it, and Step 10 names the measurement that would
restore it.

**3. Environment.** Bash. No `agent-tools`, no `claude_config` on
the prompt's path.

**4. Tradeoffs.** I5 lost: a malformed checkpoint is silent and the
push falls back. Rule value unverified (concern 1). Migration leaves
two mechanisms until the other three prompts move.

**Follow-ups.** Migrate `sys_prompt/alan-default.md` and both output
styles; then delete `record.py`, the `pre_output.record` subcommand,
`do_cancel`'s unlink, and the `output-styles/README.md` section;
reword the two prompt-tests docs.

**5. Testing.** Under `prompt-tests`, a fixture whose task tempts the
agent to end with "run `pytest` to confirm": arms = script prompt,
A′, no section. Grade the reply for unrun commands handed to the
user, and the session for a checkpoint after the last tool call. Then
check `~/.cache/claude-config/ntfy_hook.log` shows the A′ arm's
summary taken from the transcript.

---

## Notes from this run (for steps.md maintainers)

These are about the workflow, not the example. This run was on the
2026-10-17 `steps.md` and the drifted context above.

- **Step 1 item 2 "Why the current text failed": vacuous as a
  diagnosis, useful as a prompt to look.** The task is a dependency
  removal; nothing failed. The item's three listed answers (cause
  found / unverified / "no instruction covers this") do not include
  "this is not a failure-driven change", so the answer had to be
  improvised. The search it prompted did surface evidence about the
  text (the sibling rule's deletion, `NO EXCEPTIONS` being obeyed),
  which shaped Steps 10 and 11. Suggest an explicit "n/a: change is
  not failure-driven" answer, or gate the item on `correctness`.
- **Step 3 "Existing text" dimension: mostly noise here.** Every idea
  already rewrites the section because the task says so; the
  dimension's own yield (delete, drop the force, fold into another
  line) were reasonable ideas but came from treating "Step 1's failing
  text" as "the text being replaced", which the step did not say.
- **Step 4 "Failing text" line: redundant.** Each option's answer
  restated its own sequence ("rewritten in place", "removed"). It
  added one useful observation, for C (the rule's content left to a
  section that does not state it), which "abandoned" would also have
  caught.
- **Step 5 remove line: harmless duplication** of "what existing text
  conflicts" on this task, since the failing text and the conflicting
  text are the same lines.
- **Step 9 item 6 (now item 7, "Fixed check paired with judgment") "Code paired with the prompt": the most productive
  new item.** It found the extractor would match the checkpoint quoted
  inside another command, the 8,000-byte tail, and sidechains, and it
  forced the stale `env_context` hook text to be treated as a
  prompt-coupled message. Its second bullet ("what the agent does
  next") was vacuous for the ntfy code, whose verdict the agent never
  sees; the item could say so as an answer.
- **Step 12 item 2: vacuous, same root as Step 1 item 2.** "Why its
  cause no longer applies" has no referent when no cause was found.
- **Changed in `steps.md` after this run, from the findings above:**
  Step 1 item 2 now takes "no failure" as an answer and Steps 3, 4, 5
  and 12 skip their failing-text items when it is given; Step 9 item 7
  asks what the agent does next only for results it sees. On this task
  those items would now be skipped, not answered vacuously.
- **The Step 2 "code is not stronger" sentence changed scoring.** I5
  (script validation) was rated medium, not as the strongest pair, and
  its loss was accepted.
- **Context drift was large and changed the answer.** The script now
  feeds the ntfy push and has one rule; the old run's loop invariants
  no longer exist. Re-verifying the "Context gathered" section is
  essential, and the per-turn summary file was found only by reading
  `record.py`, not the prompt.
- **Step 6 found the decisive constraint again**, this time from an
  unrelated prompt line (`agent-tools run` for side effects) — the
  table's "contradict" row is where cross-section conflicts surface.
