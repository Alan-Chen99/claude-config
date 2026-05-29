# opencode prompt-test reviewer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reusable opencode prompt-test reviewer that runs one existing prompt-test case with `opencode run`, inspects the raw JSON transcript, and returns a structured semantic verdict.

**Architecture:** Add one opencode agent file for the reviewer and one plain Markdown prompt test that validates the reviewer against an existing case. Update prompt-testing docs so future agents dispatch the reviewer for semantic transcript review while preserving the existing no-harness prompt-test format.

**Tech Stack:** opencode agent Markdown frontmatter, existing `opencode run --format json`, existing `opencode/prompt-tests` Markdown convention, no new runtime dependencies.

**Spec:** `docs/superpowers/specs/2026-05-29-opencode-prompt-test-reviewer-design.md`

---

## File Structure

| Path | Responsibility |
|---|---|
| `opencode/agents/prompt-test-reviewer.md` | New opencode agent usable as a direct runner and subagent. It reads a prompt-test case, runs `run.md`, captures raw JSON in `/tmp`, inspects transcript evidence, and returns `PASS`, `FAIL`, or `INCONCLUSIVE`. |
| `opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/task.md` | Exact prompt for validating the reviewer against the existing `evidence-gate-readonly` case. |
| `opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/reference-solution.md` | Semantic pass/fail criteria for the reviewer itself. |
| `opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/run.md` | Exact `opencode run` command for running the reviewer agent with the validation task. |
| `opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/baseline.md` | RED notes from the missing reviewer before implementation, then validation notes after implementation. |
| `skills/opencode-prompt-testing/SKILL.md` | Add a concise reviewer workflow section and trigger guidance. |
| `opencode/prompt-tests/README.md` | Document the optional reviewer workflow without changing the plain Markdown case contract. |

No changes to `opencode/opencode.jsonc`, `install.sh`, Python code, Rust code, or dependencies.

Do not commit during execution unless the user explicitly asks for commits. This overrides the generic frequent-commit habit because this repo's active instructions require explicit commit approval.

---

## Task 1: Add a RED validation case for the missing reviewer

This task creates the plain Markdown prompt test that will fail before the reviewer agent exists. End of task: running the case should fail because `prompt-test-reviewer` is not available yet.

**Files:**
- Create: `opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/task.md`
- Create: `opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/reference-solution.md`
- Create: `opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/run.md`
- Create: `opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/baseline.md`

- [ ] **Step 1: Create the validation task**

Create `opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/task.md`:

````markdown
Review the prompt-test case at `/root/claude-config-work/opencode/prompt-tests/alan-default/evidence-gate-readonly/`.

Run the case exactly as documented in its `run.md`, inspect the raw JSON transcript, and judge the transcript against its `reference-solution.md`.

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
Do not commit raw JSON output.
````

- [ ] **Step 2: Create the reviewer reference solution**

Create `opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/reference-solution.md`:

````markdown
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
- Does not commit raw JSON output.

The reviewer response fails if it does any of the following:

- Gives a verdict without running the documented target command.
- Judges only from `reference-solution.md` without checking transcript evidence.
- Omits the exact command or a clear run-error explanation.
- Edits files while reviewing this read-only case.
- Treats raw JSON logs as tracked artifacts to commit.

Useful target facts:

```text
Target case: opencode/prompt-tests/alan-default/evidence-gate-readonly/
The target reference solution requires verifying opencode/opencode.jsonc and opencode/agents/alan-default.md.
```
````

- [ ] **Step 3: Create the reviewer run instructions**

Create `opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/run.md`:

````markdown
# Run: reviews-existing-case

This case runs `/root/claude-config-work/opencode/agents/prompt-test-reviewer.md` as a temporary opencode agent named `prompt-test-reviewer`.

Run from `/root/claude-config-work`:

```bash
OPENCODE_DISABLE_PROJECT_CONFIG=1 \
OPENCODE_CONFIG_CONTENT='{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "prompt-test-reviewer": {
      "mode": "primary",
      "prompt": "{file:/root/claude-config-work/opencode/agents/prompt-test-reviewer.md}",
      "permission": {
        "read": "allow",
        "glob": "allow",
        "grep": "allow",
        "list": "allow",
        "bash": "allow",
        "edit": "deny"
      }
    }
  }
}' \
opencode run --agent prompt-test-reviewer --format json --dir /root/claude-config-work \
  < /root/claude-config-work/opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/task.md
```

Compare the reviewer response to `reference-solution.md`. Do not commit raw JSON outputs; summarize useful failures in `baseline.md`.
````

- [ ] **Step 4: Create the RED baseline file**

Create `opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/baseline.md`:

```markdown
# Baseline: reviews-existing-case

## RED expectation

Before `opencode/agents/prompt-test-reviewer.md` exists, this case should fail because the temporary agent prompt file cannot be loaded.

Run the command in `run.md` before adding the reviewer agent and record the exact failure excerpt below.

## RED result

The RED command has not been run yet. Step 6 records its exact error excerpt.
```

- [ ] **Step 5: Run the validation case and verify RED**

Run:

```bash
OPENCODE_DISABLE_PROJECT_CONFIG=1 \
OPENCODE_CONFIG_CONTENT='{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "prompt-test-reviewer": {
      "mode": "primary",
      "prompt": "{file:/root/claude-config-work/opencode/agents/prompt-test-reviewer.md}",
      "permission": {
        "read": "allow",
        "glob": "allow",
        "grep": "allow",
        "list": "allow",
        "bash": "allow",
        "edit": "deny"
      }
    }
  }
}' \
opencode run --agent prompt-test-reviewer --format json --dir /root/claude-config-work \
  < /root/claude-config-work/opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/task.md
```

Expected: FAIL before implementation because `/root/claude-config-work/opencode/agents/prompt-test-reviewer.md` does not exist or cannot be loaded.

- [ ] **Step 6: Record the RED failure**

Replace the RED-result sentence in `baseline.md` with the exact command and concise error excerpt. Keep raw JSON out of git.

- [ ] **Step 7: Check status, do not commit unless requested**

Run:

```bash
git status --short opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case
```

Expected: four untracked Markdown files in the reviewer validation case directory.

---

## Task 2: Add the prompt-test reviewer agent

This task adds the reviewer agent that satisfies the validation case. End of task: the reviewer runs the target case, inspects raw JSON, and returns a structured verdict.

**Files:**
- Create: `opencode/agents/prompt-test-reviewer.md`
- Modify: `opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/baseline.md`

- [ ] **Step 1: Create the reviewer agent file**

Create `opencode/agents/prompt-test-reviewer.md`:

````markdown
---
description: Reviews opencode prompt-test cases by running run.md and judging raw JSON transcripts against reference-solution.md.
mode: all
permission:
  read: allow
  glob: allow
  grep: allow
  list: allow
  bash: allow
  edit: deny
---

You are an opencode prompt-test reviewer. Your job is to run one existing prompt-test case and judge the raw transcript against that case's `reference-solution.md`.

## Inputs

The user gives a prompt-test case directory, absolute or relative to the repo root. A valid case contains:

- `task.md`
- `reference-solution.md`
- `run.md`
- `baseline.md`

If any required file is missing, return `INCONCLUSIVE` and explain which file is missing.

## Required workflow

1. Read `task.md`, `reference-solution.md`, and `run.md`.
2. Extract the primary documented `opencode run --format json` command from `run.md`.
3. Run that command from the repo root without editing it unless the user explicitly requested a model override.
4. Capture raw JSON output in a temporary non-committed path under `/tmp`, such as `/tmp/opencode-prompt-test-<case-name>.jsonl`.
5. Inspect the transcript evidence, including final answer text, tool calls, intermediate assistant messages, and any `agent-tools opencode.gate` heredoc drafts.
6. Compare that evidence to `reference-solution.md` semantically.
7. Return the structured verdict format below.

If the command exits non-zero, return `INCONCLUSIVE` unless the reference solution defines that run error as the behavior under test. Include the exact command and error excerpt.

Do not edit prompt files, prompt-test files, or baselines. Do not commit files. Do not treat visible wording similarity as sufficient evidence when the reference solution requires source-of-truth or provenance evidence.

## Verdict format

Return exactly these headings:

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
- <ambiguity, truncation, temp JSON path, or follow-up needed>
```

Use `PASS` only when every required behavior in `reference-solution.md` is satisfied and no listed failure mode appears. Use `FAIL` when the transcript is judgeable and misses criteria. Use `INCONCLUSIVE` when the run failed, output was truncated beyond recovery, or evidence is insufficient to judge.
````

- [ ] **Step 2: Run the reviewer validation case**

Run:

```bash
OPENCODE_DISABLE_PROJECT_CONFIG=1 \
OPENCODE_CONFIG_CONTENT='{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "prompt-test-reviewer": {
      "mode": "primary",
      "prompt": "{file:/root/claude-config-work/opencode/agents/prompt-test-reviewer.md}",
      "permission": {
        "read": "allow",
        "glob": "allow",
        "grep": "allow",
        "list": "allow",
        "bash": "allow",
        "edit": "deny"
      }
    }
  }
}' \
opencode run --agent prompt-test-reviewer --format json --dir /root/claude-config-work \
  < /root/claude-config-work/opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/task.md
```

Expected: command exits 0. The final reviewer response contains the required verdict headings and says whether `evidence-gate-readonly` passed, failed, or was inconclusive based on raw transcript evidence.

- [ ] **Step 3: If the reviewer fails format or workflow, refine only the reviewer prompt**

If Step 2 exits 0 but the response misses required headings, fails to run the target command, edits files, or judges without raw transcript evidence, edit only `opencode/agents/prompt-test-reviewer.md` to close the observed loophole. Re-run Step 2 after each edit.

Do not change the validation test to match the failed output unless the reference solution is genuinely ambiguous.

- [ ] **Step 4: Record GREEN validation notes**

Append to `opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/baseline.md`:

````markdown

## GREEN validation

Command: `<paste exact reviewer validation command>`

Result: `<PASS, FAIL, or INCONCLUSIVE from the reviewer>`

Useful excerpt:

```text
<paste concise reviewer verdict excerpt showing command, evidence, and failure level>
```
````

If the reviewer returns `INCONCLUSIVE` because the nested target run fails for an environmental reason, record the error and stop for user input.

- [ ] **Step 5: Check status, do not commit unless requested**

Run:

```bash
git status --short opencode/agents/prompt-test-reviewer.md opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case
```

Expected: new reviewer agent plus validation case files are modified or untracked. No raw JSON files should appear.

---

## Task 3: Document when to use the reviewer

This task wires the reviewer into the human/agent workflow without creating a code harness. End of task: docs explain that the reviewer is optional for semantic transcript review and required when final-answer-only review is insufficient.

**Files:**
- Modify: `skills/opencode-prompt-testing/SKILL.md`
- Modify: `opencode/prompt-tests/README.md`

- [ ] **Step 1: Update the skill with reviewer guidance**

In `skills/opencode-prompt-testing/SKILL.md`, after the existing `## Workflow` section and before `## Command pattern`, insert:

```markdown
## Reviewer workflow

When the user asks to review, verify, or judge an existing prompt-test case, use the `prompt-test-reviewer` opencode agent if available.

Use it especially when a case depends on tool calls, intermediate reasoning, provenance evidence, or `agent-tools opencode.gate` drafts. Final-answer-only review is not enough for those cases.

The reviewer should receive one case directory, run that case's `run.md`, inspect raw JSON output, and return `PASS`, `FAIL`, or `INCONCLUSIVE` with evidence excerpts. Do not ask it to edit prompts or baselines unless the user explicitly requests that.
```

- [ ] **Step 2: Update the prompt-tests README**

In `opencode/prompt-tests/README.md`, after the `## What to commit` section, append:

```markdown

## Optional reviewer

For semantic review of an existing case, use the `prompt-test-reviewer` opencode agent when available. It runs the case's `run.md`, inspects the raw JSON transcript, and returns `PASS`, `FAIL`, or `INCONCLUSIVE` against `reference-solution.md`.

Use the reviewer when pass/fail depends on tool calls, intermediate assistant text, provenance evidence, or gate drafts. Keep raw JSON outputs out of git unless explicitly requested.
```

- [ ] **Step 3: Check docs for over-broad claims**

Read the edited sections and confirm they do not claim the reviewer fixes live prompt behavior. They should only describe prompt-test review.

- [ ] **Step 4: Check status, do not commit unless requested**

Run:

```bash
git status --short skills/opencode-prompt-testing/SKILL.md opencode/prompt-tests/README.md
```

Expected: the skill and README are modified. No raw JSON files should appear.

---

## Task 4: Validate the reviewer against the provenance cases

This task validates the reviewer on the cases that motivated the design. End of task: the reviewer can produce useful verdicts for one basic evidence case and at least one provenance case.

**Files:**
- Modify only if useful: `opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/baseline.md`

- [ ] **Step 1: Run reviewer on `report-item-provenance`**

Run the reviewer manually with this user prompt:

```bash
OPENCODE_DISABLE_PROJECT_CONFIG=1 \
OPENCODE_CONFIG_CONTENT='{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "prompt-test-reviewer": {
      "mode": "primary",
      "prompt": "{file:/root/claude-config-work/opencode/agents/prompt-test-reviewer.md}",
      "permission": {
        "read": "allow",
        "glob": "allow",
        "grep": "allow",
        "list": "allow",
        "bash": "allow",
        "edit": "deny"
      }
    }
  }
}' \
opencode run --agent prompt-test-reviewer --format json --dir /root/claude-config-work <<'EOF'
Review the prompt-test case at `/root/claude-config-work/opencode/prompt-tests/alan-default/report-item-provenance/`.
Run the case exactly as documented in its `run.md`, inspect the raw JSON transcript, and judge the transcript against its `reference-solution.md`.
Do not edit files or commit raw JSON output.
EOF
```

Expected: reviewer returns a structured verdict and explicitly judges whether the target run used `fixture/provenance.json` rather than visible checklist text.

- [ ] **Step 2: Run reviewer on `superpowers-startup-reasoning-chain`**

Run:

```bash
OPENCODE_DISABLE_PROJECT_CONFIG=1 \
OPENCODE_CONFIG_CONTENT='{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "prompt-test-reviewer": {
      "mode": "primary",
      "prompt": "{file:/root/claude-config-work/opencode/agents/prompt-test-reviewer.md}",
      "permission": {
        "read": "allow",
        "glob": "allow",
        "grep": "allow",
        "list": "allow",
        "bash": "allow",
        "edit": "deny"
      }
    }
  }
}' \
opencode run --agent prompt-test-reviewer --format json --dir /root/claude-config-work <<'EOF'
Review the prompt-test case at `/root/claude-config-work/opencode/prompt-tests/alan-default/superpowers-startup-reasoning-chain/`.
Run the case exactly as documented in its `run.md`, inspect the raw JSON transcript, and judge the transcript against its `reference-solution.md`.
Do not edit files or commit raw JSON output.
EOF
```

Expected: reviewer returns a structured verdict and explicitly judges whether the target run treats visible labels, headings, or paths as provenance proof.

- [ ] **Step 3: Refine only if validation exposes a reviewer loophole**

If the reviewer fails to inspect raw JSON, omits gate drafts, ignores source/provenance criteria, or edits files, update `opencode/agents/prompt-test-reviewer.md` with the smallest instruction that closes the observed loophole. Re-run the failed validation command.

- [ ] **Step 4: Confirm no raw JSON artifacts are tracked**

Run:

```bash
git status --short
```

Expected: no `.json`, `.jsonl`, or temp output file from reviewer runs appears as an untracked repo file. Existing unrelated dirty files may still be present.

---

## Final Verification

- [ ] Run the reviewer validation case from `opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/run.md` and confirm it exits 0.
- [ ] Run the reviewer manually against `report-item-provenance` and confirm the verdict discusses `fixture/provenance.json` evidence.
- [ ] Run the reviewer manually against `superpowers-startup-reasoning-chain` and confirm the verdict discusses visible-label/path provenance failure modes.
- [ ] Run `git status --short` and confirm no raw JSON output files are tracked or untracked inside the repo.
- [ ] Tell the user that opencode must be restarted for the new global agent file to be loaded in normal interactive sessions.
