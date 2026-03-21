# Gate

After execution, run through this checklist. For each item, mark pass/fail and act on failures before responding.

- [ ] **Intent match** — Does the result match the step-1 interpretation? If evidence found during execution contradicts it: RESTART from step 1 with corrected understanding.
- [ ] **Complete scope** — Did the reframed instruction cover everything the user wanted? If partial: execute remaining parts now.
- [ ] **Assumptions held** — Did the codebase/environment match what was assumed? If not: report discovery, adjust approach.
- [ ] **Output tested** — Was every produced artifact (code, config, command) verified to work? If not: test now.
- [ ] **Root cause addressed** — Was the underlying cause fixed, not just a symptom? If surface-level: investigate deeper.
- [ ] **Loose ends reported** — Were all discoveries the user should know about surfaced? If not: report them.
