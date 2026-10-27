<!-- applicable_phases: codebase_review, refactor_code -->

# Codebase Patterns

What emerges only from whole-codebase analysis? These issues are invisible in local review. Grep hints and violations are starting points, not a closed list: flag whatever breaks a category's principle.

<code-mode>
Describe the pattern across the files involved.
</code-mode>

## 1. Cross-File Comprehension

<principle>Understanding a flow should not require reading the entire codebase. When grasping one operation needs 5+ files and no guide, comprehension is broken.</principle>

<grep-hints>Call chains, event handlers, callback registrations</grep-hints>

<violations>
- [high] Implicit contracts between files (caller must know callee internals)
- [medium] Hidden dependencies (file A assumes file B ran first)
- [low] Scattered control flow (one operation spans 5+ files with no orchestrator)
</violations>

<exceptions>Well-documented module boundaries. Plugin architectures. Event-driven designs with clear event contracts.</exceptions>

<threshold>Flag when understanding a single operation requires reading 5+ files with no documentation of the flow.</threshold>
