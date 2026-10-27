# Default Conventions

These conventions apply when project documentation does not specify otherwise.
Severity levels (MUST/SHOULD/COULD) are defined in `severity.md`.

## Priority Hierarchy

Higher tiers override lower. Cite backing source when auditing.

| Tier | Source          | Action                           |
| ---- | --------------- | -------------------------------- |
| 1    | user-specified  | Explicit user instruction: apply |
| 2    | doc-derived     | CLAUDE.md / project docs: apply  |
| 3    | default-derived | This document: apply             |
| 4    | assumption      | No backing: CONFIRM WITH USER    |

## Structural Conventions

<default-conventions domain="god-object">
**God Object**: >15 public methods OR >10 dependencies OR mixed concerns (networking + UI + data). Severity: SHOULD
</default-conventions>

<default-conventions domain="god-function">
**God Function**: >50 lines OR multiple abstraction levels OR >3 nesting levels. Severity: SHOULD.
Exception: Inherently sequential algorithms or state machines
</default-conventions>

<default-conventions domain="duplicate-logic">
**Duplicate Logic**: Copy-pasted blocks, repeated error handling, parallel near-identical functions. Severity: SHOULD
</default-conventions>

<default-conventions domain="dead-code">
**Dead Code**: No callers, impossible branches, unread variables, unused imports. Severity: COULD
</default-conventions>

<default-conventions domain="inconsistent-error-handling">
**Inconsistent Error Handling**: Mixed exceptions/error codes, inconsistent types, swallowed errors. Severity: SHOULD.
Exception: Project specifies different handling per error category
</default-conventions>

## File Organization Conventions

<default-conventions domain="test-organization">
**Test Organization**: Extend existing test files; create a new one only for a distinct module boundary OR >500 lines OR different fixtures. Severity: SHOULD (for unnecessary fragmentation)
</default-conventions>

<default-conventions domain="file-creation">
**File Creation**: Prefer extending existing files; create a new one only for a clear module boundary OR >300-500 lines OR a distinct responsibility. Severity: COULD
</default-conventions>

## Testing Conventions

<default-conventions domain="testing">
**Principle**: Test behavior, not implementation. Fast feedback.

**Test Type Hierarchy** (preference order):

1. **Integration tests** (highest value): end-user verifiable behavior, with real systems/dependencies (e.g., testcontainers), verifying component interaction at boundaries
2. **Property-based / generative tests** (preferred): cover a wide input space with invariant assertions, catching edge cases humans miss; use for functions with clear input/output contracts
3. **Unit tests** (use sparingly): only for highly complex or critical logic; they are a maintenance liability, brittle under refactoring, so prefer integration tests covering the same behavior

**Test Placement**: Tests are part of implementation milestones, not separate milestones. A milestone is not complete until its tests pass.

**DON'T**:

- Test external library/dependency behavior (out of scope)
- Unit test simple code (maintenance liability exceeds value)
- Mock owned dependencies (use real implementations)
- Test implementation details that may change
- Write one test per variant when parametrization applies (use parameterized fixtures)

Severity: SHOULD (violations), COULD (missed opportunities)
</default-conventions>

## Modernization Conventions

<default-conventions domain="version-constraints">
**Version Constraint Violation**: Features unavailable in the project's documented target version. Requires: documented target version. Severity: SHOULD
</default-conventions>

<default-conventions domain="modernization">
**Modernization Opportunity**: Legacy APIs, verbose patterns, manual stdlib reimplementations. Severity: COULD.
Exception: Project requires legacy pattern
</default-conventions>

## Testing Strategy Defaults

<default-conventions domain="testing-strategy">
**Default Test Type Preferences** (apply when project docs are silent; these are Tier 3 defaults, and user confirmation, Tier 1, overrides):

| Type        | Default Strategy            | Rationale                 |
| ----------- | --------------------------- | ------------------------- |
| Unit        | Property-based (quickcheck) | Few tests, many variables |
| Integration | Behavior-focused, real deps | End-user verifiable       |
| E2E         | Generated datasets          | Deterministic replay      |

Severity: TESTING_STRATEGY_VIOLATION (SHOULD) if contradicted without override.
</default-conventions>
