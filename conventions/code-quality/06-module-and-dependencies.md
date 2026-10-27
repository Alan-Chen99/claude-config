<!-- applicable_phases: design_review, codebase_review, refactor_design, refactor_code -->

# Module & Dependencies

Are boundaries clean, and does the architecture align with how features change? When changes ripple across unrelated modules or one feature touches many components, the boundaries are wrong. This concerns relationships between files and modules, not local code patterns. Grep hints and violations are starting points, not a closed list: flag whatever breaks a category's principle.

<design-mode>
Code Intent (Design Review): would the proposed design create circular dependencies, violate layer boundaries, or need many components touched to implement one feature? Quote the Code Intent description.
</design-mode>

<code-mode>
Quote import statements or describe the dependency structure.
</code-mode>

## 1. Module Structure

<principle>Modules should have clear boundaries with minimal coupling. When changes ripple across unrelated modules, the boundaries are wrong.</principle>

<grep-hints>Import graphs, dependency declarations, module boundaries</grep-hints>

<violations>
- [high] Circular dependencies (e.g., A imports B imports A); layer violations (e.g., domain importing infrastructure)
- [medium] Wrong cohesion (unrelated things grouped in one module); missing facades (module internals exposed directly)
- [low] God modules (too many responsibilities in one module)
</violations>

<exceptions>Circular deps within the same bounded context. Infrastructure adapters importing domain. Shared kernel patterns.</exceptions>

<threshold>Flag when a dependency causes compilation order issues OR a layer violation lets infrastructure corrupt the domain.</threshold>

## 2. Architecture

<principle>Architecture should align with change patterns. When adding a feature means touching many unrelated components, the architecture fights the domain.</principle>

<grep-hints>Component boundaries, service interfaces, configuration locations</grep-hints>

<violations>
- [high] Wrong component boundaries (features awkwardly split); single points of failure (no fallback, no retry paths)
- [medium] Scaling bottlenecks (synchronous where async is needed); monolith patterns in distributed code (or vice versa)
- [low] Missing abstraction layers (everything directly coupled); scattered configuration (no central policy, settings in many places)
</violations>

<exceptions>Intentional coupling for simplicity. Early-stage monolith. Bounded contexts with a shared kernel.</exceptions>

<threshold>Flag when the architecture forces cross-cutting changes for single-domain features.</threshold>
