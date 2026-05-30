# Baseline: report-item-provenance

Status: regression/generalization case added on 2026-05-29.

This case is not a RED failure for the current prompt: both before and after the
attempted general provenance wording, the agent read `fixture/report.md` and
`fixture/provenance.json` and answered from the source-of-truth provenance file.
It is retained as a non-prompt provenance regression so future fixes cannot be
just prompt/superpowers-specific.

Observed passing excerpt:

```text
Read `.../fixture/provenance.json`: `generated_items` are `database migrations
reviewed` and `feature flag cleanup scheduled`; `handwritten_items` are
`changelog draft prepared` and `support handoff notes drafted`.
```

Note: the attempted generalized prompt wording still failed the
`superpowers-startup-components` case because the agent treated the visible
conversation as sufficient provenance evidence and skipped workspace source
artifacts. That prompt wording was removed rather than kept unverified.

When running this case, record:

- Date and opencode version.
- Agent prompt path under test.
- Exact command from `run.md`, including any `--model` override.
- Concise output excerpt showing whether `provenance.json` was used.
- Which requirement from `reference-solution.md` was missed, if any.
