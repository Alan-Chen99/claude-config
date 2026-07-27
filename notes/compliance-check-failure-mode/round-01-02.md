## Round 1-2: Mis-anchored predicate

**Spec bug (derivable in hindsight).** Baseline `min.md`. R070 checked for *"downstream"* problems. Agent correctly said *"checked git, no downstream issues"* and passed. The anchor noun (`downstream`) predetermines the failure surface; user-direction non-compliance and operational staleness sit outside `downstream`. The rule fired correctly against the noun it was written around and missed everything else. Reading the rule together with the task's actual failure axes exposes the mismatch immediately.

14 further wording variants in round 2 (G4 wordings, R080/R030 body additions) confirmed reasoning-shape findings that recur throughout the investigation: batched-per-cycle gate loop; body-only rules do not surface reliably into post-gate working memory; search-target wording controls the HIT layer.
