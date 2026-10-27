<!-- applicable_phases: diff_review, codebase_review, refactor_code -->

# Repetition & Consistency

Does each piece of logic, validation and business rule have a single source of truth? When the same thing lives in several places, a bug must be fixed everywhere -- and it won't be -- and the copies drift apart. Needs actual code. Grep hints and violations are starting points, not a closed list: flag whatever breaks a category's principle.

<code-mode>
Quote code with file:line showing the duplication or inconsistency.
</code-mode>

## 1. Duplication

<principle>Code should have a single source of truth. Test: if I fixed a bug here, where else would I need to fix it? The same transformation in several files is a missing abstraction trying to emerge.</principle>

<grep-hints>Identical multi-line blocks, similar function bodies, function names suggesting similar purpose across modules, parallel implementations, repeated configuration shapes</grep-hints>

<violations>
- [high] The same code block duplicated (3+ lines, logic not just boilerplate); the same transformation applied in 3+ files
- [medium] Copy-paste with minor variations; parallel class hierarchies doing similar things differently; copy-paste inheritance (similar classes with minor variations)
- [low] A common pattern not extracted to a shared location; data pipelines or configuration patterns repeated without abstraction
</violations>

<exceptions>Intentionally different logic serving different purposes. Test setup code. Generated/vendored code. Deliberate isolation for modularity. Similar code in different bounded contexts. Templates/generators producing similar code.</exceptions>

<threshold>Flag when a bug fix would require changing multiple locations AND the duplication is unintentional. Across files, flag when a pattern appears in 3+ implementations AND extracting a shared abstraction is the fix.</threshold>

## 2. Validation Scattering

<principle>Validation rules should live in one place. Implemented several times, the copies diverge -- and some will be wrong.</principle>

<grep-hints>Repeated regex patterns, duplicate bounds checks, email/phone/format validation across locations</grep-hints>

<violations>
- [high] Validation rules diverged between implementations
- [medium] The same validation repeated without a shared implementation
- [low] Defensive re-validation deeper in the call chain
</violations>

<exceptions>Validation at trust or service boundaries. Defense-in-depth by design. Context-specific validation rules.</exceptions>

<threshold>Flag when identical validation appears 3+ times (file scope) or in 5+ files (codebase scope) AND the implementations have diverged or will diverge.</threshold>

## 3. Business Rule Scattering

<principle>Business rules should have a single source of truth. When the same decision is made in several places, they will eventually disagree. Test: if the rule changes, how many places need updating?</principle>

<grep-hints>Repeated conditional patterns, magic numbers in multiple places, pricing/permission/eligibility logic</grep-hints>

<violations>
- [high] The same business decision in several places that could diverge
</violations>

<exceptions>Orchestration calling multiple rule checks. Rules intentionally duplicated for service isolation. Per-tenant/region rule variations. Caching of computed rules.</exceptions>

<threshold>Flag when the same business decision is made in 2+ places (file scope) or 3+ files (codebase scope) AND they have diverged or could diverge independently.</threshold>

## 4. Condition Pattern Repetition

<principle>Repeated boolean expressions should be named predicates. When the same condition appears everywhere, changing it means finding every occurrence.</principle>

<grep-hints>Identical boolean expressions, repeated guard clauses, permission/feature-flag check patterns</grep-hints>

<violations>
- [high] An identical condition in 3+ places (file) or 5+ files (codebase)
- [low] The same guard clause pattern across related functions
</violations>

<exceptions>Standard guard clauses (null checks, bounds checks). Framework-required patterns. Simple conditions that read clearly inline.</exceptions>

<threshold>Flag when an identical condition appears 3+ times (file scope) or in 5+ files (codebase scope) AND extracting a named predicate would reduce the bug surface.</threshold>
