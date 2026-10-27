# Plan JSON Schema

The CLI assigns every `id` and `version`; `plan_id`, `created_at` and `frozen_at` are set by scripts.

```
plan.json
  overview:
    problem: string
    approach: string

  planning_context:
    decisions: [Decision]                -- Decision Log
      id: DL-###
      decision: string
      reasoning: string                  -- premise -> implication -> conclusion
    rejected_alternatives: [RejectedAlternative]
      id, alternative, rejection_reason: string
      decision_ref: DL-###
    constraints: [string]                -- e.g. "MUST: support Python 3.9+ (user-specified)"
    risks: [Risk]
      id, risk, mitigation: string
      anchor: "file:L###-L###" | null
      decision_ref: DL-### | null

  invisible_knowledge:                   -- transfers to future LLM sessions
    system: string                       -- architecture, data flow, structure rationale
    invariants: [string]
    tradeoffs: [string]

  milestones: [Milestone]
    id: M-###
    number: int
    name: string
    files: [string]
    flags: [string]                      -- e.g. "error-handling", "needs-rationale"
    requirements: [string]
    acceptance_criteria: [string]
    tests: [string]                      -- "file:tests/test_auth.py", "scenario:EDGE empty token returns 401", "skip:no integration environment"
    code_intents: [CodeIntent]
      id: CI-M-###-###
      file: string
      function: string | null
      behavior: string
      decision_refs: [DL-###]
    code_changes: [CodeChange]           -- Developer (diff) and Technical Writer (doc_diff) fill these
    is_documentation_only: bool
    delegated_to: string | null

  diagram_graphs: [DiagramGraph]
    id: DIAG-###
    type: architecture | state | sequence | dataflow
    scope: overview | invisible_knowledge | milestone:M-###
    title: string
    nodes: [{id, label, type | null}]
    edges: [{source, target, label, protocol | null}]
    ascii_render: null                   -- Technical Writer fills

  waves: [{id: W-###, milestones: [M-###]}]   -- run in order; milestones within a wave run in parallel
```

## Validation Rules

`validate --phase plan-design` fails unless:

- every `decision_ref` and `decision_refs` entry names an existing decision
- every edge's `source` and `target` name nodes of its own diagram, and a `milestone:` scope names an existing milestone
- `overview.problem` is set, there is at least one milestone, and each milestone has at least one code intent

## Temporal Contamination

All string fields must avoid:

1. **Change-relative**: "will be added", "new function", "modified to"
2. **Baseline reference**: "original", "existing", "current"
3. **Location directive**: "see below", "above section"
4. **Planning artifact**: "TODO", "FIXME", "implement later"
5. **Intent leakage**: "should", "needs to", "must be implemented"

Write as if code already exists in final state.
