---
name: prompt-engineer-v2
description: Use whenever authoring, editing, reviewing, or reasoning about instructions, prompts, agent definitions, SKILL.md files, system prompts, CLAUDE.md files, or any other text that becomes part of an LLM's context. Provides foundational principles to keep in mind. Includes an optional "patch mode" script for difficult prompt edits — invoke patch mode only when the user requests it or when the change is complex enough to need the full structured workflow.
---

# Prompt Engineer v2

This skill is **context, not a workflow**: keep it in mind for the whole task.
It is also **advice, not rules**: every item here, principle or check, is
non-binding; weigh each against the text at hand and set aside what does not
fit. Nor is it complete: a text that passes every check can still fail.

## Principles

- **Readers differ in what they can see.** After compaction an agent has a
  summary, a subagent or new session nothing: write for the reader who will
  have the text in front of it.
- **Prompts are code, run by an agent that errs.** They must work, stay
  maintainable and observable, propagate errors, and let it discover and recover
  from mistakes.
- **Every character is an instruction.** Keep framing minimal. Maintainer
  notes read to the agent as instructions; keep them in one place all
  maintainers find, such as a companion CLAUDE.md.
- **Fix invariants, not symptoms.** Rule out deterministic failures, then find
  the broken pair: a structural property and the enforcement giving it teeth,
  like "no single point of failure" enforced by "output passes 3 parallel
  reviewer runs". If a reviewer skipped a check on X, restore the 3-run
  guarantee, not X: fixing X masks the broken pair, so X′ fails next. Test each
  property: if a naive design that merely emits the named artifact (a block, a
  tool call) satisfies it, restate it as a relationship between steps
  (ordering, feedback loop, dependency).
- **A failing line is evidence about the line.** Before adding anything, find
  why the existing text failed (unseen, misread, outweighed, misleading) from a
  transcript or a reproduction, or mark the cause unverified. Then fix that
  text: a new guard beside it unchanged leaves the cause to misfire where no
  one watches.
- **Code is no more reliable than a prompt.** A hook or script is written by an
  agent as fallible as the one it guards, freezing a possibly nuanced condition at write
  time. It looks infallible only to its author: on the cases no one anticipated,
  which always exist, it is typically worse than a reader's judgment. Keep it
  for truly mechanical conditions. A prompt paired with code acts on the code's
  verdict: check what the agent does when the code fires wrongly or stays silent.
- **TDD for prompts.** When the broken enforcement is itself a check, test or
  review, fix only it; defer what it reviews until a real run shows it catching
  the failure: patched symptoms would hide whether it works.
- **Removal needs permission the agent can see.** Adding costs an edit, removing
  a search for dependents, and no line shows if it is three steps or three years
  old, so agents only add. Pair each step that can add artifacts with one that
  removes them as confidently: a stated safe-to-remove rule, a diff against a
  named commit, or a prune step enumerating candidates. **Someone must do it**:
  a workflow gives every routine task, destructive ones included, to an agent
  with a safe procedure, not to the human.

## Checks for each edit

**Deterministic failures first**: they occur even under perfect obedience.
Commands crashing or exiting 0 with wrong output, steps needing absent state
or tools, "if X" with X uncheckable, underspecified specs, dangling pointers,
context missing or late. Then misreading, skipping under pressure, over-applied
triggers, misordering, hallucinated verification.

### The rule

- **Needed?** A rule guarding no failure, because the agent would not make it
  unprompted or another line already prevents it, is cost only.
- **What, not how.** A prescribed method is also a claim that its steps are
  right and enough, so the reader stops at them. State the outcome; give steps
  only where the reader cannot derive them.
- **What goes stale?** A count, a version, a path, "currently": write what
  stays true, or how to look it up.

### Where it fires

- **Rules need triggers, not just procedures.** "If git blame shows a function
  is new, remove it" fires zero times: nothing says which functions to check.
  Cover a defined set unconditionally, or have a step enumerate the candidates.
- **Fires in the right places?** Too broad reaches cases it was not written
  for. Too narrow, when a failure motivates the edit, is scoped by the case
  instead of the invariant: words lifted from the case, categories mapping 1:1
  onto its failures, examples mirroring it (pre-existing wording exempt),
  artifact-type or domain framing narrower than the invariant ("your *code*
  must…" when it covers prose). Examples span domains, at least one the case
  does not touch.
- **Where does obeying it do harm?** An edge case, or a case where its fixed
  action is wrong and the reader sees no way out. Narrow the condition, name
  the exception, or state the goal the rule serves so the reader can serve it
  when the rule would not.

### Who reads it

- **Readers you did not picture.** An agent on another task that the text
  still binds (an autoloaded skill, an inherited CLAUDE.md, a shared system
  prompt), or one arriving with another framing (a summary, a subagent brief,
  another skill's vocabulary): read each line as they would. Which readings
  does it admit, and where does it misfire?
- **Which claims will a reader on another task take as a premise?** A
  statement written as plain fact is read as usable for any action, not only
  the one it was written for.

### What it leaves out or hides

- **Does the text shrink the job unseen?** "Review X" read as "look only at
  X"; "do not touch the tests" read as "and do not report the test this
  breaks"; a step list read as the whole job; cross-cutting work the task
  implies (tests, docs, error paths, cleanup, the message to whoever waits on
  the result) left to no one. Routine work goes to an agent (someone must do
  it); anything else the agent reports undone instead of dropping.
- **What does the user never see?** A rule that changes what the user gets
  with no visible act, such as a filter, a default, a "never do X" the user
  wants this time, runs unnoticed until it costs them. Make its effect visible
  to them, or ask.

### Testing the edit

- **Regressions**: name ≥3 scenarios where current behavior is correct and how
  the change could break each.
- **Cold read by a fresh subagent**, the test for the reader checks: give it
  the full edited prompt and the invariant, never the failing case, its text or
  failure mode; ask what narrows below the invariant and which lines it reads
  otherwise than meant. Revise the prompt on each finding and re-review.
- Running cases or reading transcripts? First read this skill's
  `experiments.md`.

## Patch mode

Only for multi-invariant rewrites, a non-obvious regression surface, or on user
request: run the script and follow each `NEXT STEP`.

<invoke cmd="agent-tools skill prompt_engineer_v2.do --step 1" />
