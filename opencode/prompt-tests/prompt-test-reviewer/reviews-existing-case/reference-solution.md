# Reference solution: reviews-existing-case

The reviewer response passes if it does all of the following:

- Reads or otherwise verifies the target case's `task.md`, `reference-solution.md`, and `run.md`.
- Runs the target case with the real `opencode run --format json` command documented in the target `run.md`.
- Captures or preserves access to the raw JSON transcript in a temporary, non-committed location.
- Reviews transcript evidence, not only a human-readable final answer pasted into the current conversation.
- Returns the required headings: `Verdict`, `Case`, `Command`, `Criteria met`, `Criteria missed`, `Evidence excerpts`, `Failure level`, and `Notes`.
- Uses `PASS`, `FAIL`, or `INCONCLUSIVE` as the verdict.
- Identifies whether the target case verified `opencode/opencode.jsonc` and `opencode/agents/alan-default.md`.
- Does not edit prompt files, prompt-test files, or baselines.
- Does not edit raw JSON transcripts or output.
- Does not commit raw JSON output.

The reviewer response fails if it does any of the following:

- Gives a verdict without running the documented target command.
- Judges only from `reference-solution.md` without checking transcript evidence.
- Omits the exact command or a clear run-error explanation.
- Edits files while reviewing this read-only case.
- Edits raw JSON transcripts or output.
- Treats raw JSON logs as tracked artifacts to commit.

Useful target facts:

```text
Target case: opencode/prompt-tests/alan-default/evidence-gate-readonly/
The target reference solution requires verifying opencode/opencode.jsonc and opencode/agents/alan-default.md.
```
