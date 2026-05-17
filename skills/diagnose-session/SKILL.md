---
name: diagnose-session
description: use only if invoked by user or workflow
---

# Diagnose Session

Post-hoc analysis of a Claude Code conversation log. Surfaces findings the
agent may have missed in its self-reporting (Required notes).

## Usage

```
/diagnose-session path/to/session.jsonl
```

## Workflow

### Step 1: Render and read the log

Run cc-pretty in agent mode:

```bash
agent-tools cc-pretty <FILE> --agent 2>/dev/null
```

If the session is small, the rendered log appears directly in the Bash output.
If large, the script writes chunk files to `/tmp` and prints their paths —
read all listed files in parallel using the Read tool.

Thinking blocks (`╭─ thinking ─` markers) and full tool input are always shown
(critical for diagnosis — many findings appear only in thinking blocks).

### Step 2: Scan for findings

Scan the rendered log for each category below. For every potential finding,
you MUST follow the evidence-first protocol:

**Evidence-first protocol:**
1. QUOTE the specific text from the log (tool output, error message, agent text)
2. CLASSIFY into exactly one category
3. EXPLAIN why this matters (one sentence)

#### Detection tiers

**HIGH detectability** — scan for these patterns systematically:

| Category | Detection signals |
|----------|------------------|
| **tool issue** | Tool outputs containing `✗`, non-zero exit codes, "error", "failed", "denied", "permission", capability errors. Also: tools that return unhelpful results forcing the agent to retry. |
| **context waste** | Repeated reads of the same file. Failed reads (file not found). Reading files then not using the content. Large tool outputs that didn't contribute to the result. |
| **corrected mistake** | Error→revision sequences: agent tries something, gets an error, then changes approach. Failed commands followed by different commands. Agent reverses a prior assessment or conclusion. |
| **workflow dropout** | Multi-step skill workflows (e.g., `/do` steps 1→2→3→4→5→6) where a later step was never invoked. Detection: (1) identify skill step invocations (bash calls to skill scripts with `--step N`), (2) check the rendered output of each step for continuation directives ("NEXT STEP", "Execute this command now", "run step N after"), (3) verify the instructed follow-up appears in subsequent tool calls. **Truncation hazard:** `--tool-max` truncates tool output tails — step directives sit at the END and may be invisible in the rendered log. When skill step calls are detected, grep the raw JSONL for "NEXT STEP" to bypass truncation: `grep -o 'NEXT STEP.*step [0-9]' <FILE>`. **High-risk pattern:** long execution gaps (>5 minutes, >20 tool calls) between a directive and when it should be followed — the agent is likely to forget. Also check for competing closure signals (e.g., output-style finalization scripts) that may have replaced the workflow's own completion path. Always **significant** severity — the dropped steps are invisible to the user and typically contain quality gates or validation. |

**MEDIUM detectability** — look for these with evidence:

| Category | Detection signals |
|----------|------------------|
| **manual action needed** | Agent mentions something the user must do (install, configure, restart, approve). Check if it was surfaced in Required notes. |
| **instruction issue** | Agent references a file/instruction that doesn't exist. Conflicting instructions observed. Agent works around an instruction rather than following it. |
| **unexpected change** | Agent modifies files beyond what was asked. Scope creep visible in the diff or tool calls. Agent replaces something rather than augmenting it when augmentation was requested. |

**THINKING-BLOCK patterns** — scan `╭─ thinking ─` sections for these:

| Category | Detection signals |
|----------|------------------|
| **contradictory reasoning** | Agent's thinking contradicts its text output or tool results. Statements like "I already fixed this" when the fix hasn't been verified. Agent dismissing review findings without investigation. Thinking says one thing, output says another. **Exclusion:** An agent explicitly citing guidelines, protocol, or instructions to justify an action that differs from its internal assessment is protocol-compliance, NOT a contradiction (e.g., "I'd normally do X but the rules say Y so I'll do Y"). |
| **under-investigated critical issue** | Critical terms (segfault, crash, data loss, corruption, security vulnerability, race condition) mentioned in thinking but with minimal follow-up. The agent acknowledges a serious problem but doesn't investigate its scope, root cause, or downstream impact. A single mention of a critical term without evidence of investigation is a finding. |
| **unverified prior-iteration claim** | Agent references what a prior iteration did or didn't do without verifying the claim. Phrases like "prior iteration missed X", "this was already done", "the previous run handled this". These claims may be wrong and need cross-referencing against actual evidence. |
| **dismissed concern** | Agent notices something concerning in thinking but doesn't surface it in output or Required notes. The thinking block reveals awareness of a problem that the user never sees. |

**LOW detectability** — report only with strong textual evidence:

| Category | Detection signals |
|----------|------------------|
| **suspected user mistake** | Agent notices something wrong with user's input/files but doesn't flag it. Agent fixes a user error silently. User's next message confirms something the agent should have caught. |
| **hidden challenge** | Non-obvious problems the agent solved that weren't apparent from the initial request. These are hard to detect externally — only report if the log clearly shows the agent discovering and solving an unexpected problem. |

### Step 3: Check existing Required notes (workspace conversations only)

If the conversation contains "Required notes" sections in assistant messages:
1. List what was self-reported
2. Compare against your findings
3. Flag items that were reported under the wrong category (miscategorization)

If no Required notes exist (non-workspace conversation), skip this step and
note that self-reporting was not active for this conversation.

### Step 4: Produce the report

Format findings as:

```
## Session Diagnosis: <session-id>

### Overview
<1-2 sentences: what the conversation was about, how many turns>

### Findings

#### <category>
> <quoted evidence from log>

<explanation — one sentence>
<severity: minor | notable | significant>

[repeat for each finding]

### Self-Reporting Comparison (workspace only)
- Self-reported: <count> items
- Diagnosed: <count> items
- Overlap: <count>
- Missed by self-reporting: <list>
- Miscategorized: <list>
- False positives in self-reporting: <list>

### Thinking-Block Findings
[Findings from thinking blocks get their own section because they represent
information the agent had but chose not to surface. These are often the most
important findings.]

### Summary
<2-3 sentences: overall quality assessment, most impactful missed items>
```

## Rules

1. Every finding MUST have a direct quote from the log. No finding without evidence.
2. Do NOT hallucinate findings. If the log is clean, say so — "No findings" is
   a valid and expected outcome for clean sessions. Do not manufacture findings
   to fill the report.
3. Do NOT use subagents. This skill runs as a single analysis pass.
4. Severity guide:
   - **significant**: Would change what the user does next
   - **notable**: User should know but doesn't change immediate action
   - **minor**: Completeness item, low practical impact
5. When in doubt about a finding, include it with lower severity rather than omitting.
6. For corrected mistake: the agent fixing its own error is EXPECTED behavior.
   The finding is that it wasn't reported, not that the error occurred.
7. For suspected user mistake: be careful distinguishing "user made a mistake"
   from "user has a different intent than the agent assumed."
8. Context waste means the **agent** read or fetched irrelevant content. Token
   caching statistics, system-level overhead, and infrastructure details are NOT
   context waste — only agent-initiated reads/writes that didn't contribute to
   the result count.
9. Lead the Findings section with significant/notable items. Group minor items
   at the end under a "Minor" subheading so users see high-impact findings first.
