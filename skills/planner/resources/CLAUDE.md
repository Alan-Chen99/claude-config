# resources/

Planner templates that scripts load by name through `get_resource()` (`skills/scripts/skills/planner/shared/resources.py`) and inject into an agent's prompt: an edit here changes what that agent is told.

## Files

| File                  | What                                                       | When to read                         |
| --------------------- | ---------------------------------------------------------- | ------------------------------------ |
| `plan-json-schema.md` | plan.json reference, injected into architect step 6 (`architect/plan_design_execute.py`) | Changing plan.json fields or the architect's plan writing |
