<!-- applicable_phases: design_review, codebase_review, refactor_design, refactor_code -->

# Cross-File Consistency

Do similar things behave alike across files? Similar APIs should share conventions, and a feature flag should be evaluated the same way everywhere. Needs a view of several files. Grep hints and violations are starting points, not a closed list: flag whatever breaks a category's principle.

<design-mode>
Code Intent (Design Review): does the proposed API match existing similar APIs? Quote the Code Intent description.
</design-mode>

<code-mode>
Quote code from multiple files showing the inconsistency.
</code-mode>

## 1. Interface Consistency

<principle>Similar APIs should have consistent signatures. When similar functions surprise users with different conventions, they cause bugs.</principle>

<grep-hints>Similar function signatures with different parameter orders, CRUD operation patterns, service method signatures</grep-hints>

<violations>
- [high] APIs with similar purposes and incompatible signatures that share consumers
- [medium] Inconsistent naming conventions across related functions
- [low] Mixed sync/async for similar operations without clear reason
</violations>

<exceptions>Intentional API differences. Domain-specific conventions. Versioned APIs. Overloads with a clearly distinct purpose.</exceptions>

<threshold>Flag when 2+ similar functions have different parameter orders (file scope) or 3+ APIs have incompatible signatures (codebase scope) AND the confusion affects consumers.</threshold>

## 2. Feature Flag Sprawl

<principle>Feature flags should be checked consistently. When the same flag is evaluated with different logic in different places, behavior becomes unpredictable.</principle>

<grep-hints>Feature flag checks, toggle patterns, conditional feature code</grep-hints>

<violations>
- [high] The same flag checked with different conditions in different locations
- [medium] Undocumented flag dependencies (flag A requires flag B)
</violations>

<exceptions>Flags with intentionally different behavior per context. A/B test variations. Gradual rollout logic.</exceptions>

<threshold>Flag when the same feature flag is checked with different logic in different places AND the difference is unintentional. Dead and never-toggled flags are Zombie Code (03).</threshold>
