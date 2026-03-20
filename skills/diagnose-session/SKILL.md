---
name: diagnose-session
description: Analyze a Claude Code conversation log to surface items the agent should have reported but didn't. Invoke with a path to a JSONL session file.
---

# Diagnose Session

Post-hoc analysis of a Claude Code conversation log. Surfaces findings the
agent may have missed in its self-reporting (Required notes).

## Usage

```
/diagnose-session path/to/session.jsonl
```

## Workflow

### Step 1: Render the log

Locate cc-pretty.py (ships with claude-config, sibling to skills/):

```bash
CC_PRETTY="$(dirname "$(readlink -f ~/.claude/skills)")/scripts/cc-pretty.py"
```

Render the conversation to a temporary file:

```bash
SESSION_ID="$(basename "<FILE>" .jsonl)"
PYTHONPATH="$(dirname "$CC_PRETTY")" python3 "$CC_PRETTY" <FILE> --tool-max 500 --no-progress --no-color 2>/dev/null > "/tmp/diagnose-session-${SESSION_ID}.txt"
```

Thinking blocks are rendered with `╭─ thinking ─` markers. These are a critical
data source — many important findings (contradictions, under-investigation,
suspicious reasoning) appear ONLY in thinking blocks.

If the output is too large (>4000 lines), re-run with `--tool-max 200`.

Read the rendered output using the Read tool. If it exceeds context, read in
chunks using offset/limit.

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
