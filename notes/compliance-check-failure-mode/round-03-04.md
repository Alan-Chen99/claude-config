## Round 3-4: Rule fires within-frame only

**Spec bug (derivable in hindsight).** Ungrounded predicate; then guidance clause added (*"go beyond literal"*). Agent applied the check but only within its already-chosen frame — the choice of frame happens before the rule fires. Adding a guidance bullet widened the wrong-content candidate pool by one entry; did not open the missing-context pool.

F17 records the specific case that made this clean: R030's *"observations diverge from your model"* antecedent is false when the scope-restricted reading of the task made `PROMPT.md` read-as-data (problems-*in*-scratchpad, not problems-*about*-the-workflow). The conflation "agent saw X" ≠ "agent's model should be consistent with X" was an early diagnostic error. In hindsight: a body rule cannot restore access to a scope the agent has already discarded during frame selection.
