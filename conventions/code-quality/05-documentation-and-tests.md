<!-- applicable_phases: diff_review, codebase_review, refactor_code -->

# Documentation & Tests

Is this documented and tested correctly? Documentation that contradicts code is worse than none, tests that do not communicate behavior fail as documentation, schema drift causes runtime errors, and generated code without provenance misleads maintainers. Needs actual code. Grep hints and violations are starting points, not a closed list: flag whatever breaks a category's principle.

<code-mode>
Quote code or docs with file:line.
</code-mode>

## 1. Documentation Staleness

<principle>Documentation that contradicts code is worse than no documentation. Stale docs mislead readers and cause bugs.</principle>

<grep-hints>Docstrings with parameter names, @param, @return, TODO, FIXME</grep-hints>

<violations>
- [high] A parameter name in the docstring that is not in the signature; a docstring type conflicting with the type annotation (when one exists)
- [medium] A docstring describing a return value the code never returns; a comment making a strong claim ("always", "never", "must") that the code structurally contradicts
- [low] TODO/FIXME referencing completed or removed work
</violations>

<exceptions>Incomplete documentation. Missing docs. Outdated style in docs.</exceptions>

<threshold>Flag only when documentation is demonstrably incorrect, not merely incomplete: stale docs cause hallucinations, missing docs only mean less context.</threshold>

## 2. Test Quality as Documentation

<principle>Tests document expected behavior. When a test name does not say what behavior it verifies, it fails as documentation.</principle>

<grep-hints>`test_works`, `test_ok`, `test_success`, `test_case_`, `test_1`, `assert True`</grep-hints>

<violations>
- [high] A low-information test name (e.g., test_works, test_ok, test_success, test_case_1); a test with 0 assertions
- [medium] A test name shorter than 3 tokens (excluding the test\_ prefix); a name describing implementation, not behavior
- [low] A test asserting only True, None or trivial values; several near-identical test functions differing in inputs (use parameterized/table-driven)
</violations>

<exceptions>Tests referencing ticket numbers (e.g., TEST-1234, JIRA-567) for traceability. Smoke tests named test_works.</exceptions>

<threshold>Flag when the test name gives no behavioral information AND is not a ticket/regression reference.</threshold>

## 3. Generated and Vendored Code Awareness

<principle>Non-maintainable code (generated, vendored) must be clearly marked. Without provenance, maintainers modify code that should be regenerated.</principle>

<grep-hints>`_generated`, `_pb`, `.pb.go`, `vendor/`, `third_party/`, `node_modules/`</grep-hints>

<violations>
- [high] Generated files with no regeneration command in CLAUDE.md; vendored directories with no upstream source in CLAUDE.md
- [medium] External libraries copied into the repo without provenance
</violations>

<threshold>Flag when a file or directory matches a generation pattern (e.g., *.pb.go, *_generated.*, vendor/, third_party/) AND CLAUDE.md has no entry giving its provenance.</threshold>

## 4. Schema-Code Coherence

<principle>Schema and code must stay synchronized. A field referenced in code but absent from the schema, or the reverse, is drift that causes runtime errors.</principle>

<grep-hints>Schema file extensions (.proto, .graphql, JSON schema), field access patterns</grep-hints>

<violations>
- [high] Code references a field not in the schema definition; a schema field unused in any code path (dead field)
- [medium] Type mismatch between schema and code representation
</violations>

<exceptions>Intentional divergence marked with `:SCHEMA:` (e.g., `:SCHEMA: field 'legacy_id' unused; migration pending`). Fields used only in specific deployment configs.</exceptions>

<threshold>Flag when a field name in code has 0 matches in the corresponding schema file, or a schema field has 0 references in the codebase.</threshold>
