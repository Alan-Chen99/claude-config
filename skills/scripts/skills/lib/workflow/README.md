# Workflow framework

What the code here does not say. The execution model is in `CLAUDE.md`.

## Discovery

`discover_workflows("skills")` imports every module under `skills/` outside
`lib/` and keeps each module-level `WORKFLOW` that is a `Workflow`. One import
error anywhere fails the whole call, which lists every failing module. A skill
that defines no `WORKFLOW` is invisible to it, so the step tests skip that
skill. deepthink, decision-critic, problem-analysis and codebase-analysis are
among those skills.

## Question relay

`constants.py` holds both halves. `SUB_AGENT_QUESTION_FORMAT` goes into a
sub-agent's prompt and `QUESTION_RELAY_HANDLER` into the dispatching step. The
planner skill's `INTENT.md` (`skills/planner/` at the repo root), "Question
Relay", has the flow. The protocol has this shape for three reasons:

- The orchestrator reinvokes a questioning sub-agent fresh and never resumes
  it, because resumed sub-agents came back with 0 tokens and 0 tool uses. So
  the sub-agent saves its state to `plan.json` before it yields, and its
  script's step 1 detects the continuation.
- The `<needs_user_input>` block is the whole response. Detection is then a
  tag match and never a guess at question marks in prose.
- The limits (3 questions, 2-3 options, a 12-character header) sit inside
  AskUserQuestion's schema, since the relay passes the fields through.
