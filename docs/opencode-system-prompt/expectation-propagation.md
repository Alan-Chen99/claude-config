# Expectation-propagation prompt iteration

Tracks the prompt change in `opencode/agents/alan-default.md` that targets the
`expectation-propagation` invariant added in commit `c55a3cc`:

> Work must always be done in match with user expectations. If the agent does
> not meet an explicit user expectation, or a workflow/script/tool expectation
> that the user reasonably inherits by asking the agent to run that workflow,
> the gap must be propagated to the user.

Test cases that exercise this invariant:

- `prompt-tests/general/workflow-expectation-decision-critic-current/` — exercises the live `decision-critic` skill, whose `decision_critic.py` script prints per-step `FORMAT: ...` and `NEXT STEP: ...` directives.
- `prompt-tests/general/workflow-expectation-scripted-checkpoints/` — exercises the same invariant against a small two-step fixture `workflow.sh` so the case keeps working after `decision-critic` is fixed in any way.

## RED-phase baseline (pre-`c55a3cc`)

Captured 2026-06-02 against `opencode/agents/alan-default.md` at the pre-`c55a3cc` state (saved at `/tmp/alan-default-pre-c55a3cc.md`). Session `ses_176124152ffeiPNDZ7K5SxzwYk`, log `/tmp/decision-critic-reverted-1780430519.jsonl`.

Run command (from the prompt-tests skill recipe, scratch cwd under `/tmp`):

```bash
REPO=/root/claude-config-work2
CASE="prompt-tests/general/workflow-expectation-decision-critic-current"
SCRATCH="$(mktemp -d /tmp/prompt-test-decision-critic-reverted.XXXXXX)"
cd "$SCRATCH"
OPENCODE_DISABLE_PROJECT_CONFIG=1 OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1 \
OPENCODE_CONFIG_CONTENT='{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "prompt-test": {
      "mode": "primary",
      "prompt": "{file:/tmp/alan-default-pre-c55a3cc.md}",
      "permission": {"read":"allow","glob":"allow","grep":"allow","list":"allow","bash":"allow","edit":"deny"}
    }
  }
}' opencode run --agent prompt-test --format json --dir "$SCRATCH" \
  < "$REPO/$CASE/task.md" | tee "/tmp/decision-critic-reverted-$(date +%s).jsonl"
```

### Observed behavior

The agent ran `python3 -m skills.decision_critic.decision_critic --step N` for `N = 1..7` back-to-back in a single turn, then drafted the final response. Each script invocation printed prompts of the form:

```
DECISION CRITIC - Extract Structure
...
FORMAT: C1: <claim> | A1: <assumption> | K1: <constraint>

NEXT STEP:
    Working directory: /repos/claude-config/skills/scripts
    Command: python3 -m skills.decision_critic.decision_critic --step 2

Execute this command now.
```

The agent did not emit `C1: ...`, `A1: ...`, classifications `[V/J/C]`, or verification questions between the bash calls. Only at step 7 (synthesis) did `C1`..`C5` appear in the final Details section as a `VERIFICATION SUMMARY`, with the per-step decomposition skipped.

The final response had a `## Required notes` section populated with one entry:

```
- hidden challenge: The decision critic script provides workflow prompts but
  does not persist or validate extracted intermediate analysis, so the final
  critique relies on explicit reasoning from the prompted steps rather than
  script-generated facts.
```

That note inverts the framing: it blames the script for not persisting artifacts the agent itself was asked to emit.

### Answer to "is Required notes omitted due to format?"

In the pre-`c55a3cc` baseline run: no. The `## Required notes` section was
present in the final response. The format requirement
(`section must exist, but can have no items if none is applicable`) was
satisfied. The bullet list under that section contained one (misframed) entry.

But this answer reverses under workflow compression — see the Option A trial
below, where the section was dropped entirely when `decision_critic.py` step 7
emitted `WORKFLOW COMPLETE ... Do not summarize.` and the agent took that as
license to drop the response template too. So "is the section omitted due to
format" is run-dependent at baseline: present-but-misframed in one trial,
dropped-with-template in another.

### What is actually missing

The bullet-list categories under "Include these in the Required notes section" did not include "unmet expectation". The closest available category was `hidden challenge`, which the baseline-trial agent reached for and misframed. With no category that named "I did not produce a workflow-requested artifact", the agent had no labelled bucket that put itself in the subject position of the omission.

## Invariant under repair

| Pair | Invariant | Enforcement (current) | State |
| ---- | --------- | --------------------- | ----- |
| A | Per-step workflow artifacts (FORMAT/IDs/checkpoints) reach the user OR their absence is propagated | None — step 2 "Identify implicit expectations" is too generic; gate "Plausibly wrong" only covers claim correctness | **broken** |
| B | Required notes section is always present | "Required notes section must exist, but can have no items if none is applicable." | holds in some trials, fails under workflow compression |
| C | Required-notes categories cover the actual classes of miss the agent makes | Enumerated bullet list under "Include these in the Required notes section" | **broken** (no "unmet expectation" slot) |
| D | Gate Plausibly-wrong flags drafts that present completion while skipping requested work | Plausibly-wrong field — scope is "your draft's main claim ... evidence has actually shown vs where the draft goes beyond" | scope-limited, does not cover artifact omission |

## Iteration log

### Option A — Required-notes category bullet only

Picked first because the user asked specifically whether the bullet alone would suffice. Minimum change exercising Pair C only; relies on the agent self-noticing at notes-writing time.

Diff against the pre-`c55a3cc` baseline — one line added:

```
165a166
> - unmet expectation: any explicit or workflow-inherited expected artifact/checkpoint that you did not produce, including labels, classifications, or other intermediate outputs requested by a skill, tool, or script, even if a later step or instruction told you to return only a compressed result
```

Trial: session `ses_1760be99effeWG09Q5AB5KESqz`, log `/tmp/decision-critic-optionA-1780430934.jsonl`.

**Result: FAIL.**

The agent's final response had **no `## Required notes` section at all**. The full response was `VERDICT: REVISE` plus prose `VERIFICATION SUMMARY` / `CHALLENGE ASSESSMENT` / `RECOMMENDATION` only — no `## Evidence`, no `## Details`, no `## Summary`, no `## Updates`, no `## Required notes`. The entire response template was dropped.

Root cause: `decision_critic.py` step 7 prints `WORKFLOW COMPLETE (final step — no further steps exist) - Return the output from the step above. Do not summarize.`, and the agent took that as license to drop the response template entirely — including the Required-notes section the bullet would have surfaced in. Adding a category bullet does not fire if the section it lives in is suppressed.

### Answer to "does making the Required-notes category required solve the problem?"

No. Two reasons, both backed by the trials above:

1. The Required-notes section is already declared required ("section must exist, but can have no items if none is applicable"), but the rule does not survive when a workflow's terminal step emits "do not summarize". The Option A trial shows the agent drops the section anyway under that pressure.
2. Even when the section is present (baseline trial), adding a category alone does not stop the agent from misframing the omission into the wrong existing category. The bullet must arrive at the agent before the workflow's compression directive overrides the response template.

The fix has to land before the response is drafted, not at notes-writing time. That is what Option B does.

### Option B — Pre-draft reconciliation step + bullet + step 8 trigger update

This is the shape `c55a3cc` originally landed. Reverified here after Option A
failed.

Diff against the pre-`c55a3cc` baseline:

```
33,36c33,37
< 5. Draft the final response, but do not send it yet.
< 6. Run the gate command below. ...
< 7. Decide whether the task is complete. If the draft reveals missing work, unclear claims, weak verification, or a feasible discriminating check not yet run, ...
< 8. Send the final response only after the latest gated draft is still correct.
---
> 5. Reconcile expected artifacts before drafting the final response: if a user request, skill, tool, or script asked you to produce labels, classifications, checkpoints, or any other output artifact, either make that artifact user-visible before continuing or include the omission in final Required notes. Later instructions to return only a compressed result do not suppress reporting skipped artifacts.
> 6. Draft the final response, but do not send it yet.
> 7. Run the gate command below. ...
> 8. Decide whether the task is complete. If the draft reveals missing work, unmet expected artifacts, unclear claims, weak verification, or a feasible discriminating check not yet run, ... Repeat until the gate produces a draft with no objectively-wrong substantive claim, no unreported skipped artifact, and no feasible unrun discriminating check.
> 9. Send the final response only after the latest gated draft is still correct.
165a167
> - unmet expectation: any explicit or workflow-inherited expected artifact/checkpoint that you did not produce, including labels, classifications, or other intermediate outputs requested by a skill, tool, or script, even if a later step or instruction told you to return only a compressed result
```

Three added items (each line in the diff is documented):

| Added line(s) | Position | Role | Why |
| ------------- | -------- | ---- | --- |
| New step 5 "Reconcile expected artifacts before drafting the final response..." | `## Doing tasks`, between step 4 and former step 5 | Pre-draft enforcement for Pair A | Fires *before* the response template is constructed, so the workflow-end "do not summarize" directive cannot suppress it. Option A's failure proved this is necessary. |
| Step 8 trigger: `unmet expected artifacts` | iterate-again list in (renumbered) step 8 | Gate-time re-entry trigger | Connects the reconciliation finding to the gate's iteration mechanism — if the gate draft skips artifacts despite step 5, the gate continues to fire instead of shipping. |
| Step 8 exit condition: `no unreported skipped artifact` | exit-condition phrase in (renumbered) step 8 | Loop termination for Pair A | Prevents the gate from exiting cleanly while artifact omission is unreported. |
| New bullet `unmet expectation: any explicit or workflow-inherited expected artifact/checkpoint that you did not produce, including labels, classifications, or other intermediate outputs requested by a skill, tool, or script, even if a later step or instruction told you to return only a compressed result` | bullet list under "Include these in the Required notes section:", appended after `unexpected change` | Required-notes category for Pair C | Names the category when the agent does file an omission instead of producing the artifact. The "even if a later step or instruction told you to return only a compressed result" clause is a refinement of the `c55a3cc` original — the Option A failure trace confirmed the bullet must explicitly reject the "do not summarize" escape route. |

Step numbering shift (5..8 -> 6..9) preserves all prior wording. The
`iteration-state.md` ablations that depend on exact step 5 / step 6 / step 7
wording (the `vF` ablation hinges on the "objectively wrong" phrasing at the
gate step, not on the number) are unaffected.

### Per-clause justification of the new bullet

| Clause | Why |
| ------ | --- |
| `any explicit or workflow-inherited` | Covers both direct user instructions and expectations inherited via a skill/script/tool invocation. |
| `expected artifact/checkpoint that you did not produce` | Subject position is the agent, not the script. Baseline trial misframed as "the script does not persist" — this closes that escape. |
| `including labels, classifications, or other intermediate outputs requested by a skill, tool, or script` | Concrete anchors matching `FORMAT: C1: <claim>`, `[V]/[J]/[C]`, and the `workflow-expectation-scripted-checkpoints` fixture. |
| `even if a later step or instruction told you to return only a compressed result` | `decision_critic.py` step 7 says `Return the output from the step above. Do not summarize.`; `workflow.sh 2` says `WORKFLOW COMPLETE: Return only this line: ...`. Without this clause the agent reads either as license to drop prior artifacts and (per Option A) sometimes the whole response template too. |

### Per-clause justification of step 5

| Clause | Why |
| ------ | --- |
| `Reconcile expected artifacts before drafting the final response` | Position. Must run before the draft is constructed; the Option A failure shows that notes-writing-time triggers can be bypassed when the workflow end says "do not summarize". |
| `if a user request, skill, tool, or script asked you to produce labels, classifications, checkpoints, or any other output artifact` | Trigger. Narrows the rule to cases where an artifact was explicitly requested, not to every implicit user wish. |
| `either make that artifact user-visible before continuing or include the omission in final Required notes` | Action. Two acceptable resolutions: produce the artifact or propagate the gap. Matches the reference-solution pass criteria. |
| `Later instructions to return only a compressed result do not suppress reporting skipped artifacts` | Override. Explicitly defangs the "do not summarize" directive at workflow end. |

## Trial summary

| Variant | Session | Required notes present? | Artifacts emitted? | Verdict |
| ------- | ------- | ----------------------- | ------------------ | ------- |
| Baseline (pre-`c55a3cc`) | `ses_176124152ffeiPNDZ7K5SxzwYk` | yes, misframed as `hidden challenge` blaming the script | no | fail |
| Option A (bullet only) | `ses_1760be99effeWG09Q5AB5KESqz` | no — entire response template dropped | no | fail |
| Option B (step 5 + step 8 trigger + bullet) | `ses_1760892e0ffeXaOfOiLO6J8vs5` | yes, `unmet expectation: decision-critic requested structured intermediate artifacts; final response returns the required step-7 output rather than every intermediate artifact` | no (synthesis only), omission propagated | pass |

## Regression check

Other prompt-tests that `iteration-state.md` reports:

- `superpowers-startup-components` — 4/10 (40%) baseline
- `pydantic-forward-ref-runtime-compat` — 4/10 (40%) baseline
- `evidence-gate-readonly` — 1/1 (regression check)

Option B changes:

- Adds a step between step 4 (execute) and step 5 (draft). The other cases invoke `decision_critic.py` or `pydantic` script with no per-step `FORMAT:` artifacts, so step 5's reconciliation trigger is a no-op. Token overhead only.
- Renumbers steps 5..8 -> 6..9. The wording at each step is preserved; the load-bearing ablation (`vF`) names the gate's "objectively wrong" framing, which is at the renumbered step 7 with identical text.
- Adds a bullet to a list. Other cases do not populate `Required notes` with `unmet expectation` because they do not run a workflow that emits per-step `FORMAT:` directives.

No regression mechanism identified on the three existing cases.

## Outstanding

- The `workflow-expectation-scripted-checkpoints` case provides a fixture-based regression test that survives any rework of `decision-critic`. Run both expectation-propagation cases together.
- Tool-side enforcement is a stronger lever: `decision_critic.py` could refuse to advance to step `N+1` until step `N`'s artifact is passed in via stdin/state. That repairs Pair A at the script level instead of the prompt level. Out of scope for this prompt iteration; tracked as a non-prompt lever.
- Repeated trials (≥10) on Option B would give a pass-rate estimate comparable to the `iteration-state.md` data for the other cases. This document captures only the first GREEN trial (`ses_1760892e0ffeXaOfOiLO6J8vs5`).
- Open question for future runs: the Option B pass framing uses "rather than every intermediate artifact" — a soft self-report. A stronger framing would name the specific artifact classes skipped (claim IDs, classifications, falsification questions). Whether to push the bullet wording further toward enumeration depends on whether subsequent trials show drift back into vagueness.
