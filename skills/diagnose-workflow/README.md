# diagnose-workflow

Structural extraction of sub-agent workflow data from Claude Code JSONL logs.

## Design Rationale

Built as part of a multi-iteration observability evaluation (DEC-002). The core
insight: **self-reporting cannot be the primary observability mechanism for
multi-agent workflows** because:

1. Dead agents (API errors) cannot self-report — 4/10 agents in session 2129515e
2. Parent agents miscount — claimed 7/3 success/fail, actual was 6/4
3. Truncated sessions produce zero reporting — session 1d245d22 ended mid-dispatch
4. Self-serving bias — agents under-report their own inefficiency

## Approach: Two-Tier Structural Extraction

**Tier 1**: Main-log-only extraction via `agent-tools cc-workflow`.
Parses Agent tool_use/tool_result pairs for ground-truth metrics: tokens, tool
counts, durations, completion status. Zero compliance dependency — reads existing
artifacts, requires no agent cooperation.

**Tier 2**: Sub-agent JSONL drill-down for investigating Tier 1 anomalies.
Reads `<session-id>/subagents/agent-<id>.jsonl` for internal tool sequences,
file coverage, retry patterns, error timelines, and Bash command previews.
Invoked via `--tier2 [all|anomalies|<index>]`.

## Validation Results

Tested across 40+ fresh sessions over 4 independent verification rounds (iters
4, 8, 10, 13). Deep-verified 15+ agents by manually counting tool calls from
raw JSONL — 100% accuracy in all cases.

| Metric | Self-Reporting | Structural Extraction |
|--------|---------------|----------------------|
| Availability | Requires agent completion | Always available |
| API error detection | Cannot (agent dead) | 100% |
| Missing result detection | Cannot (no output) | 100% |
| Parent miscount detection | n/a | Catches discrepancies (e.g., claimed 3 errors, actual 4) |
| Truncated session coverage | Zero output | Full agent dispatch data |
| Overlap with self-reporting | Content-level findings | Structural findings — zero redundancy |

## Known Limitations

- Cannot detect parent-level dropped work (items discussed but never delegated).
  Use `session-analysis` (diagnose mode) for content-level analysis.
- Content summaries for `Explore`-type subagents show intermediate reasoning
  rather than structured results. The first-line summary is less useful for these.
- Does not assess quality of agent outputs — only structural success/failure.
