<!-- applicable_phases: design_review, diff_review, codebase_review, refactor_design, refactor_code -->

# Structure & Composition

Can I understand this unit in isolation, and change it without understanding its dependents? Structure should reveal intent and isolate concerns. Grep hints and violations are starting points, not a closed list: flag whatever breaks a category's principle.

<design-mode>
Code Intent (Design Review): does the proposed function do one thing? Does the intent draw clear responsibility boundaries? Does the design inject dependencies or hard-code them? Is the component's definition complete in one place? Would its error handling match other components at the same level? Quote the Code Intent description.
</design-mode>

<code-mode>
Quote code with file:line.
</code-mode>

## 1. Function Composition

<principle>A function should do one thing, describable in a single sentence. When the description needs "and", the function likely needs splitting.</principle>

<grep-hints>Functions >50 lines, long parameter lists</grep-hints>

<violations>
- [high] God functions (multiple unrelated responsibilities); long parameter lists (4+ params signal a missing concept)
- [medium] Deep nesting (3+ levels of conditionals); mixed abstraction levels (high-level orchestration beside low-level detail)
- [low] Boolean parameters that fork behavior (consider splitting into two functions)
</violations>

<exceptions>Long functions that do one thing linearly (e.g., state machine, parser). Nesting depth from error handling.</exceptions>

<threshold>Flag when a function has multiple unrelated responsibilities. Length alone is not a smell.</threshold>

## 2. Control Flow Smells

<principle>Control flow should reveal intent, not obscure it. When following execution takes significant mental effort, the structure needs simplification.</principle>

<grep-hints>`elif.*elif.*elif`, `switch`, `case`, `? :.*? :`, ternary chains</grep-hints>

<violations>
- [high] Long if/elif chains (5+ branches -> lookup table or strategy pattern)
- [medium] Nested ternaries (2+ levels -> named variables); early-return candidates buried in nested else branches
- [low] Conditional assignment cascades; implicit else branches hiding edge cases
</violations>

<exceptions>Exhaustive pattern matching. State machines with explicit states.</exceptions>

<threshold>Flag when control flow obscures intent. Explicit branching for documented cases is acceptable.</threshold>

## 3. State and Flags

<principle>Boolean flags that interact create implicit state machines. When understanding state means tracking several flags, make the state machine explicit.</principle>

<grep-hints>`is_.*=`, `has_.*=`, `_flag`, `_state`, multiple boolean assignments</grep-hints>

<violations>
- [high] Boolean flag tangles (3+ interacting flags = implicit state machine)
- [medium] Stateful conditionals depending on mutation order
- [low] Defensive null chains (e.g., x and x.y and x.y.z -> optional chaining or null object)
</violations>

<exceptions>A single boolean for simple on/off state. Builder pattern flags.</exceptions>

<threshold>Flag when flags interact in ways that require mental state tracking. Independent flags are fine.</threshold>

## 4. Dependency Injection

<principle>Business logic should be testable without network, disk or database. Hard-coded dependencies make code untestable and tightly coupled.</principle>

<grep-hints>`datetime.now`, `time.time`, `os.environ`, `open(`, `requests.`, `http.`</grep-hints>

<violations>
- [high] Hard-coded dependencies (e.g., new Date() inline -> inject a clock); global state access (avoid or inject)
- [medium] Side effects mixed with computation (separate pure logic from effects); concrete class dependencies (depend on an interface)
- [low] Environment coupling (reads env vars directly -> inject config)
</violations>

<exceptions>Entry points that wire dependencies. Test utilities. Scripts meant to run directly.</exceptions>

<threshold>Flag untestable business logic. Infrastructure code at boundaries is expected to have dependencies.</threshold>

## 5. Definition Locality

<principle>A component's definition -- its identity, requirements, constraints and behavior -- should be complete at a single site. Test: to understand what it IS, how many locations must I read; to change what it requires, how many files must I edit?</principle>

<grep-hints>The same requirement checked in 2+ locations, component identity split across files, extraction with a default (args.get, kwargs.get, getattr with default)</grep-hints>

<violations>
- [high] The same requirement declared in 2+ locations (e.g., parser marks it required AND handler checks if missing); component identity split across files without clear ownership; a definition needing mental reassembly from 3+ sources
- [medium] Interface declared at one site and validated at another without a shared reference; defaults defined apart from the schema (e.g., type in schema, default in code)
</violations>

<exceptions>Dependency injection (the injected collaborator's definition lives with the collaborator: runtime wiring, not scatter). Composition (A uses B; B's definition is B's concern). Inheritance (intentional decomposition). Plugin architectures (clear ownership boundaries). Registry + reference (define once, reference many: the fix, not a smell).</exceptions>

<threshold>Flag when a definition is split across 2+ locations without clear ownership. Key test: who owns this fact? If ownership is unclear or duplicated, it is scatter. Common in LLM-generated code.</threshold>

## 6. Error Handling

<principle>Errors should preserve context, reach appropriate handlers, and follow one pattern per abstraction level, so a caller knows what to expect from similar operations.</principle>

<grep-hints>`except:`, `catch (`, `pass`, `# TODO`, `raise Error(`, mixed exception/return-code patterns, inconsistent error message formats</grep-hints>

<violations>
- [high] Swallowed exceptions (empty catch blocks); generic catches (e.g., catch Exception -> catch specific errors); incompatible error patterns for similar operations, within a class or across components at one abstraction level
- [medium] Errors at the wrong abstraction level (low-level errors leaking to callers); inconsistent exception hierarchies at one abstraction level
- [low] Missing context (raise Error('failed') -> raise Error(f'order {id}: {reason}')); no standard for error context/wrapping within a file or across modules
</violations>

<exceptions>A generic catch at top level with logging. Expected errors swallowed deliberately, with a comment. Different patterns for different abstraction levels (domain vs API vs infra). Wrappers translating between error styles. Legacy code under active migration.</exceptions>

<threshold>Flag when error handling obscures or loses information; a documented catch-all with logging is acceptable. Flag inconsistency when one class uses 2+ incompatible patterns for similar operations, or one abstraction level uses 3+ across files (needs a codebase view), AND no migration plan exists.</threshold>
