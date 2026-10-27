<!-- applicable_phases: design_review, diff_review, codebase_review, refactor_design, refactor_code -->

# Naming & Types

If a reader sees only a name or type, will their mental model match actual behavior? Names are micro-documentation and types are contracts: when either lies, readers write bugs. Grep hints and violations are starting points, not a closed list: flag whatever breaks a category's principle.

<design-mode>
Code Intent (Design Review): does each proposed function or class name predict its behavior? Does the intent use domain types or raw primitives, and do they fit the concept? Does it introduce a new name for an existing concept? Quote the Code Intent description.
</design-mode>

<code-mode>
Quote code with file:line.
</code-mode>

## 1. Naming Precision

<principle>A name should predict behavior well enough that reading the implementation confirms rather than surprises.</principle>

<grep-hints>`Manager`, `Handler`, `Utils`, `Helper`, `Data`, `Info`, `process`, `handle`, `do`</grep-hints>

<violations>
- [high] Names describing HOW not WHAT (e.g., loopOverItems -> processOrders); verbs that lie (e.g., get that mutates, validate that parses)
- [medium] Implementation details in public API names; vague umbrella terms (e.g., Manager, Handler, Utils, Data)
- [low] Negated booleans (e.g., isNotValid -> isInvalid, disableFeature -> featureEnabled)
</violations>

<exceptions>Generic names in genuinely generic contexts (item in a generic collection, T in type params). Test: would a specific name add signal or just noise?</exceptions>

<threshold>Flag only when the name actively misleads. Imperfect but accurate names are style preferences.</threshold>

## 2. Missing Domain Modeling

<principle>Domain concepts should be explicit in code, not hidden in raw comparisons. A concept checked several ways belongs in a domain object.</principle>

<grep-hints>`== 'admin'`, `status ==`, `role ==`, `type ==`, magic numbers</grep-hints>

<violations>
- [high] Domain predicates in raw conditions (e.g., user.role == 'admin' -> user.can_edit()); magic value comparisons (e.g., status == 3 -> Status.APPROVED)
- [medium] String comparisons for state (e.g., mode == 'active' -> enum); business rules buried in conditions (extract to a domain object method)
</violations>

<exceptions>Explicit comparisons inside the domain layer itself. Config values compared once at startup.</exceptions>

<threshold>Flag when the same domain concept is checked via raw comparison in 2+ places.</threshold>

## 3. Type-Based Branching

<principle>Type dispatch scattered across code indicates missing polymorphism: when you branch on type in several places, the type itself should carry the behavior.</principle>

<grep-hints>`isinstance`, `typeof`, `instanceof`, `hasattr`, `in dict`, `.type ==`</grep-hints>

<violations>
- [high] isinstance/typeof chains (3+ branches -> polymorphism candidate); the same type dispatch in several locations
- [medium] Attribute-presence checks used as type dispatch (e.g., hasattr, key in dict)
- [low] Duck-typing conditionals that should be protocols/interfaces
</violations>

<exceptions>A single isinstance check for input validation. Type narrowing for type safety.</exceptions>

<threshold>Flag when the same type dispatch appears in 2+ places. Single-use type checks are often appropriate.</threshold>

## 4. Type Design

<principle>Domain concepts deserve their own types. Primitives that cross boundaries without validation invite bugs; value objects with validation prevent them.</principle>

<grep-hints>`str` for IDs, `float` for money, `dict` passed through a call chain, `Any`, `object`</grep-hints>

<violations>
- [high] Primitive obsession (e.g., userId as string -> UserId type with validation); missing value objects (e.g., money as float -> Money(amount, currency))
- [medium] Stringly-typed data (JSON strings -> typed objects); leaky abstractions (callers must know implementation details)
- [low] Optional explosion (many nullable fields -> separate types per state)
</violations>

<exceptions>Primitives in internal implementation, at serialization boundaries, and on performance-critical paths.</exceptions>

<threshold>Flag when primitives cross API boundaries without validation.</threshold>

## 5. Naming Consistency

<principle>A concept should have one name, within a file and across the codebase. Several names for one thing make readers doubt whether they are the same.</principle>

<grep-hints>Synonyms as variable prefixes (user/account/customer, config/settings/options, id/uid/identifier)</grep-hints>

<violations>
- [high] One entity under different names (e.g., user vs account vs customer), within a file or drifting across modules to integration points
- [medium] Inconsistent abbreviations (e.g., userId vs uid vs id)
- [low] Style inconsistency without semantic confusion
</violations>

<exceptions>Different names for genuinely different concepts. External API naming conventions. Domain-specific terminology. Aliasing for clarity at a specific scope. Legacy compatibility aliases in a bounded migration.</exceptions>

<threshold>Flag when one concept has 2+ names within a file, or 3+ names across modules (needs a codebase view), AND readers would doubt whether they refer to the same thing.</threshold>
