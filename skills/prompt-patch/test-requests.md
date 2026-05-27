<!--
This file is documentation for maintainers of the `prompt-patch` skill.
It captures one full run of the 12-step workflow on a concrete example
task, so that anyone editing `steps.md` can see the *shape* of output
each step is expected to produce.

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

A worked example of the prompt-patch workflow, as documentation for
people editing this skill. The example task is small enough to fit in
one file but exercises every step.

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

- `alan-default-next.md` lines 204–221 contain the "Before response"
  section. The instruction is to run `agent-tools pre_output.record`
  with a JSON argument whose fields are `turn`, `summary`, `workflow`,
  `uncertainties`, `possible-verification`, `possible-next-steps`.
- `src/claude_config/pre_output/record.py` discards its argument,
  prints `recorded successfully.`, then prints a `<system-reminder>`
  block with two rules: "NEVER ask user to read files or run commands
  that you have not already read or run yourself" and "NEVER reply to
  user if uncertainties remain. Do more verification and research."
- Lines 219 ("You may re-record with updated info using the same
  `turn` value if you decide more work is needed after the first
  call") and 221 ("This should be the last thing you run. If you
  needed to call any tools (including read) afterwards, call
  `agent-tools pre_output.record` again") together make the call
  repeatable within a turn — the protocol is a loop, not a
  one-shot.
- Out of scope for *this* task: `output-styles/*.md`,
  `sys_prompt/alan-default.md`, and the `agent-tools` Rust subcommand
  that wraps the script. These also reference `pre_output.record` and
  would need attention as a follow-up.

---

### Step 1 — Motivation

**Problem.** `sys_prompt/alan-default-next.md` lines 204–221 require
running `agent-tools pre_output.record '{…}'` before every
user-facing response. Three behaviors are bundled into that call:

1. *Externalization.* The agent must fill out six JSON fields before
   the tool can be invoked.
2. *Rule re-injection.* The script's stdout contains a
   `<system-reminder>` re-stating two behavioral rules; this stdout
   appears immediately after the externalization, in the agent's
   freshest context.
3. *Loop.* The "re-record with same `turn`" instruction makes the
   call repeatable: if the rules surface a problem with the
   externalization, the agent fixes the problem and calls again.

We want all three behaviors without the script.

**Cost of inaction.** The prompt is coupled to a custom executable
that lives outside the prompt file. Any environment running this
prompt must also ship `agent-tools` and `claude_config.pre_output`.
The rule text is invisible from the prompt file itself — a maintainer
reading `alan-default-next.md` has to chase a Rust binary to find out
what rules are injected at response time.

**Success criteria.**

- `alan-default-next.md` contains no reference to `pre_output.record`.
- An agent operating under the revised prompt still externalizes turn
  state with the same six fields (or an explicit replacement that
  serves the same purpose).
- The two behavioral rules are still present in the agent's context
  at response generation time.
- The fix loop — "rules surfaced after externalization; agent
  restarts if rules are violated" — is preserved as a structural
  property of the prompt, not just an aspiration.
- No new external script dependency is introduced.

**Classification.** `efficiency`. The invariants hold today (the
script works). The change optimizes the enforcement mechanism by
removing a hidden runtime dependency. Step 2 enumerates the
invariants that the optimization puts at risk so Step 7 can preserve
them.

> NEXT STEP:
> `agent-tools skill prompt_patch.do --step 2 --mode=efficiency …`

---

### Step 2 — Invariant Extraction

Pairs the current "Before response" mechanism guarantees. Focus is on
the *relationships between steps*, not on the existence of any single
field.

- **I1 — Every uncertainty the agent identifies is either fixed or
  carried into the response.**
  Enforced by: the JSON `uncertainties: [...]` field at lines 209–217
  is written by the agent *before* the script's stdout arrives. After
  the agent commits the list, `record.py:14-19` prints the rule
  "NEVER reply to user if uncertainties remain. Do more verification
  and research," which then forces the agent to either resolve the
  listed uncertainties or call `record` again with an updated list.
  Line 219 ("re-record with updated info using the same `turn`
  value") closes the loop. Drop any one of (a) the commit field,
  (b) the rule print, or (c) the re-record instruction, and the
  enforcement collapses.

- **I2 — The agent gains no work-savings from under-reporting its
  state.**
  Enforced by: the tool call appears *after* the work and *before*
  the response, with the rules emerging in the tool's stdout. The
  agent's options at that point are (a) honestly commit and possibly
  loop, or (b) under-commit to skip the loop — but (b) saves no
  work, because the work of constructing the JSON has already been
  done by the time the rules appear. The mechanism makes the honest
  path the path of least resistance, rather than relying on a check
  that catches dishonesty after the fact.

- **I3 — The agent does not punt verification onto the user.**
  Enforced by: `record.py:16` prints "NEVER ask user to read files
  or run commands that you have not already read or run yourself."
  Because this print happens after the agent has already drafted its
  turn state (and likely some of its response), the rule operates as
  a post-hoc check: if the draft says "please run X to verify," the
  rule fires and the agent must either run X itself or rewrite. The
  `possible-verification` field at line 215 is the structured slot
  the rule targets.

- **I4 — Workflow disorientation is self-correcting within a turn.**
  Enforced by: the `workflow: <skill or workflow> step <n> | none`
  field at line 212 must be filled in before the call can be made.
  An agent that lost track of which step of a multi-step workflow
  it was on is forced to confront that gap when it tries to fill the
  field. Re-record after research (line 219) recovers state.

- **I5 — The protocol is the last action before user-facing text.**
  Enforced by: line 221 ("This should be the last thing you run. If
  you needed to call any tools (including read) afterwards, call
  `agent-tools pre_output.record` again."). The "again" clause is
  load-bearing; without it, an agent that does more tool work after
  the first call would skip a fresh commit.

**Mode = efficiency, so pairs at risk during the optimization.**

- I1 (fix loop). High risk. Any replacement that emits the commit and
  the rules in the same static prompt context loses the
  commit-then-surface ordering that makes the loop a forced step
  rather than an optional check.
- I2 (no-skip incentive). High risk. Same reason: if the rules are
  readable at the same time as the commit-block requirement, the
  agent can anticipate them and pre-trim the commit, eliminating the
  loop without paying any work-cost.
- I3 (no-punt). Medium risk. Depends on where the rule text lives in
  the replacement.
- I4 (workflow tracking). Low risk. The workflow field is just a
  field; preserving it is straightforward.
- I5 (last-action). Medium risk. If the replacement is "agent emits
  a block at start of response," there's no enforcement that another
  cycle runs after intervening tool work.

I1 and I2 are the load-bearing pairs. Step 4 must reject any option
that fails to preserve them.

> NEXT STEP:
> `agent-tools skill prompt_patch.do --step 3 --invariants=… --mode=efficiency`

---

### Step 3 — Brainstorm

Ten-plus ideas, one-liner each. Letters mark shared mechanism. Force
variety across *where the commit lives*, *what triggers the rules*,
*what enforces the loop*, and *where the ordering between commit and
rules is established*.

1. **(T)** Replace the script with a `cat <<EOF … EOF` Bash
   invocation whose stdout is the rule text; agent calls it between
   commit and response. Loop = agent restarts on violation.
2. **(H)** Add a `UserPromptSubmit` hook that prepends rules as a
   `<system-reminder>` to every user message. No loop — rules arrive
   before commit.
3. **(H)** Add a `SessionStart` hook that injects rules once per
   session.
4. **(S)** Two-block prompt protocol: commit block, then a static
   `<rules-check>` block in the prompt, then a final block. Loop =
   final block diff against commit block.
5. **(T)** Tool-stdout via a one-line `echo` of the rule text in the
   prompt (no separate file, no heredoc).
6. **(S)** Pin the rule list at the very end of the prompt, just
   before the Response template, so it is the most recent static
   content the agent reads before generating a response.
7. **(T)** Tool-call to `false` whose stderr is the rules; agent
   reads the error and restarts. (Creative but ugly.)
8. **(T)** Adversarial check tool: takes the commit as arg, prints
   `violation: X` or `ok`; agent restarts on violation.
9. **(S)** Embed the rules inside the Response template example, so
   the rule text is structurally part of what the agent reproduces.
10. **(E)** Background process tails session logs and injects warnings
    when rules are violated; agent reacts on next turn.
11. **(R)** Thinking-block requirement: before the response, the
    agent emits a chain-of-thought block listing each rule and
    confirming compliance.
12. **(N)** Eliminate the externalization entirely; keep only the
    rules as inline instructions at the top of the prompt.

**Mechanism groups.** T (tool-stdout for rules): 1, 5, 7, 8.
H (system hook): 2, 3. S (static prompt position): 4, 6, 9.
E (external process): 10. R (thinking block): 11. N (no
externalization): 12.

T is over-represented; further T variants suppressed. H, S, E, R, N
all have at least one idea. Convergence acceptable.

> NEXT STEP:
> `agent-tools skill prompt_patch.do --step 4 --ideas=…`

---

### Step 4 — Identify Target State & Workflows

**Target result state.** For each user-facing response under
`alan-default-next.md`: (a) the agent has committed a structured
turn-state block, (b) the rules have surfaced *after* the commit,
(c) any rule violation found post-commit has been resolved by
looping back through (a) → (b), and (d) `alan-default-next.md` is
self-contained — no script, no required hook config.

**Each option must contain the loop in its observable sequence.** A
strictly linear "commit, then respond" sequence cannot restore I1
and I2 and is rejected at this step.

**Option A — Cat-heredoc checkpoint with restart loop**
(from #1, lightly enriched by #6).

Observable sequence:

1. Agent finishes its tool-use work.
2. Agent emits `<turn-state>` block as the first content in its
   forthcoming response.
3. Agent calls `Bash: cat <<'EOF' … EOF` whose heredoc body is the
   rule text wrapped in a `<system-reminder>`.
4. Tool output reaches the agent's context. Agent compares the
   commit to the rules.
5. Branch:
   - **Clean.** Continue to the response body.
   - **Violation found** (Uncertainties non-empty, "please run X" in
     draft, etc.). Agent does the missing work. Restart at step 2
     with an updated commit.
6. Terminates when the latest commit is clean.

Structural invariants restored:

- I1 (fix loop): yes — the restart at step 5 IS the loop. The cat
  call is the structural artifact the loop attaches to.
- I2 (no-skip incentive): yes — the rules arrive in tool stdout
  AFTER the commit. The commit cost is already paid before the
  agent learns what the rules say. Trimming the commit changes the
  rule-check outcome only by hiding work already done; no
  work-savings.
- I3 (no-punt): yes — rule text is in the heredoc, fires the same
  way as the script's stdout.
- I4 (workflow tracking): yes — workflow field preserved in commit.
- I5 (last action): yes — cat call is the last tool before response
  body; restart rule covers intervening tool use.

Abandoned: none. Tradeoff: heredoc body takes ~10 lines of prompt
space instead of a one-line script reference. Acceptable.

**Option B — Two-block prompt protocol** (from #4, #6).

Observable sequence:

1. Agent finishes work.
2. Agent emits `<turn-state-commit>` block in the response.
3. Agent reads a static `<rules-check>` instruction immediately
   after the commit-block requirement in the prompt.
4. Agent emits `<turn-state-final>` block.
   - If the final block equals the commit block, no fix happened.
   - If it differs, the diff is the visible evidence that the agent
     fixed something.
5. Agent emits response body.

Structural invariants:

- I1 (fix loop): partial — there *is* a structural slot for the
  loop (the diff between commit and final), but nothing in the
  prompt forces the diff to exist. The agent can emit identical
  commit and final blocks without ever consulting the rules.
- I2 (no-skip incentive): weak — both the commit-block requirement
  and the rules-check sit in the same static prompt. Agent reading
  the prompt sees both before writing either, so it can anticipate
  the rules when constructing the commit. The no-work-savings
  argument breaks.
- I3, I4, I5: similar to A.

**Option C — UserPromptSubmit hook + inline commit block**
(from #2 plus a minimal inline block).

Observable sequence:

1. User submits message → harness fires the hook → hook output is
   prepended to the agent's context as a `<system-reminder>` with
   rules.
2. Agent does work.
3. Agent emits `<turn-state>` block at start of response.
4. Agent emits response body.

Structural invariants:

- I1 (fix loop): weak — no structural restart; agent has to notice
  on its own.
- I2 (no-skip incentive): *inverted*. The hook fires before any
  agent output; rules arrive before commit. Agent reading the
  hook-injected reminder can then pre-trim the forthcoming commit.
- I3, I4, I5: comparable to A on those axes, but I2 is the deal-
  breaker.

Plus: replaces script dependency with `settings.json` dependency.
The stated goal ("without a pre-output script") is met literally,
but the new mechanism still depends on something outside the prompt.

**Distinctness check.** A has a tool call between commit and rules;
B has two prompt-mandated blocks straddling a static rules section;
C has a hook-injected reminder *before* any agent output. The
temporal ordering of rule arrival relative to commit differs across
all three. Distinct.

A is the only option that structurally preserves both I1 and I2.

> NEXT STEP:
> `agent-tools skill prompt_patch.do --step 5 --target-state=… --option-a=… --option-b=… --option-c=…`

---

### Step 5 — Draft Prompt Updates Per Option

**Option A — Cat-heredoc checkpoint with restart loop.**

Replace `sys_prompt/alan-default-next.md` lines 204–221 with:

```
## Before response

Every user-facing response — including short acknowledgments like
"ok" or "done" — goes through a checkpoint protocol whose purpose
is (a) to commit your current state before the rules are re-stated,
and (b) to loop back and fix anything the rules surface.

Step 1 — commit. After your work, write this block as the first
content of your forthcoming response:

<turn-state>
Turn: <int>
Summary: <≤10 words>
Workflow: <skill or workflow> step <n> | none
Uncertainties: [unresolved observations, unverified assumptions, ...]
Verification: [commands the user can re-run to verify; you must
               have run them yourself first]
Next steps: [refactor, update docs, ...]
</turn-state>

Step 2 — checkpoint. Run this command exactly:

```bash
cat <<'EOF'
<system-reminder>
RULES — apply at this checkpoint:
- NEVER ask the user to read files or run commands that you have
  not already read or run yourself. The Verification field above
  must list commands YOU ran.
- NEVER reply while the Uncertainties field is non-empty. Do more
  research, then restart at step 1 with an updated commit.
- This is the last thing before the response body. If you do more
  tool work after this checkpoint (other than a reset call),
  restart at step 1.
</system-reminder>
EOF
```

Step 3 — fix loop. Compare your commit to the rules in the tool
output. If any rule is violated, do the missing work, then restart
at step 1 with an updated commit.

Step 4 — respond. Continue with the response body.
```

- Remove: lines 204–221 in their entirety.
- Placement: same location (just above the Response template).
- Trigger: every user-facing response.

**Option B — Two-block prompt protocol.**

Replace lines 204–221 with:

```
## Before response

Emit a `<turn-state-commit>` block with the six fields. Read the
rules in `## Pre-response rules` (immediately following this
section). Then emit a `<turn-state-final>` block — identical to
commit if no rule was violated, corrected otherwise. Both blocks
are required.
```

Add `## Pre-response rules` section below it containing the rule
text.

**Option C — UserPromptSubmit hook + inline commit block.**

Modify `settings.json` to add a UserPromptSubmit hook emitting the
rules as a `<system-reminder>`. Replace lines 204–221 with a short
inline block requirement, no rule text.

> NEXT STEP:
> `agent-tools skill prompt_patch.do --step 6 --options-drafted=…`

---

### Step 6 — Context & Conflict Check

| Question | Option A | Option B | Option C |
| --- | --- | --- | --- |
| Existing instructions that **reinforce** the change | Line 165 mentions Bash tooling as standard. Response template already mandates structured response shape. | Response template already mandates structured response shape. | Line 11 already acknowledges hooks as a system context injection mechanism. |
| Existing instructions that **contradict** the change | Line 165 ("Wrap…with-side-effects with `agent-tools run`") — `cat <<EOF` is not side-effectful, so the wrap doesn't apply. Resolved. | None directly. | The stated task is "without a pre-output script"; replacing the script with a `settings.json` hook is the same kind of out-of-prompt coupling. Contradicts the spirit of the task. |
| What can go wrong at each step of this workflow | (1) Agent skips the cat call. (2) Agent runs cat but doesn't actually compare output to commit. (3) Agent loops on an unresolvable uncertainty forever. | (1) Agent emits identical commit and final blocks without checking — the slot for the loop exists, the loop didn't fire. (2) Rules and commit-requirement sit in the same static prompt; agent can anticipate rules during the commit, losing I2. | (1) `settings.json` may be unset on a fresh deployment; the prompt then silently runs without rule injection. (2) Rules-before-commit inverts I2 by construction. |

**Hard constraint that emerged from this step.** The replacement
must preserve the *commit-before-rules* ordering as a structural
property, not as an instruction the agent might follow. Only A
meets this.

**Revisions.**

- Option A: keep. Add a "loop guard" to bound restart cycles (so
  scenario 3 in the table doesn't deadlock).
- Option B: drop. The diff between commit and final blocks is
  evidence-of-a-fix-having-happened only if the agent chose to
  fix something — the prompt does not force the diff to be
  non-trivial. I1 weak, I2 abandoned.
- Option C: drop. Inverts I2; introduces a different out-of-prompt
  dependency.

> NEXT STEP:
> `agent-tools skill prompt_patch.do --step 7 --conflicts-found=… --revisions-made=…`

---

### Step 7 — Regression Analysis

Option A only (B and C dropped in Step 6).

**Scenario 1: trivial confirmation turn ("ok," "done").**
Current behavior: agent calls `pre_output.record` with a minimal
JSON; the rule reminder still surfaces.
Risk: agent may skip the entire checkpoint protocol on a one-word
reply, treating it as too small to warrant the cat call. I1 and I2
silently fail on those turns.
Mitigation: wording "every user-facing response — including short
acknowledgments like 'ok' or 'done'" already in the draft. Also: a
one-word reply with non-empty Uncertainties is itself a rule
violation that the loop catches — so as long as the protocol runs
at all on these turns, it self-checks.

**Scenario 2: long turn with extensive tool work before final reply.**
Current behavior: agent calls record once before the final reply;
re-calls if intervening work matters (I5).
Risk: with the cat checkpoint, agent might call cat early in the
turn, then do more tool work, then respond — without a fresh
checkpoint. I5 fails.
Mitigation: the draft's "if you do more tool work after this
checkpoint, restart at step 1" already covers this. Add a positive
example in the draft: "If you call cat, then do `git log`, then
want to respond — restart, do not respond directly."

**Scenario 3: agent gets stuck in an uncertainty that cannot be
resolved with available tools.**
Current behavior: agent may loop on `pre_output.record` calls.
Risk: same in Option A — the cat call can run repeatedly without
progress.
Mitigation: add a loop guard from Step 6 revision. After three
restarts on the same uncertainty, the agent acknowledges the
uncertainty in the final commit and proceeds. Carrying an
unresolved uncertainty into the reply (visibly, in the block) is
allowed; hiding it is not.

**Scenario 4: agent calls cat then immediately responds without
reading the output.**
Current behavior: tool stdout from the script-based mechanism
carries a `<system-reminder>` block, which Claude Code (and
similar harnesses) typically elevate in attention.
Risk: cat's stdout is plain tool output; whether the harness
elevates `<system-reminder>` tags coming from tool stdout vs.
harness injection is a target-environment property.
Mitigation: include `<system-reminder>` tags inside the heredoc
body (already in the draft). Whether the elevation applies is
flagged in Step 11 and the testing plan.

**Scenario 5: asymmetric ordering (I2) preservation under various
prompt-edit attacks.**
Imagine a future maintainer who, for brevity, considers moving the
rule text from the heredoc into the static prompt above the
"Before response" section. That edit would silently break I2 — the
loop still runs, but the agent now reads the rules before writing
the commit.
Mitigation: a comment in `alan-default-next.md` (or in the
`steps.md` companion docs) noting that the *location* of the rule
text (in the heredoc, not in static prompt) is load-bearing for
I2. Out of scope for this prompt change; record as a maintenance
note.

Revisions baked into the final draft (Step 8):

- Positive examples for trivial confirmations and intervening tool
  work.
- Three-restart loop guard.
- Keep `<system-reminder>` tags inside the heredoc.

> NEXT STEP:
> `agent-tools skill prompt_patch.do --step 8 --regressions-found=… --mitigations=…`

---

### Step 8 — Pick Best Option & Full Draft

**Pick: Option A** (cat-heredoc checkpoint with restart loop).

Why over B: B's loop is structural in form (two blocks) but not in
enforcement — the agent can emit identical commit and final blocks
without ever checking. A's tool boundary makes the
commit-before-rules ordering observable and unfakeable.

Why over C: C inverts the asymmetric-ordering invariant by
injecting rules before the commit. The agent can then anticipate
the rules when writing the commit, eliminating the
no-skip-incentive property. Also re-introduces an out-of-prompt
dependency (`settings.json`), defeating the stated goal.

Why over the existing script: the rule text now lives in the
prompt file (visible to anyone reading `alan-default-next.md`),
the cat command is a POSIX built-in (no custom binary needed), and
the mechanism is otherwise structurally equivalent.

Accepted tradeoff: heredoc body takes ~10 lines of prompt space
instead of a one-line script reference. Worth it.

**Full draft** — `sys_prompt/alan-default-next.md`, replace lines
204–221 with:

```
## Before response

Every user-facing response — including short acknowledgments like
"ok" or "done" — goes through a checkpoint protocol whose purpose
is (a) to commit your current state before the rules are re-stated,
and (b) to loop back and fix anything the rules surface.

Step 1 — commit. After your work, write this block as the first
content of your forthcoming response:

<turn-state>
Turn: <int>
Summary: <≤10 words>
Workflow: <skill or workflow> step <n> | none
Uncertainties: [unresolved observations, unverified assumptions, ...]
Verification: [commands the user can re-run to verify; you must
               have run them yourself first]
Next steps: [refactor, update docs, ...]
</turn-state>

Use these exact field names. Leave a field empty if not applicable.
Do not fabricate.

Step 2 — checkpoint. Run this command exactly:

```bash
cat <<'EOF'
<system-reminder>
RULES — apply at this checkpoint:
- NEVER ask the user to read files or run commands that you have
  not already read or run yourself. The Verification field above
  must list commands YOU ran.
- NEVER reply while the Uncertainties field is non-empty. Do more
  research, then restart at step 1 with an updated commit.
- This is the last thing before the response body. If you do more
  tool work after this checkpoint (other than a reset call),
  restart at step 1.
</system-reminder>
EOF
```

The boundary between your commit and the rules is the tool call.
Do not skip it.

Step 3 — fix loop. Compare your commit block to the rules in the
tool output. If any rule is violated:

- Do the missing work (run the command, do the research, finish
  the workflow step).
- Restart at step 1 with an updated commit.

Repeat until the latest commit satisfies all rules.

Loop guard: if you restart three times on the same uncertainty
without progress, acknowledge the uncertainty in the Uncertainties
field of your final commit and proceed to step 4. Carrying an
unresolved uncertainty into the reply (visibly, in the block) is
allowed; hiding it is not.

Step 4 — respond. Continue with the response body.

If you reach the response body and notice the checkpoint was
skipped, call any tool (e.g. `Bash: true`) to reset, then restart
at step 1.
```

No other changes inside `sys_prompt/alan-default-next.md`.

> NEXT STEP:
> `agent-tools skill prompt_patch.do --step 9 --chosen-option=A --draft-written=yes`

---

### Step 9 — Deterministic Failure Mode Check

1. **Commands that may crash or silently succeed.** `cat <<'EOF' …
   EOF` is POSIX-standard with single-quoted heredoc (no shell
   expansion). Cannot crash on a sane shell. Cannot silently
   produce the wrong output — the heredoc body is literal.
2. **Impossible to follow in some situations.** The agent always
   has the Bash tool in `alan-default-next.md` contexts. The reset
   path uses `Bash: true`, also a POSIX builtin.
3. **Impossible to know when to follow.** "Every user-facing
   response" is determinable by the agent (it knows when it is
   producing user-facing output). The "violation" check is
   concrete: agent compares the rule text it just read against
   fields it just wrote.

**Environment requirements.** Bash with heredoc support (universal
on Linux/macOS/WSL). No new dependencies; the change *removes*
`agent-tools` and `claude_config.pre_output` requirements.

> NEXT STEP:
> `agent-tools skill prompt_patch.do --step 10 --deterministic-issues=none --env-requirements=bash`

---

### Step 10 — Non-Deterministic Error Check

1. **Misinterpretation (severity: medium).** "Every user-facing
   response" could be read as "every substantive response." The
   draft addresses this with "including short acknowledgments like
   'ok' or 'done'."
2. **Skipping under pressure (severity: high).** Long context,
   deep nesting, or compaction can drop the protocol from salient
   context. Mitigation: place the section immediately before the
   Response template (so it is the closest static text to the
   generation point); the reset path covers cases where the agent
   notices a skip late.
3. **Over-application (severity: low).** Agent might run the cat
   checkpoint inside subagent dispatches. Subagents have their own
   system prompts and won't carry this protocol. Risk is low.
4. **Ordering errors (severity: high).** Agent could run cat
   before emitting the commit block (mid-thinking, not as the
   response prefix). Mitigation: the draft says "as the first
   content of your forthcoming response" for the commit, and "Step
   2" for the cat call. Numbered steps make the ordering explicit.
5. **Hallucination of fields (severity: medium).** Verification
   and Next steps fields are open-ended. Mitigation: "commands YOU
   ran" wording for Verification; "Do not fabricate" instruction.
6. **Loop misuse (severity: medium).** Agent might restart on a
   rule that isn't actually violated (false positive), or fail to
   restart on a genuine violation (false negative). Mitigation:
   the three-restart loop guard caps false-positive loops; the
   commit-and-rules artifacts make false negatives auditable in
   transcripts.

All medium-and-above risks have mitigations in the draft. No
further revisions.

> NEXT STEP:
> `agent-tools skill prompt_patch.do --step 11 --risks-found=… --revisions=none`

---

### Step 11 — Top Concerns

Three concerns not already covered above.

1. **Heredoc-stdout `<system-reminder>` may not be elevated by the
   harness.** Likelihood medium. Impact medium. The original
   script-based mechanism relies on the harness elevating attention
   to `<system-reminder>` tags. Whether that elevation applies to
   tool stdout vs. harness-generated reminders is harness-specific.
   If Claude Code treats them identically, the change is
   attention-neutral. If not, the inline approach has genuinely
   lower attention at the checkpoint. Mitigation: test in the
   target harness before deploying. The testing plan in Step 12
   covers this.

2. **Rule text now lives in the prompt, not in shared code.**
   Likelihood high. Impact low. Rule changes used to mean editing
   `record.py`; now they mean editing `alan-default-next.md`.
   Other prompts that want the same protocol (`alan-default.md`,
   `output-styles/*.md`) carry their own copies. Possible
   mitigation: factor the rule list into a shared include — out of
   scope for this change.

3. **The cat call clutters session transcripts.** Likelihood high.
   Impact low. Every response shows a `cat` invocation in its tool
   log. Mitigation: none; the visibility of the checkpoint as a
   tool call is the mechanism, not a bug.

None of the three has both likelihood ≥ medium AND impact ≥ medium
that is not already addressed. Concern 1 is the closest call —
flagged in testing.

> NEXT STEP:
> `agent-tools skill prompt_patch.do --step 12 --concerns=… --final-revisions=none`

---

### Step 12 — Final Version

**File changed.** `sys_prompt/alan-default-next.md`.

**Change.** Replace lines 204–221 (the entire current "Before
response" section, beginning with `## Before response` and ending
with `…call \`agent-tools pre_output.record\` again.`) with the
draft from Step 8 (reproduced here verbatim):

```
## Before response

Every user-facing response — including short acknowledgments like
"ok" or "done" — goes through a checkpoint protocol whose purpose
is (a) to commit your current state before the rules are re-stated,
and (b) to loop back and fix anything the rules surface.

Step 1 — commit. After your work, write this block as the first
content of your forthcoming response:

<turn-state>
Turn: <int>
Summary: <≤10 words>
Workflow: <skill or workflow> step <n> | none
Uncertainties: [unresolved observations, unverified assumptions, ...]
Verification: [commands the user can re-run to verify; you must
               have run them yourself first]
Next steps: [refactor, update docs, ...]
</turn-state>

Use these exact field names. Leave a field empty if not applicable.
Do not fabricate.

Step 2 — checkpoint. Run this command exactly:

```bash
cat <<'EOF'
<system-reminder>
RULES — apply at this checkpoint:
- NEVER ask the user to read files or run commands that you have
  not already read or run yourself. The Verification field above
  must list commands YOU ran.
- NEVER reply while the Uncertainties field is non-empty. Do more
  research, then restart at step 1 with an updated commit.
- This is the last thing before the response body. If you do more
  tool work after this checkpoint (other than a reset call),
  restart at step 1.
</system-reminder>
EOF
```

The boundary between your commit and the rules is the tool call.
Do not skip it.

Step 3 — fix loop. Compare your commit block to the rules in the
tool output. If any rule is violated:

- Do the missing work (run the command, do the research, finish
  the workflow step).
- Restart at step 1 with an updated commit.

Repeat until the latest commit satisfies all rules.

Loop guard: if you restart three times on the same uncertainty
without progress, acknowledge the uncertainty in the Uncertainties
field of your final commit and proceed to step 4. Carrying an
unresolved uncertainty into the reply (visibly, in the block) is
allowed; hiding it is not.

Step 4 — respond. Continue with the response body.

If you reach the response body and notice the checkpoint was
skipped, call any tool (e.g. `Bash: true`) to reset, then restart
at step 1.
```

**Environment requirements.** Bash with heredoc support. No
`agent-tools`, `claude_config.pre_output`, or `settings.json` hook
dependency.

**Known tradeoffs (accepted).**

- Concern 1 from Step 11: if the target harness does not elevate
  `<system-reminder>` tags coming from tool stdout, attention to
  rules at the checkpoint is lower than under the script-based
  mechanism. Verify in the target harness before treating the
  change as a drop-in replacement.
- Rule text now lives in the prompt file; parallel prompts carry
  their own copies if they want the same protocol. Factoring is
  out of scope.
- Every response shows a `cat` invocation in its tool log. The
  visibility of the checkpoint as a tool call is the mechanism.

**Out of scope, follow up separately.** Once this change is in,
audit other consumers of `pre_output.record`
(`output-styles/alan-default*.md`, `sys_prompt/alan-default.md`)
and decide per-file whether to migrate them or keep the script for
those callers. After all callers are migrated, delete
`src/claude_config/pre_output/record.py`, the `pre_output.record`
subcommand in `agent-tools/src/main.rs`, and the corresponding
README entry in `output-styles/README.md`.

Also: add a maintenance note (in this file's companion CLAUDE.md
or as a comment near the rule heredoc) that the rule text *must
stay inside the heredoc*. Moving it to static prompt text breaks
I2. This is a load-bearing positioning that is not obvious from
reading the prompt alone.

**Testing suggestion.** Two-part test under the target harness.

1. *Mechanical.* Apply the change. Start a fresh session under
   `alan-default-next.md`. Send three prompts: substantive
   ("explain X"), trivial ("ok"), and one that should surface an
   uncertainty (e.g., "is foo defined in bar.py?" without giving
   the agent access to bar.py). For each, verify the response
   begins with a `<turn-state>` block, the session log contains a
   `cat` tool call with the expected stdout, and on the third
   prompt the agent loops (either resolves by reading bar.py, or
   carries the uncertainty into the final block with a clear
   acknowledgment).
2. *Attention.* On a turn with a deliberate rule violation
   pre-injected in the commit (e.g., "Verification: tell the user
   to run pytest"), observe whether the agent restarts at step 1
   after the cat call (passing) or proceeds to respond as-is
   (failing — indicates concern 1 from Step 11 is real for this
   harness, and the heredoc `<system-reminder>` is not elevated).

Done.

---

## Notes from this run (for steps.md maintainers)

These observations are about the *workflow*, not the example.

- **Invariant quality is load-bearing for everything downstream.**
  A first-pass attempt at Step 2 produced shallow pairs of the form
  "a block of fields exists at the start of the response," which
  led Step 4 to generate linear single-pass options. None of those
  options preserved the loop or the asymmetric ordering — and Step
  6 had no hard constraint to reject them on. The strong invariants
  are about *relationships between steps* (commit→rules ordering,
  restart loop, no-work-savings from under-reporting) rather than
  about the existence of any single artifact. The `steps.md` prompt
  for Step 2 currently illustrates the pair shape but does not push
  the agent to look for *relationship invariants*. Consider whether
  the Step 2 prompt should ask "what relationships between agent
  steps does the current mechanism guarantee?" as a separate axis
  from "what artifacts must exist?" — but verify that's general,
  not just an artifact of this example.

- **Linear options are the failure mode for Step 4 on
  loop-containing mechanisms.** If the mechanism being optimized
  contains a loop, every option must embed the loop in its
  observable sequence. An option that is a flat sequence of agent
  emissions is structurally incapable of replacing a looping
  mechanism, and should be rejected at Step 4 rather than carried
  into Step 5 and Step 6. The `steps.md` prompt for Step 4 says
  options must differ in "temporal sequence" but does not say
  options must *contain* the structural features of the mechanism
  being replaced. Consider adding that constraint — but verify
  this is general.

- **The "structural property vs aspirational instruction"
  distinction.** Option B in this run had a slot for the loop
  (commit + final blocks) but no enforcement that the loop fired.
  This is a common failure mode: a prompt-edit can introduce the
  *shape* of an invariant without introducing its *enforcement*.
  Step 2's "Enforced by: NOT 'the agent does X' — that is a
  deterministic-instruction claim, not an enforcement" guidance
  already names this trap. Worth verifying that Step 6 prompts
  push for the same distinction when evaluating options.

- **Step 6's hard-constraint output is where load-bearing
  invariants get teeth.** In this run, "commit-before-rules
  ordering must be structural" emerged as a hard constraint at
  Step 6, and Options B and C both failed it. Without this
  hard-constraint step, both would have survived into Step 7 or
  Step 8 and the wrong option could have been picked.

- **Step 7's "3+ scenarios" minimum is easy when invariants are
  strong.** Each invariant generates at least one regression
  scenario (one per pair); the 3-minimum is trivial. With weak
  invariants, agents may pad with low-value scenarios to hit the
  threshold. The 3-minimum feeling forced is a tell that Step 2
  was thin.

- **Step 11 vs Step 10 separation worked.** Step 10 caught
  agent-side mistake modes (skipping, ordering, hallucination);
  Step 11 caught system-side / environmental concerns (harness
  elevation behavior, rule duplication across files, transcript
  clutter). The "novel concerns not covered" framing of Step 11
  is a useful filter.

- **Out-of-scope artifacts surfaced naturally in Step 12.** The
  agent flagged `output-styles/*.md` and the Rust subcommand as
  follow-up cleanup without being prompted to. Also surfaced: a
  load-bearing positioning constraint (rule text must live in the
  heredoc, not the static prompt) that future maintainers need to
  know about. If Step 12 explicitly required an "out-of-scope
  follow-ups and maintenance notes" section, this would become
  reliable rather than best-effort.
