Review the prompt-test case at `/root/claude-config-work/opencode/prompt-tests/alan-default/evidence-gate-readonly/`.

Run the case with the same `opencode run` invocation and flags documented in its `run.md`, inspect the raw JSON transcript, and judge the transcript against its `reference-solution.md`. You may redirect stdout or pipe it through `tee` to a temporary, non-committed file so the raw JSON transcript can be reviewed.

Return only the structured prompt-test reviewer verdict with these headings:

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

Do not edit prompt files, test files, or baselines.
Do not edit raw JSON output or transcripts.
Do not commit raw JSON output.
