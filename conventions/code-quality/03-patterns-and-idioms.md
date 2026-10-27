<!-- applicable_phases: diff_review, codebase_review, refactor_code -->

# Patterns & Idioms

Is this idiomatic for its language and version? Outdated patterns, verbose anti-patterns, needlessly complex expressions and dead code add cognitive load without benefit. Needs actual code. Grep hints and violations are starting points, not a closed list: flag whatever breaks a category's principle.

<code-mode>
Quote code with file:line.
</code-mode>

## 1. Boolean Expression Complexity

<principle>A boolean expression should be readable at a glance. If it needs mental evaluation to understand, it needs simplification or a name.</principle>

<grep-hints>`and.*and`, `or.*or`, `&&.*&&`, `||.*||`, `not.*not`, `!.*!`</grep-hints>

<violations>
- [medium] Multi-clause expressions (3+ AND/OR terms -> extract a named predicate); negated compound conditions (e.g., not (a and b) -> clearer positive form)
- [low] Mixed AND/OR without parentheses clarifying precedence; double/triple negatives (e.g., if not disabled, if not is_invalid)
</violations>

<exceptions>Complex conditions with clear structure and comments explaining the logic.</exceptions>

<threshold>Flag when the expression needs mental evaluation to understand.</threshold>

## 2. Conditional Anti-Patterns

<principle>Conditions should express intent directly. When a simpler form preserves the meaning, the complex form is an anti-pattern.</principle>

<grep-hints>`if.*return True.*else.*return False`, `try:.*except:.*pass`, `and do_`</grep-hints>

<violations>
- [medium] if cond: return True else: return False (just return cond); exception-based control flow (try/except as if/else)
- [low] Short-circuit side effects (e.g., cond and do_thing()); Yoda conditions without clear benefit (e.g., if 5 == x)
</violations>

<exceptions>Exception handling for actual exceptional conditions. Short-circuit for lazy evaluation.</exceptions>

<threshold>Flag mechanical anti-patterns only. Intent-preserving variations are style preferences.</threshold>

## 3. Modern Idioms

<principle>Modern language features exist to simplify common patterns. Older patterns kept without need add cognitive load.</principle>

<grep-hints>`for i in range(len(`, `+ str(`, `.format(`, callback patterns, `null` checks</grep-hints>

<violations>
- [medium] Old iteration patterns (e.g., manual index loops -> for-each, enumerate); deprecated API usage
- [low] Missing language features (e.g., destructuring, pattern matching); callbacks -> async/await; string concatenation -> f-strings/templates; manual null checks -> optional chaining, null coalescing
</violations>

<exceptions>Older patterns kept for compatibility. Performance-critical code avoiding allocations.</exceptions>

<threshold>Flag when the modern idiom is clearly better AND available in the project's language version. Do not flag style preferences.</threshold>

## 4. Readability

<principle>Code should be understandable in isolation. When understanding needs an external lookup or tribal knowledge, the code needs clarification.</principle>

<grep-hints>Boolean literals in function calls, magic numbers, unexplained constants</grep-hints>

<violations>
- [high] Boolean trap (e.g., fn(True, False) -> fn(enabled=True, debug=False)): any call whose argument meaning needs a look at the signature
- [medium] Magic numbers/strings (e.g., 42 -> MAX_RETRIES = 42); positional args where named params would clarify intent
- [low] Dense expressions (-> named intermediate variables); missing WHY comments on non-obvious decisions; implicit ordering dependencies between calls (document or make explicit)
</violations>

<exceptions>Well-known constants (0, 1, -1, 100). A boolean to an obviously named function (e.g., setEnabled(true)).</exceptions>

<threshold>Flag when meaning needs an external lookup. Self-evident code needs no comments.</threshold>

## 5. Zombie Code

<principle>Dead code is noise that misleads readers: code that cannot execute or is never called should be removed. Test: if I deleted this, would any test fail or behavior change?</principle>

<grep-hints>Commented-out blocks, `#if 0`, unreachable branches, unused variables; exported symbols with 0 callers, feature flags, configuration options, dead modules</grep-hints>

<violations>
- [high] Commented-out code blocks (>5 lines of code, not documentation); unreachable branches (e.g., else after unconditional return, dead switch cases); exported functions with 0 callers anywhere in the codebase; feature flags always true/false (never toggled in any environment)
- [medium] Unused local variables or parameters; dead flags (feature shipped, flag never removed)
- [low] Functions never called within their file; configuration options never read; dead modules (no imports from any live code path)
</violations>

<exceptions>Commented code explained as a debugging aid. Unused params required by an interface contract. Public API entry points. Plugin interfaces. Feature flags controlled externally. Backward-compatibility exports with a deprecation notice.</exceptions>

<threshold>Flag when code is demonstrably unreachable or unused -- exports, modules, flags and configuration across the whole codebase (needs a codebase view) -- AND no exception above applies.</threshold>
