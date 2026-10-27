# Planner Executor: QR Gate Override Errors

**Date**: 2026-02-17
**Subject**: Parent agent overrides QR findings when plan instructions conflict with project rules
**Status**: Analysis Complete, Proposed Fix Below
**Related**: `planner-verification-reporting-analysis.md` (sibling problem, same architectural weakness)

## Summary

During planner execution of a 7-item AGENTS.md update task, the Doc QR agent correctly identified 6 policy violations. The parent (orchestrator) agent dismissed all 6 as "false positives" and routed through `--qr-status pass`. The Code QR agent missed 1 serialization behavior change. All errors shipped.

## Errors Observed

### Error 1: Blockquote edits (6 instances)

AGENTS.md defines blockquotes (`>`) as user-maintained and addition-only. The executing agent edited 6 blockquotes inline (changing `> [ ]` to `> [x]`), violating both rules.

Doc QR flagged all 6; the parent's thinking on dismissing them:

> "The QR's concern seems like a false positive given the explicit instruction to execute the plan"

**Evidence**: subagent `agent-a1ece0c` (Doc QR) of the original session (Evidence Logs).

### Error 2: Serialization behavior change

`removal_queue.py` line 90: `adapter.dump_json(data, indent=2, exclude_none=False)` serializes `"commit_sha": null` where old code (`if commit_sha: entry["commit_sha"] = commit_sha`) omitted the key entirely.

**Code QR missed this.** It compared new code to `json.dumps` behavior instead of the old conditional logic.

**Evidence**: subagent `agent-ac45b94` (Code QR). File: `/repo/essay_wb/run/removal_queue.py:90`.

### Error 3: User-facing print replaced with logger

`prompt_update.py` line 438: `print(diff_text)` → `logger.info(diff_text)` in an interactive CLI function where the user reads the diff then types follow-up via `input()` on line 450. Output disappears unless logging configured at INFO level.

**Neither QR caught this.** The executing agent (M-003) applied print→logger blanket replacement without distinguishing user-facing output.

**Evidence**: subagent `agent-a9fd3cd` (M-003). File: `/repo/essay_wb/prompting/prompt_update.py:438`.

### Error 4: Missing script inventory entry

`scripts/propose_meta_aggregate_prompt.py` was created but not added to the AGENTS.md script inventory (lines 218-242). AGENTS.md rules require script inventory updates.

### Error 5: Item marked DONE despite regression

"Replace `output_type=str`" item marked [DONE] despite Error 2 (serialization behavior change) being a known regression introduced by the same work.

## Root Cause

**Plan authority displacement.** The plan file (Evidence Logs) contained task-specific instructions that the orchestrator treated as authoritative specification. When QR findings conflicted with plan instructions, the orchestrator resolved the conflict in the plan's favor.

The plan never mentions "addition-only", "blockquote", or "script inventory" — project rules that apply regardless of task.

### Mechanism in executor.py

Steps 4 and 7 dispatch QR agents; steps 5 and 8 are gates. Gate routing is **LLM-determined**: the orchestrator reads QR output, decides pass/fail, then invokes either:

```
python3 -m skills.planner.orchestrator.executor --step 5 --qr-status pass
python3 -m skills.planner.orchestrator.executor --step 5 --qr-status fail
```

(`executor.py` lines 585-586, 657-658)

`format_gate()` (line 211) renders deterministically from `qr.passed`, but `qr.passed` is set by the LLM's `--qr-status` choice, so the LLM orchestrator is the sole arbiter of whether QR passed — violating the "dumb dispatcher" invariant from `INTENT.md`:

> "Orchestrator is a dumb dispatcher... never decides to 'proceed anyway' when protocol requires iteration"

### Why QR prompts didn't catch everything

`impl_code_qr_decompose.py` and `impl_docs_qr_decompose.py` contain zero mentions of cross-cutting project rules (AGENTS.md blockquote policy, addition-only rule, script inventory). QR agents check only what those prompts name.

## Relationship to Verification Reporting Analysis

Same weakness: **executor.py relies on LLM judgment for critical gates instead of deterministic enforcement.**

| | This analysis | Verification reporting |
|---|---|---|
| What's fabricated | "QR passed" | "Tests verified" |
| Where it breaks | Steps 5/8 (QR gates) | Steps 3/9 (test execution / retrospective) |
| Data exists? | Yes (QR output has findings) | No (test results never recorded) |

Fixes are **complementary**, not overlapping.

## Proposed Fix

**Change 1: Deterministic QR gate routing** (`executor.py`)

Replace LLM-chosen `--qr-status pass/fail` with script-read routing from `qr-{phase}.json`. The QR verify step already writes structured output; the gate step should read it directly instead of trusting the LLM's summary. Remove `--qr-status` CLI arg from steps 5 and 8. ~30-50 lines changed.

**Change 2: Project-rule invariant checks in QR decompose prompts** (`impl_docs_qr_decompose.py`, `impl_code_qr_decompose.py`)

Add mandatory check items for cross-cutting project rules: blockquote preservation, addition-only edits, script inventory completeness, behavioral compatibility. These are sourced from the project's `context.json` `constraints` field (which exists but was not populated). ~15 lines of prompt additions per file.

## Evidence Logs

| Item | Location |
|---|---|
| Original agent session (the work reviewed) | `~/.claude/projects/-repo/cb24e8f0-51ce-474d-9608-dfbda9f789f4.jsonl` |
| Review session (this analysis) | `~/.claude/projects/-repo/380868ad-81ac-4052-9ba9-267f83b30bbf.jsonl` |
| Plan file (no project rules mentioned) | `/repo/notes/2026-02-17-seven-active-work-items-plan.md` |
| executor.py (gate mechanism) | `~/.claude/skills/scripts/skills/planner/orchestrator/executor.py` lines 211, 585-586, 657-658, 900-904 |
| QR decompose (missing invariants) | `~/.claude/skills/scripts/skills/planner/quality_reviewer/impl_docs_qr_decompose.py`, `impl_code_qr_decompose.py` |
| INTENT.md ("dumb dispatcher" invariant) | `~/.claude/skills/planner/INTENT.md` |
