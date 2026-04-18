<narrative_check>
FOR EACH NARRATIVE SECTION:

  EXTRACT: What pronouns appear? Quote first 3 sentences.
  EXTRACT: What verb forms? (active: 'I built' vs passive: 'was built')
  EXTRACT: What hedging words? ('might', 'could', 'may', 'perhaps')

  EXPECTED: First-person, active voice, definitive statements.
    RIGHT: 'I built this because...'
    WRONG: 'The tool was created to...'

  VIOLATIONS: | Section | Quote | Issue | Confidence |
</narrative_check>

<instructional_check>
FOR EACH INSTRUCTIONAL SECTION:

  EXTRACT: What verb forms open each instruction?
  EXTRACT: Any first-person pronouns? Quote them.

  EXPECTED: Imperative verbs, no first-person.
    RIGHT: 'Pass the --strict flag for full validation.'
    WRONG: 'I pass the --strict flag when I want full validation.'

  VIOLATIONS: | Section | Quote | Issue | Confidence |
</instructional_check>

<reference_check>
FOR EACH REFERENCE SECTION:

  EXTRACT: What subjects appear? ('The function', 'It', 'I')
  EXTRACT: Any opinion language? ('best', 'should', 'recommended')

  EXPECTED: Third-person declarative, factual.
    RIGHT: 'The function accepts three parameters...'
    WRONG: 'I accept three parameters...'

  VIOLATIONS: | Section | Quote | Issue | Confidence |
</reference_check>

<hybrid_boundary_check>
FOR HYBRID CONTENT:

  EXTRACT: Where do section boundaries occur?
  At each boundary, what voice is used before/after?

  EXPECTED: Clean voice shifts at section boundaries.
  COMMON FAILURE: First-person bleeding into usage instructions.

  VIOLATIONS: | Boundary | Before Voice | After Voice | Issue |
</hybrid_boundary_check>