---
name: prompt-engineer-v2
description: Use whenever writing, editing, reviewing or reasoning about text that becomes part of an LLM's context (prompts, agent definitions, SKILL.md, CLAUDE.md, system prompts).
---

# Prompt Engineer v2

This skill is **context, not a workflow**: keep it in mind for the whole task.
It is also **advice, not rules**: every principle and check is non-binding;
weigh each against the text at hand and set aside what does not fit. Nor is it
complete: a text that passes every check can still fail. Of this skill, only the
next section binds.

## Rules beyond the user's words

No rule reaches standing text unless the user's words require all of it or the
user first approved its exact text.

- **Rule:** text telling later agents what they must, must not or may only do,
  in any form (a default, a preference stated as fact) or place (prompt, doc,
  memory, script output), or a hook or check enforcing one on them. A fact
  setting no convention is not one; a choice among working options is. A brief
  or plan used only in its task is not one.
- **Needs approval:** a rule you write, or brief an agent to write, that is new
  to its file, tighter, read more widely, or stripped of a hedge or limiting
  condition, unless the least demanding reading of the user's own words
  requires every must, scope and step of it. Words naming a source to copy
  require its text unchanged; a standing order to record rules approves
  none. Loosening or deleting a whole rule needs none.
- **Approval:** the user's yes to the exact text, shown apart from other
  changes (a hook or check: what it matches, does and says); approving a plan
  or diff approves no text. Write it as approved, or ask again. Unable to ask,
  leave it out and report its text as awaiting approval.
- **User's words:** only text shown verbatim as theirs or as approved, never a
  summary's gist; a briefer relays rules a subagent reports to the user
  verbatim. No agent approves or waives.
- **Waiver:** the user's explicit leave to add rules unreviewed, for the task or
  the span they name; "don't stop" is not one. Rules written under it are
  still reported verbatim.

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
- **A failing line is evidence about the line.** Before adding anything, find
  why the existing text failed (unseen, misread, outweighed, misleading) from a
  transcript or a reproduction, or mark the cause unverified. Then fix that
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
  costs them. Make its effect visible to them, or ask.

### Testing the edit

- **Regressions**: name ≥3 scenarios where current behavior is correct and how
  the change could break each.
- **Cold read by a fresh subagent**, the test for the reader checks: give it
  the full edited prompt and the invariant, never the failing case, its text or
  failure mode; ask what narrows below the invariant and which lines it reads
  otherwise than meant, and, for each fixed rule, what the reader can do from
  the text it sees when the user explicitly asks for the other action, and who
  sees it. Revise the prompt on each finding and re-review.
- Running cases or reading transcripts? First read this skill's
  `experiments.md`.

## Patch mode

Only for multi-invariant rewrites, a non-obvious regression surface, or on user
request: run the script and follow each `NEXT STEP`.

<invoke cmd="agent-tools skill prompt_engineer_v2.do --step 1" />
