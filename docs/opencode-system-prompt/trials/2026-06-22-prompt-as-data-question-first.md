# prompt-as-data and underlying-question scoping

Date: 2026-06-22
Runner: `opencode run` via inline-config A/B harness
Model: `openai/gpt-5.5`
Variant: `xhigh`
Default prompt under test: `opencode/agents/alan-default-ids.md`

## Question

When the user asks "summarize status" / "diagnose status" of a workflow whose
prompt material (the active `PROMPT.md`) names a prior loop that didn't resolve
the same goal, does the agent open the older worktree, or does it stay
cwd-local?

Empirical answer in the original sessions: stays cwd-local. Three diagnostic
sessions (`ses_10f36948effeXWQ1dEPYPeuEdZ` "summarize status",
`ses_10efa3cd5ffeL6p9p6JZs9nwvo` "summarize status" without strategy-anchor
phrasing, `ses_10ee37d78ffeB41v6n4vGb3SeB` "diagnose and summarize") all opened
zero files in `/root/claude-config-work/` despite `PROMPT.md` saying *"older
loop didnt resolve the qeustion. we will work on the same task."* In contrast,
ralph worker iter 1 (`ses_111f55dffffekcWkHMXtTbD2nv`), which received the same
`PROMPT.md` content but as a directive (the worker's task body) rather than as
data to summarize, opened the older worktree's scratchpad and decisions
multiple times.

Hypothesis: the failure is **prompt-as-data vs prompt-as-instruction** on top
of **task-verb literalness**. When PROMPT.md is data to summarize, the
references inside it become metadata, not instructions; the agent's scoping is
driven by the literal verb which is satisfiable from cwd, so the older
worktree never enters scope.

## Harness

Inline opencode config (`OPENCODE_DISABLE_PROJECT_CONFIG=1`) registering one
test agent per run, all using:

```
opencode run --agent <name> --model openai/gpt-5.5 --variant xhigh \
  --format json --dir <workdir> < /tmp/task.md
```

Task (same for every run):

```
diagnose and summarize status of ralph workflow "/root/claude-config-work2/PROMPT.md" + /workspace/ralph/build.yml ; read scratchpad
```

Workspace state needed for reproduction: `.ralph/agent/*` populated in BOTH
`/root/claude-config-work2/` and `/root/claude-config-work/`. The state used
in the variant runs was tag `ep-loop4` checked out as `/tmp/ep-loop4-test`.

## Runs

| Variant | Rule change | Older-worktree reads | Tool calls | Tokens in/out |
|---|---|---|---|---|
| baseline | none | 0 | 46 | 147K / 9K |
| A (initial fix) | new R060.5 + G1 + G2 (verb examples + "PROMPT.md, referenced files, prior context" naming) | 5 | 53 | 161K / 12K |
| B (ablation) | new R060.5 main body only, no G1/G2 | 12 | 73 | 156K / 13K |
| D (final) | R061 reworded only: *"Gather enough context to answer the user's underlying question, not just the literal task verb."* | 10 | 74 | 171K / 7K |

Session IDs:

- baseline: `ses_10ee37d78ffeB41v6n4vGb3SeB`
- A: `ses_10edb95f5ffe7x0xKjV7nzIo13`
- B: `ses_10eaa0cf0ffedvjVGgMNbVKlmM`
- D: `ses_10ea9972affeQNGnU8EomAY3JR`

## Observations

1. **Verb change alone is insufficient.** Baseline used the stronger "diagnose
   and summarize" verb and still failed.

2. **All three rule variants moved behavior — the minimal one moved it most.**
   Variant A (the longest) underperformed Variants B and D. Adding G1 (verb
   examples) and G2 (PROMPT.md-specific naming) did not improve outcomes; they
   added overfit risk without behavioral payoff.

3. **R061 reworded (D) won on every axis.**
   - More older-worktree reads than A (10 vs 5).
   - Richer final answer: variant D's diagnosis found the `ep-loop4` tag,
     recovered `PROMPT.md` from git history via `git show ff5b693:PROMPT.md`
     and `git show ep-loop4:.ralph/agent/scratchpad.md`, and surfaced the
     work-vs-ep-loop4 state confusion — explicitly tagging it under "suspected
     user mistake". Variant A's diagnosis was a mechanical status snapshot.
   - No structural disruption (no new rule, no step-list renumbering).
   - Less overfitted wording (no PROMPT.md-specific naming).

4. **Variant A's "G2 was load-bearing" claim was wrong.** My turn-13 commit
   claimed R060.5-G2's case-specific wording carried the work. The ablation
   shows the bare main-body rewording is enough. Variant A overshot.

5. **Side effect (uniform across A, B, D): "underlying question" trips
   prompt-engineer-v2 auto-load.** All three variants loaded the
   `prompt-engineer-v2` skill at tool call 2 because the wording matches its
   trigger heuristic. Harmless on the tested case; a vector to watch when
   future rules use meta-cognitive vocabulary.

6. **Variant D's reasoning is visible in opencode-pretty.** Reasoning
   summaries like *"**Investigating Git log discrepancies**"* and
   *"**Considering tool applicability**"* render normally. My earlier claim
   about encrypted reasoning blocking inspection was wrong — it was a
   SQLite-query-side mistake; `opencode-pretty <session-id>` surfaces the
   summaries.

## Conclusion and applied changes

Applied **Variant D** (minimal — reword R061 only) to:

- `opencode/agents/alan-default-ids.md` — R061 reworded; no new rule, no
  step-list renumbering, no other changes.
- `opencode/agents/alan-default.md` — same change without IDs.
- `docs/opencode-system-prompt/alan-default-commentary.md` — mirror with
  inline intent comment summarizing the ablation finding and pointing here.

Variant A (R060.5 + G1 + G2) is documented but not applied — the ablation
showed it was over-engineered.

## Open questions / follow-up trials

- **Robustness across verbs.** Tested only "diagnose and summarize". The
  "review X" / "what's going on with X" / "is X working" verb family should
  be tested separately; Variant D's wording is verb-agnostic but the empirical
  claim is single-verb only.

- **Variance.** One run per variant. The behavioral spread (5 vs 12 vs 10
  reads) is large enough to suggest the rule matters, but per-variant
  stochasticity is not characterized. A 3-run-per-variant follow-up would
  tighten that.

- **"Underlying question" trigger of prompt-engineer-v2.** Three runs all
  loaded the skill needlessly. If this becomes load on real tasks, reword to
  avoid the phrase (e.g., "user's actual decision," "what the user needs
  next").

- **Gate-template hook.** Earlier analysis suggested forcing the inferred
  question into the gate `# Task` heredoc template. Variant D works without
  that hook because R061's rewording fires at initial scoping; the gate-
  template idea is no longer needed for this failure mode.

## Reproduction

Worktree state:

```
git worktree add /tmp/ep-loop4-test ep-loop4
```

Prompt files (in `/tmp` during the trial; recreatable from this trial's
commit):

- Variant D prompt is the post-fix `opencode/agents/alan-default-ids.md`
  itself; just point inline config at the worktree's file.
- Variants A and B prompts are reconstructable by reverting the R061 reword
  and inserting the respective R060.5 block from the trial commit.

Task: see "Harness" above (single line, /tmp/task.md).

Inline config: see `/tmp/run-variant-{B,D}.sh` (kept during the trial; the
`OPENCODE_CONFIG_CONTENT` JSON is straightforward — single agent definition
pointing at the prompt file under test, `permission` set to `allow` for read /
glob / grep / list / bash / edit / write).
