# session-analysis

Post-hoc analysis of agent session logs (opencode exports and Claude Code
JSONL): focus-directed evidence artifacts and task answers over one or more
sessions.

This skill merges the skills formerly known as `diagnose-session` and
`session-timeline` into one skeleton-first, two-mode workflow. The
diagnose-session category machinery was removed after method comparison
showed it trades salient detection for systematic negatives; its working
mechanics live on as protocol rules (self-report verification, workflow
completion, large-output rule).

## Design Rationale

Self-reporting (Required notes) has systematic blind spots:

- **corrected-mistake** is under-reported (self-serving bias — agents avoid
  reporting their own errors)
- **tool-issue** is under-reported (agents work around tool problems without
  flagging them)
- **suspected-user-mistake** is under-reported (agents notice issues but don't
  flag them, especially when the agent was initially wrong)

External inspection complements self-reporting because it has different strengths:

| Category | Self-reporting | External inspection |
|----------|---------------|-------------------|
| hidden-challenge | Good (agent knows what was hard) | Poor (hard to detect from log) |
| suspected-user-mistake | Poor (self-serving bias) | Medium (requires context) |
| corrected-mistake | Poor (self-serving bias) | Good (error→revision visible) |
| tool-issue | Poor (agents work around it) | Good (✗ markers, errors visible) |
| context-waste | Poor (agents don't notice) | Good (repeated reads visible) |

## Limitations

- Supports both Claude Code JSONL and opencode session exports. Both
  harnesses are read via the shared skeleton-first reading protocol (see
  SKILL.md).
- Cannot detect hidden-challenge reliably (requires real-time reasoning context)
- Cannot detect suspected-user-mistake without understanding user's full intent
- Single-pass analysis: no iterative deepening on ambiguous findings
- Thinking-block findings depend on the model's internal reasoning patterns;
  different models may surface concerns differently

## Relationship to Self-Reporting

This skill is additive, not a replacement. The hybrid approach:
1. Improved self-reporting instruction (`conventions/agent-responses.md`)
   adds backward-scan, forcing questions, and relabeling override to reduce
   systematic under-reporting
2. session-analysis (task mode, or evidence mode + parent synthesis) catches
   what the agent still missed or miscategorized
3. Together they provide more complete coverage than either alone
