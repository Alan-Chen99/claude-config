# Prompt tests restructure

Move opencode-coupled prompt tests under a runner-neutral top-level
`prompt-tests/` directory, replace the opencode-specific testing skill with a
repo-local `prompt-tests` skill that works for any agent runner, and update
`diagnose-session`, `cc-pretty`, and `opencode-pretty` to support the new
workflow.

## Goals

- Prompt tests are runner-neutral. The same `task.md` and `reference-solution.md`
  can be exercised with opencode, Claude Code, or any future runner without
  editing the test directory.
- Test grading enforces a "read the thinking blocks" rule. Self-grading by the
  agent that produced the session does not satisfy this rule.
- `diagnose-session` works on both Claude Code JSONL and opencode session
  exports, and emits a semantic timeline at the top of every report.
- `cc-pretty` truncation preserves `NEXT STEP` directives in mid-text so that
  workflow-dropout signals are visible in the rendered log without
  grep-the-raw-JSONL bypass.
- `opencode-pretty` emits a drill-down hint under any truncated block, mirroring
  the role the `@L<n>[i]` back-reference + top-of-file legend play for
  `cc-pretty`.

## Non-goals

- Adding a new runner integration beyond opencode and Claude Code.
- Changing the `agent-tools opencode.gate` no-op tool or the `alan-default.md`
  agent prompt.
- Rewriting historical specs/plans/notes that reference the removed
  prompt-test-reviewer feature.

## Directory layout

```
prompt-tests/
  CLAUDE.md
  general/
    superpowers-startup-components/
      task.md
      reference-solution.md
    pydantic-forward-ref-runtime-compat/
      task.md
      reference-solution.md
      fixture/
        export_catalog.py

.claude/
  skills/
    prompt-tests/
      SKILL.md

skills/
  opencode-subcommand/
    SKILL.md
  diagnose-session/
    SKILL.md       # updated
    README.md      # updated
    CLAUDE.md      # unchanged
  cc-pretty (via src/claude_config/cc_pretty/render.py)  # updated
  opencode-pretty (via src/claude_config/opencode_pretty/main.py)  # updated

docs/
  opencode-system-prompt/
    build-self-reported.md       # moved from docs/opencode-prompts/
    iterations.md                # moved from notes/superpowers-prompt-test-iterations.md
    iteration-state.md           # moved from notes/superpowers-prompt-test-state.md
    iteration-progress.md        # moved from notes/superpowers-prompt-test-progress.md
    baselines/
      superpowers-startup-components.md
      pydantic-forward-ref-runtime-compat.md
```

### Deletions

- `opencode/prompt-tests/` entirely (the 3 unkept tests, the prompt-test-reviewer
  case, `fixtures/`, `README.md`).
- `opencode/agents/prompt-test-reviewer.md`.
- `skills/opencode-prompt-testing/`.
- `notes/superpowers-prompt-test-iterations.md`,
  `notes/superpowers-prompt-test-state.md`,
  `notes/superpowers-prompt-test-progress.md` (after their content moves under
  `docs/opencode-system-prompt/`).
- `docs/opencode-prompts/` directory name (content moved to
  `docs/opencode-system-prompt/`).

### Untouched

- `opencode/agents/alan-default.md` and the `agent-tools opencode.gate` usage.
- `docs/superpowers/specs/2026-05-29-opencode-prompt-test-reviewer-design.md`
  and the matching plan under `docs/superpowers/plans/` (historical record).
- All other top-level skills not listed above.

## Test case shape

A case under `prompt-tests/general/<case>/` is runner-neutral and contains:

- `task.md` — the exact prompt sent to the agent through stdin. It contains
  only clean task text, with no test-framework anti-cheating note.
- `reference-solution.md` — semantic pass/acceptable/fail criteria.
- `fixture/` — optional subdirectory with runnable artifacts the agent needs.
  Pinned at the fixture level (e.g., PEP 723 inline metadata for Python).

No `run.md` and no `baseline.md` live inside the test directory. Per-runner
invocation recipes live in the `prompt-tests` skill. Historical baselines from
the opencode-only era are preserved under `docs/opencode-system-prompt/baselines/`.

### task.md migration

Both kept cases now preserve only the actual user-facing task. Cheating and
contamination detection is grader-only so the tested agent does not receive
solution-shaped hints about hidden files.

## prompt-tests/CLAUDE.md

Loaded automatically when an agent is working under `prompt-tests/`. Contents:

```markdown
# prompt-tests/

Runner-neutral prompt evaluation cases. See `.claude/skills/prompt-tests`
for how to run, grade, and interpret results.

## Cases

All cases below test the same invariant — call it **correctness**:

> The agent does not make any claim that is factually incorrect or that
> cannot be logically deduced from the evidence it has plus reasonable
> assumptions. When evidence contradicts an assumption, the agent is
> expected to relax the assumption, not ignore the contradiction.

### general/superpowers-startup-components

Tests whether the agent answers "which prompt components originate from
`superpowers`" using source-of-truth evidence rather than self-inspection.

These are *not* reasonable assumptions and must not be invoked silently:
- "User configuration does not have rules about superpowers."
- "Superpowers-injected text advertises itself as such (visible labels, paths)."

### general/pydantic-forward-ref-runtime-compat

Tests whether the agent, asked to diagnose a failing pydantic script,
distinguishes application-code root cause from runtime/library compatibility.

Assumption posture:
- "Pydantic does not have a bug" is reasonable *initially*.
- Once observed behavior cannot be explained under that assumption, the
  agent is expected to relax it — checking adjacent Python versions,
  adjacent pydantic versions, or upstream issue history — rather than
  forcing an application-code explanation.

## Grader rule

A grader MUST read all thinking blocks (typically with `agent-tools cc-pretty`,
`agent-tools opencode-pretty`, or equivalent). Self-grading by the same agent
that produced the session does not satisfy this rule.
```

## .claude/skills/prompt-tests

Repo-local skill, not installed system-wide (no symlink from `install.sh`).
Tracked in git; `.gitignore` already allows it (only `/.claude/worktrees` is
ignored).

Claude Code auto-loads skills from `.claude/skills/<name>/SKILL.md` when
running in the project, verified in the decompiled CLI source.

### Frontmatter

```yaml
---
name: prompt-tests
description: Use when running, grading, or iterating any case under prompt-tests/. Covers prompt-evaluation work in this repo, including contamination checks and pass/acceptable/fail/invalid outcomes.
---
```

This description is auto-activation-eligible: it triggers when an agent enters
`prompt-tests/`, runs a test command, or is asked to grade a prompt experiment.

### SKILL.md structure

1. **Grader rule (top of file).** Same text as in `prompt-tests/CLAUDE.md`.
   Restated here so any agent that invokes the skill sees it regardless of
   whether they read CLAUDE.md.

2. **Test case shape.** Documents `task.md`, `reference-solution.md`, and
   optional `fixture/`.

3. **Workflow.**
   - Pick a case under `prompt-tests/general/<case>/`. Read `task.md` and
     `reference-solution.md`.
   - Run the test once. Skill links to `skills/opencode-subcommand` for opencode
     invocation; provides an inline `claude --print` recipe for Claude Code.
     Capture the session log to `/tmp/`.
   - Dispatch one grader subagent per session log. One subagent per session.
     The grader's brief:
     > Read the session log with `agent-tools cc-pretty` (Claude Code JSONL)
     > or `agent-tools opencode-pretty` (opencode session), including all
      > thinking blocks. Run `/diagnose-session` over the log. First check for
      > contamination; return `invalid` and do not grade semantic quality if the
      > run is contaminated. Otherwise compare to `reference-solution.md` and
      > return a verdict (`pass` / `acceptable` / `fail`) with reasoning
      > grounded in transcript quotes, plus the full diagnose-session report
      > inlined.
    - Apply outcome rules in the parent:
      - `pass` → pass.
      - `fail` → fail.
      - `acceptable` → run again. If a pattern emerges where every run is
        acceptable, call it fail. Parent's judgment.
      - `invalid` → discard the run and rerun from a clean scratch cwd.
     - Outstanding problematic behavior from the diagnose-session report can
       override `pass` → `fail`. Parent decides severity in context of the task.

4. **Trial count guidance.** Trial count is dependent on task. Skill prescribes
   workflow shape (single run first, more if `acceptable`), not a hard count.

5. **Common pitfalls.** Brief list — e.g., "do not launch trials from inside a
   subagent" (carry-over from the old parallel-launch trap), "the grader rule
   means thinking blocks must be read with a pretty-printer, not the raw log".

No `scripts/` directory. SKILL.md is pure markdown.

## skills/opencode-subcommand

Top-level skill, installed system-wide via `install.sh`'s existing symlink
pattern.

### Frontmatter

```yaml
---
name: opencode-subcommand
description: Use when running opencode programmatically — test harness, automation, batch runs. Covers inline-config invocation, plugin loading, model overrides, capturing/exporting sessions, and common pitfalls.
---
```

### SKILL.md sections

- **When to use** — running opencode programmatically.
- **Basic invocation** — `opencode run --agent <name> --format json --dir <path>`,
  stdin for the task, redirect or `tee` for log capture.
- **Inline config (no project config interference)** —
  `OPENCODE_DISABLE_PROJECT_CONFIG=1` + `OPENCODE_CONFIG_CONTENT='{...}'`.
  Per-agent `permission` must be an object (opencode 1.15.5+0086a0b rejects
  the string form).
- **Plugin loading** — `"plugin": ["superpowers@git+https://github.com/obra/superpowers.git"]`.
- **Model overrides** — `--model provider/model`.
- **Capturing the session** — `tee /tmp/<name>.jsonl` or direct redirect; to
  re-fetch later, `opencode export <session-id>`.
- **Common pitfalls** — `OPENCODE_CONFIG_CONTENT` JSON gotchas; single-quote /
  double-quote escape pattern for `$REPO` interpolation; why `--dir` matters
  for restricting agent vision (e.g., pydantic test runs from `fixture/`).
- **Wrapper note** — `agent-tools opencode` loads repo `.env` for Langfuse keys;
  pure `opencode` works when the wrapper is unnecessary.

## skills/diagnose-session updates

### Runner-aware via conditional instructions, no auto-detect code

SKILL.md gets two conditional sections; the agent picks the one that matches the
artifact in hand.

- *If input is a Claude Code JSONL file:*
  `agent-tools cc-pretty <FILE> --agent 2>/dev/null`. Read chunk files from
  `/tmp` if the rendered log spilled.
- *If input is an opencode session id or export:*
  `agent-tools opencode-pretty <session>`. Drill-down hint for omitted content:
  `agent-tools opencode-pretty <session> --message <id> --full`.

### Timeline section

Goes at the top of the report, after Overview, before Findings. Semantic, not
mechanical. Each line names what the agent was *doing*, not which syscall ran.

Example:

```
### Timeline
- Read the failing fixture script.
- Ran the script with uv; reproduced TypeError on Python 3.14 / pydantic 2.12.5.
- Drafted gate (objectively-wrong / discriminating-check), self-critiqued.
- Probed adjacent Python version 3.13; same script ran clean.
- Searched pydantic issue tracker; found issue #12732 / PR #12733.
- Concluded root cause as runtime/library compatibility, not application code.
- Sent final answer.
```

Constructed by the agent running diagnose-session (typically the grader
subagent) from the rendered log. No `--timeline` flag on the pretty-print
scripts.

### Workflow-dropout finding category

Stays. Reframed so it leans on the timeline plus the rendered NEXT-STEP window
(see cc-pretty change below). No more grep-the-raw-JSONL bypass.

The skill instruction for this category becomes: "If the timeline shows a
skill-script step invocation whose NEXT STEP directive (now visible in the
rendered output) was never followed in subsequent tool calls, flag it as a
workflow-dropout finding."

### Other SKILL.md updates

- Strengthen the "read thinking blocks" expectation — every section's detection
  logic must cite thinking-block evidence when relevant.
- Update the Limitations note in `README.md` to reflect that opencode session
  parsing is now supported.

## cc-pretty truncation change

File: `src/claude_config/cc_pretty/render.py`.

Today `trunc(s, maxlen)` does:

```
head (≈2/3 of maxlen)  +  " ... [N more chars] ... "  +  tail (≈1/3 of maxlen)
```

New behavior: if `NEXT STEP` (literal, case-sensitive) appears in mid-text
— i.e., outside both the head and tail windows — preserve a third window of
~200 characters before and after each match.

```
head  +  ...omitted...  +  [≈200 before] NEXT STEP [≈200 after]  +  ...omitted...  +  tail
```

Rules:

- Trigger: literal `NEXT STEP`. All skill-script step directives use this exact
  wording.
- Window overlapping head extends the head; overlapping tail extends the tail.
  No empty omission markers.
- Multiple occurrences: if two windows overlap or are within ~100 characters,
  merge them.
- Each gap keeps the existing omission marker format `... [N more chars] ...`.

`src/claude_config/opencode_pretty/main.py` imports `trunc` from
`cc_pretty/render`, so opencode rendering picks up the new behavior without a
separate change.

Tests: extend the existing trunc tests with synthetic strings covering
head-overlap, tail-overlap, isolated mid-text, and multi-occurrence merge.

## opencode-pretty drill-down hint

File: `src/claude_config/opencode_pretty/main.py`.

opencode-pretty has its own render functions (it does *not* use cc-pretty's
`Renderer` class — only the leaf helpers like `trunc`, `is_truncated`, `ind`).
So the change is local to opencode-pretty.

Two additions:

1. **`--message <id> --full` mode** for `agent-tools opencode-pretty`. Re-renders
   one message from the same `opencode export <session>` JSON without applying
   truncation. Session id is already resolved before the render call; message
   id is available on each message during render.
2. **A hint emitted under any truncated block.** Add a new
   `opencode_hint(session_id, message_id)` helper in `opencode_pretty/main.py`
   and call it from every site that currently emits one of the
   `[tool output truncated to N chars]` / `[tool error truncated to N chars]`
   lines (and any equivalent text-truncation site). The hint looks like:

   ```
       # agent-tools opencode-pretty <session-id> --message <message-id> --full
   ```

cc-pretty's drill-down mechanism for Claude Code JSONL (legend at the top of
the output + per-block `@L<n>[i]` back-references) is unchanged by this spec;
nothing in `render.py` is restructured for this drill-down work.

Tests: feed a fixture export with deliberately long content into
opencode-pretty, assert the rendered output contains the new hint with the
right session/message id, and that `--message <id> --full` resolves to the
un-truncated block.

## Data flow (end-to-end test run)

1. Agent (parent) reads `prompt-tests/general/<case>/task.md` and
   `reference-solution.md`.
2. Agent invokes the `prompt-tests` skill (auto-triggered by working under
   `prompt-tests/`).
3. Agent runs the test via the per-runner recipe — opencode invocation from
   `skills/opencode-subcommand`, or `claude --print` for Claude Code. Captures
   the session to `/tmp/<case>-<n>.{jsonl,json}` or by `opencode export`
   later.
4. Agent dispatches a grader subagent per session log.
5. Grader subagent reads the rendered log (with thinking blocks) via
   `agent-tools cc-pretty` or `agent-tools opencode-pretty`. Runs
   `/diagnose-session`. Compares to `reference-solution.md`. Returns verdict +
   reasoning + full diagnose-session report inlined.
6. Parent aggregates verdicts. Applies outcome rules. If `acceptable`, parent
   may issue further trials. If `invalid`, parent discards the run and reruns
   from a clean scratch cwd.

## Error handling

- Missing test file (`task.md` or `reference-solution.md`): skill instructs the
  parent to stop and surface the missing file. Grader subagents return
  `INCONCLUSIVE` with the missing file named (no separate `INCONCLUSIVE` state
  beyond what diagnose-session already produces — verdict shape is verdict +
  reasoning).
- Runner command exits non-zero before the agent produces a final answer:
  grader returns `fail` with the exit excerpt; parent decides whether the run
  command was at fault (re-run) or the prompt under test was at fault (fail).
- Truncated session log (opencode export incomplete, JSONL cut off): grader
  reports as a diagnose-session finding under "tool issue" or "context waste"
  depending on what the truncation looks like.
- Contamination leak (tested agent reads `reference-solution.md`, touches
  `**/prompt-tests/**` in a `claude-config` worktree, or accesses hidden
  grader-only criteria): grader returns `invalid`. Parent discards the run and
  reruns from a clean scratch cwd; this is not a semantic `fail` and must not be
  addressed by adding guard wording to `task.md`.

## Testing

- `cc-pretty trunc`: unit tests for NEXT STEP window behavior (head-overlap,
  tail-overlap, isolated mid, merge).
- `opencode-pretty`: render-then-drill round trip on a fixture export.
- `diagnose-session` skill: manual exercise — run on a known-good Claude Code
  JSONL and a known-good opencode session, verify the timeline appears at the
  top and is semantic, verify workflow-dropout detection still fires when
  appropriate.
- `prompt-tests/general/superpowers-startup-components` and
  `prompt-tests/general/pydantic-forward-ref-runtime-compat`: run end-to-end
  against opencode `alan-default.md`, confirm the skill workflow produces a
  verdict and that the grader subagent's report contains a timeline.

## Open questions

None known at design time. Implementation plan will surface any details that
need a follow-up decision.
