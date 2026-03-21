---
name: do
description: Meta-execution pipeline — transforms any request into intent identification, actionable reframing, execution, reflection with self-correction, and followup anticipation.
---

# /do

Process the user's request through this 5-step pipeline.

## Step 1: Reframe

Transform the request into the most actionable form.

| Request shape                                   | Reframed instruction                                         |
| ----------------------------------------------- | ------------------------------------------------------------ |
| "Can X work?" / "Is X possible?" / "Would X..." | Try X. Report whether it works, with evidence.               |
| "Build X" / "Create X" / "Make X"               | Build X. Run it. Verify it works. Fix problems.              |
| "Fix X" / "X is broken" / "X doesn't work"      | Diagnose root cause. Fix. Verify fix. Test edge cases.       |
| "Refactor X" / "Clean up X"                     | Refactor. Run tests. Verify no regression.                   |
| "Look into X" / "Investigate X"                 | Research X. Report findings with actionable recommendations. |

If the request contains multiple sub-tasks, decompose and address each.

## Step 2: Identify Expectations

Before acting, determine a list of implicit user expectations:

| Dimension    | Examples                                                             |
| ------------ | -------------------------------------------------------------------- |
| Given        | "rules in docs/CLAUDE.md"                                            |
| Action       | "change is documented, does not introduce inconsistency in codebase" |
| Knowledge    | "alternatives considered, rejected with good reason"                 |
| Verification | "Verified X against source code, Assumptions tested with commands"   |

## Step 3: Execute

Execute the reframed instruction. Bias toward action over discussion. Use all available tools.

## Step 4: Anticipate Followup

Generate the user's most likely followup in each category:

1. **"Are you sure that / did you verify..."** — What claim or result would the user challenge for evidence?
2. **"This is incomplete: ..."** — What part of the deliverable would the user point out as missing?
3. **"You didn't address ..."** — What aspect of the original request was skipped or underserved?
4. **other**: one that is non of the first 3 categories

IMPORTANT: MUST identify at least one possible followup in EACH category.

For each: evaluate whether it can be resolved non-destructively (no risky side effects, revertable with git or backups). If yes, got back to step 3 to resolve it now. If no, flag it in your response.

## Step 5: Gate

After execution, run through this checklist. For each item, mark pass/fail and act on failures before responding.

- [ ] **Intent match** — Does the result match the step-1 interpretation? If evidence found during execution contradicts it: RESTART from step 1 with corrected understanding.
- [ ] **Complete scope** — Did the reframed instruction cover everything the user wanted? If partial: execute remaining parts now.
- [ ] **Assumptions held** — Did the codebase/environment match what was assumed? If not: report discovery, adjust approach.
- [ ] **Output tested** — Was every produced artifact (code, config, command) verified to work? If not: test now.
- [ ] **Root cause addressed** — Was the underlying cause fixed, not just a symptom? If surface-level: investigate deeper.
- [ ] **Loose ends reported** — Were all discoveries the user should know about surfaced? If not: report them.
