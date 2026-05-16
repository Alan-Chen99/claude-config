---
name: diagnose-workflow
description: Extract structural sub-agent workflow summary from a Claude Code session log. Shows what agents ran, succeeded/failed, token usage, and anomalies — without relying on self-reporting.
---

# Diagnose Workflow

Structural extraction of sub-agent workflow data from Claude Code JSONL logs.
Unlike self-reporting, this reads ground-truth data from the log itself — agent
dispatch parameters, completion status, token counts, tool usage, and durations.

## Usage

```
/diagnose-workflow path/to/session.jsonl
```

## Why This Exists

Self-reporting (Required notes) has systematic failures for multi-agent workflows:
- Dead agents (API errors) cannot self-report
- Parent agents miscount successes/failures
- Truncated sessions produce zero self-reporting
- High tool counts (retries) and long-running agents go unmentioned

Structural extraction catches all of these because it reads what actually happened,
not what the agent claims happened.

## Workflow

### Step 1: Run structural extraction

```bash
agent-tools cc-workflow <FILE>
```

Read and present the output to the user.

If the script reports "No Agent tool calls found in this session", tell the user
and stop — this session has no sub-agent workflow to diagnose.

### Step 3: Run JSON extraction for programmatic analysis

If you need to reason about the data (e.g., for comparison or deeper analysis):

```bash
agent-tools cc-workflow <FILE> --json
```

### Step 4: Interpret and present findings

Present findings in this format:

```
## Workflow Diagnosis: <session-id>

### Agent Summary
<paste the table output from Step 2>

### Anomalies
For each anomaly, explain its impact:
- **ERROR**: Agent died — its assigned work was not completed. The parent
  may have reported this, or may have silently continued without it.
- **MISSING_RESULT**: Agent was dispatched but no result was ever recorded.
  Session may have been truncated, or the agent hung.
- **HIGH_TOOL_COUNT**: Agent used significantly more tools than peers
  (>40). May indicate retries, errors, or scope creep within the agent.
- **LONG_RUNNING**: Agent took >5 minutes. May indicate complex work or
  repeated failures.
- **ZERO_TOKENS**: Agent completed but recorded 0 tokens. Unusual — may
  indicate a recording error or rejected agent.

### Coverage Assessment
- What categories/areas were assigned to agents?
- Which succeeded vs failed?
- Is there a gap — work that should have been done but wasn't covered?

### Comparison to Self-Reporting (workspace sessions only)
If this is a workspace session, also check the assistant text for:
1. Does the parent mention how many agents succeeded/failed?
2. Does the parent's count match the structural data?
3. Are anomalous agents mentioned in Required notes?
```

### Step 5: Tier 2 drill-down (when anomalies need investigation)

When Tier 1 reveals anomalies (API errors, high tool counts, missing results),
drill into the sub-agent's internal JSONL to understand what happened:

```bash
# Drill down into all anomalous agents (default)
agent-tools cc-workflow <FILE> --tier2

# Drill down into ALL agents (including healthy ones)
agent-tools cc-workflow <FILE> --tier2 all

# Drill down into a specific agent by index (1-based)
agent-tools cc-workflow <FILE> --tier2 3
```

The drill-down report shows per-agent:
- **Tool breakdown**: which tools the agent called and how many times
- **Bash commands**: actual commands the agent ran (top 5)
- **Files touched**: what files the agent actually read/edited (excludes internal tool-results artifacts)
- **Repeated operations**: same tool+target called multiple times (indicates retries or broad search)
- **API errors**: errors encountered inside the agent
- **Failed tool calls**: tool invocations that returned errors
- **Expected non-zero exits**: diff/grep exit 1 (normal behavior, separated from real failures)
- **Progress assessment** (for failed agents): how far the agent got before dying

Use Tier 2 when you need to answer:
- "Did the failed agent do any useful work before dying?"
- "Why did this agent use so many tools?"
- "What files did the agent actually look at?"

### Step 6: Anomalies-only mode (optional)

For quick triage of sessions with many agents:

```bash
agent-tools cc-workflow <FILE> --anomalies-only
```

### Interpreting Tier 1 output

- **Tokens = N/A**: Agent did work (tool calls > 0) but reported 0 tokens. Typical
  for API-errored agents that completed tool calls before dying.
- **DISPATCH BATCHES**: Groups of agents dispatched in the same assistant message
  (concurrent). If absent, all agents were dispatched sequentially.

## Rules

1. Always run the extraction script — do NOT attempt to parse JSONL manually.
2. Do NOT use subagents. This skill runs as a single analysis pass.
3. When the parent's reported counts disagree with structural data, the
   structural data is ground truth. State the discrepancy explicitly.
4. For sessions with 0 anomalies: say so clearly. A clean workflow is a
   valid and useful finding.
5. Content summaries for `Explore`-type subagents may show intermediate
   reasoning text rather than structured results. This is a known limitation —
   note it but do not treat it as an anomaly.

## Relationship to diagnose-session

| Aspect | diagnose-session | diagnose-workflow |
|--------|-----------------|-------------------|
| **What it reads** | Rendered conversation text | Raw JSONL structure |
| **What it finds** | Unreported Required notes items | Agent success/failure, anomalies, resource usage |
| **Scope** | All conversation activity | Sub-agent workflows only |
| **Strength** | Content-level analysis (errors, waste, mistakes) | Structural ground-truth (tokens, counts, durations) |
| **Weakness** | Cannot see inside sub-agents | Cannot assess content quality |

For comprehensive diagnosis, use both:
1. `/diagnose-workflow` first — get the structural picture
2. `/diagnose-session` second — get content-level findings
