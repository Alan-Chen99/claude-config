---
name: prompt-engineer-v2
description: Use whenever writing, editing, reviewing or reasoning about text that becomes part of an LLM's context (prompts, agent definitions, SKILL.md, CLAUDE.md, system prompts).
---

# Prompt Engineer v2

This skill is **context, not a workflow**: keep it in mind for the whole task.
It is also **advice, not rules**: not every item applies to every task, but
the reason beneath each does, and adapting the item to your task is your job. Nor is it complete: a text that passes every check can still fail.

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
- **Fix invariants, not symptoms.** Find the broken pair: a structural
  property and what holds it. Test each property: if a naive design that merely
  emits the named artifact (a block, a tool call) satisfies it, restate it as a
  relationship between steps (ordering, feedback loop, dependency).
- **A failing line is evidence about the line.** A request to add a rule
  usually reports a failure. Before adding anything, find the text that should
  have prevented it and why it failed (unseen, misread, outweighed, misleading)
  from a transcript or a reproduction, or mark the cause unverified. Then fix that
  text: a new guard beside it unchanged leaves the cause to misfire where no
  one watches.
- **Fixed rules and judgment fail differently.** Fixed where the condition is
  mechanical, judgment where it is nuanced; a failing fixed rule may need
  loosening, failing judgment a check. A mechanical condition is still the
  author's guess at every case: give a fixed rule a visible way out. Where both
  act, check each side when the other errs: a check firing wrongly or silent, a
  reader overriding a correct check.
- **TDD for prompts.** When the broken enforcement is itself a check, test or
  review, fix only it; defer what it reviews until a real run shows it catching
  the failure: patched symptoms would hide whether it works.
- **Removal needs permission the agent can see.** Adding costs an edit, removing
  a search for dependents, and no line shows if it is three steps or three years
  old, so agents only add. Pair each step that can add artifacts with one that
  removes them as confidently: a stated safe-to-remove rule, a diff against a
  named commit, or a prune step enumerating candidates.

## Checks for each edit

**Failures under perfect obedience first.** Commands crashing or exiting 0
with wrong output, steps needing absent state or tools, "if X" with X
uncheckable, underspecified specs, dangling pointers, context missing or late.
Then misreading, skipping under pressure, misordering, hallucinated
verification.

A remedy in this skill, or a reviewer's finding, that adds or tightens a rule,
or adds an exception, beyond the user's words is a question for them, not an
edit: see "What does the user never see?".

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
  Cover a defined set, have a step enumerate the candidates, or name a moment
  in the work where the case is already in front of the reader.
- **Fires in the right places?** Too broad reaches cases it was not written
  for. Too narrow, when a failure motivates the edit, is scoped by the case
  instead of the invariant.
- **Where does obeying it do harm?** An edge case, or a case where its fixed
  action is wrong and the reader sees no way out, for a hook or script too.
  Narrow the condition, name the exception, give a visible override, or state
  the goal the rule serves so the reader can serve it when the rule would not.
  Mirror: where does leaving it to judgment do harm? A mechanical condition
  readers keep getting wrong wants a check.

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

- **Does the text shrink the job unseen?** Look for cross-cutting work the task
  implies (tests, docs, error paths, cleanup, the message to whoever waits on
  the result) left to no one. **Someone must do it**: a workflow gives every
  routine task, destructive ones included, to an agent with a safe procedure,
  not to the human; anything else the agent reports undone instead of dropping.
- **What does the user never see?** A rule that changes what the user gets
  with no visible act, such as a filter, a default, a "never do X" the user
  wants this time, or a judgment call made silently, runs unnoticed until it
  costs them. Make its effect visible to them, or ask. A rule stricter than
  the loosest reading of the user's words, or a hard rule or an exception they
  never asked for, is hidden whatever its effect: before adding it to its file,
  in any checkout, show them its exact text and ask. Their request for
  something like it, or your mention after adding, is not their yes. Asking
  costs one reply; a hidden rule or exception changes what every later reader
  does.

### Testing the edit

- **Regressions**: name ≥3 scenarios where current behavior is correct and how
  the change could break each.
- **Cold read by a fresh subagent**, the test for the reader checks: give it
  the full edited prompt, copied away from maintainer notes (read in place, a
  nearby CLAUDE.md can load with it), and the invariant, in the user's words
  where they gave it, never the failing case, its text or failure mode; ask
  what narrows below the invariant or reaches past it and which lines it reads
  otherwise than meant, and, for each fixed rule, what the reader can do from
  the text it sees when the user explicitly asks for the other action, and who
  sees it. Revise the prompt on each finding, putting new or tightened rules, new
  exceptions, and approved rules reworded, to the user first, and re-review.
- Running cases or reading transcripts? First read this skill's
  `experiments.md`.

## Patch mode

Only for multi-invariant rewrites, a non-obvious regression surface, or on user
request: run the script and follow each `NEXT STEP`.

<invoke cmd="agent-tools skill prompt_engineer_v2.do --step 1" />
