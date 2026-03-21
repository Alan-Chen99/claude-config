# Anticipate Followup

Generate the user's most likely followup in each category:

1. **"Are you sure that / did you verify..."** — What claim or result would the user challenge for evidence?
2. **"This is incomplete: ..."** — What part of the deliverable would the user point out as missing?
3. **"You didn't address ..."** — What aspect of the original request was skipped or underserved?
4. **other**: one that is non of the first 3 categories

IMPORTANT: MUST identify at least one possible followup in EACH category.

For each: evaluate whether it can be resolved non-destructively (no risky side effects, revertable with git or backups). If yes, got back to step 3 to resolve it now. If no, flag it in your response.
