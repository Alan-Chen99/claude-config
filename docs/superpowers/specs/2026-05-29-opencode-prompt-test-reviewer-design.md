# opencode prompt-test reviewer - Design

Status: approved
Date: 2026-05-29

## Purpose

Add a lightweight reviewer workflow for existing opencode prompt tests. The
reviewer runs one prompt-test case with the real `opencode` binary, inspects the
raw JSON transcript, and returns a structured semantic verdict against the
case's `reference-solution.md`.

This improves the prompt-test feedback loop without changing live agent behavior
or replacing the existing plain Markdown test format.

## Scope

In scope:

- A reusable subagent-oriented review contract for one prompt-test case.
- Running the command documented by the case's `run.md`.
- Capturing raw JSON output in a temporary, non-committed location.
- Reviewing final answers, tool calls, intermediate assistant text, and gate
  heredoc content when present.
- Returning `PASS`, `FAIL`, or `INCONCLUSIVE` with evidence excerpts and missed
  criteria.

Out of scope:

- Runtime enforcement in `opencode.gate`.
- Prompt changes to `opencode/agents/alan-default.md`.
- A full automated test harness or exact-output golden comparison.
- Committing raw JSON logs by default.
- Updating `baseline.md` automatically.

## Existing test format

The reviewer operates on the existing prompt-test layout:

```text
opencode/prompt-tests/
  <agent-name>/
    <case-name>/
      task.md
      reference-solution.md
      run.md
      baseline.md
```

`run.md` remains the source of truth for the exact `opencode run` command.
`reference-solution.md` remains the semantic source of truth for pass/fail
criteria. The reviewer adds execution and review discipline; it does not change
the case file contract.

## Reviewer contract

Input:

- Absolute or repo-relative prompt-test case directory.
- Optional model override, only when the caller explicitly asks for one.

Responsibilities:

- Read `task.md`, `reference-solution.md`, and `run.md`.
- Execute the documented `opencode run --format json` command from the repo root.
- Store raw JSON output under an ignored temporary location such as `/tmp` or a
  repo-local ignored temp path.
- Parse enough of the transcript to identify final answer text, tool calls,
  intermediate assistant messages, and any `agent-tools opencode.gate` heredoc
  drafts.
- Compare the transcript to `reference-solution.md` semantically.
- Report whether failures are final-answer failures, tool-use/evidence failures,
  intermediate-reasoning failures, or gate-draft failures.

Non-responsibilities:

- Do not edit prompt files.
- Do not edit test files or baselines unless the caller explicitly asks.
- Do not commit files.
- Do not treat visible wording similarity as sufficient evidence when the
  reference solution requires provenance or source-of-truth evidence.

## Verdict format

The reviewer returns a compact structured result:

```text
Verdict: PASS | FAIL | INCONCLUSIVE

Case: <case-path>
Command: <exact command run or why it could not be run>

Criteria met:
- <brief criterion>

Criteria missed:
- <reference-solution criterion>

Evidence excerpts:
- <tool call, final answer, or gate draft excerpt>

Failure level:
- none | final-answer | tool-use | intermediate-reasoning | gate-draft | run-error

Notes:
- <ambiguity, truncation, or follow-up needed>
```

`INCONCLUSIVE` is reserved for cases where the run fails, output is truncated, or
the transcript does not contain enough information to judge a required criterion.

## First validation cases

The first version should be validated against existing cases:

- `opencode/prompt-tests/alan-default/evidence-gate-readonly/`: confirms the
  reviewer can identify whether required local evidence files were verified.
- `opencode/prompt-tests/alan-default/report-item-provenance/`: confirms the
  reviewer can detect whether provenance was based on `provenance.json` rather
  than visible checklist text.
- `opencode/prompt-tests/alan-default/superpowers-startup-reasoning-chain/`:
  confirms the reviewer can flag the known provenance failure where visible
  labels, headings, or paths are treated as proof of origin.

## Error handling

- If `opencode run` exits non-zero, return `INCONCLUSIVE` unless the reference
  solution defines the run error itself as the failure under test.
- If raw output is too large for the tool output window, record the path where it
  was captured and inspect targeted sections from that file.
- If `run.md` contains multiple command variants, use the primary command unless
  the caller selected a model override or variant.
- If the documented command is stale or invalid, report the exact command and
  error instead of silently repairing it.

## Future extensions

Deterministic checks can be added later for objective requirements, such as
whether a transcript includes a read of `fixture/provenance.json`. Those checks
should complement the semantic reviewer, not replace it.

Runtime fixes, such as an `opencode.gate` provenance enforcement path, should be
designed separately after the reviewer can reliably identify prompt-test
failures.
