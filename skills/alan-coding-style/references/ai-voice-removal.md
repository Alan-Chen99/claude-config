<scope>
SCOPE: These patterns apply to ALL human-readable text in the codebase.
This includes but is not limited to:
  - Documentation (docstrings, README files, inline comments)
  - Exception messages and error strings
  - Logging statements (log.info, log.warning, log.error, etc.)
  - CLI help text and user-facing output
  - Variable/function/class names that embed prose (e.g. descriptive constants)
  - Commit messages and PR descriptions drafted by the agent
  - Test descriptions and assertion messages

If text is meant for a human to read, these patterns apply. Do NOT skip
this step because the output is "just code" -- code is full of prose.
</scope>

<re_read>
Read your draft again, slowly, sentence by sentence.
Then check for AI-generated patterns.
</re_read>

VERIFICATION METHOD: Extract first, then judge.
For each pattern: (1) extract candidates, (2) assess each.

<pattern_1_tricolons>
TRICOLONS / RHYTHMIC PARALLELISM

  EXTRACT: List all sentences with 3+ comma-separated elements
  or parallel phrase structures.

  JUDGE each: Does it have manufactured symmetry?
    WRONG: 'Clear context, focused execution, reliable results.'
    RIGHT: 'The same agents run at every stage. Standards don't change.'

  For each violation, record:
    | Quote | Confidence (HIGH/MED/LOW) |
</pattern_1_tricolons>

<pattern_2_contrarian>
CONTRARIAN OPENERS / RHETORICAL REFRAMING

  EXTRACT: List all sentences with contrastive structure:
    - 'X isn't Y -- it's Z'
    - 'X is not Y -- it's Z'
    - 'This is not X' followed by counter-statement
    - 'not X but Y' / 'not X -- Y'
    - Any sentence negating X then asserting Y as replacement

  JUDGE each: Is it a rhetorical reframe that adds no information?
    WRONG: 'Review isn't a gate you pass once -- it's continuous.'
    WRONG: 'This is not overhead -- it catches mistakes.'
    WRONG: 'It's not about X -- it's about Y.'
    RIGHT: 'I run every plan through review before execution starts.'
    RIGHT: State what happens without the rhetorical negation.

  For each violation, record:
    | Quote | Confidence (HIGH/MED/LOW) |
</pattern_2_contrarian>

<pattern_3_metaphors>
DEAD METAPHORS

  EXTRACT: List all figurative language (metaphors, analogies).

  JUDGE each: Is it a cliche that has lost vividness?

  WRONG (by category -- if it appears in business writing, it's dead):
    FOUNDATION: 'flawed foundation', 'unknown foundation', 'solid foundation',
                'building blocks', 'cornerstone', 'pillars'
    JOURNEY:    'ever-evolving landscape', 'roadmap', 'path forward',
                'on the same page', 'moving forward'
    BUILDING:   'framework', 'architecture', 'construct', 'scaffold'
    NATURE:     'ecosystem', 'organic', 'root cause', 'cultivate'
    MACHINE:    'leverage', 'drive', 'fuel', 'mechanism'

  RIGHT: Use concrete consequences instead:
    'all need to be thrown away'
    'invalidates half of them'
    'you're building on code you haven't verified'

  For each violation, record:
    | Quote | Category | Confidence (HIGH/MED/LOW) |
</pattern_3_metaphors>

<pattern_4_emphasis>
HOLLOW EMPHASIS

  EXTRACT: List all sentences containing 'important', 'critical',
  'worth noting', 'key', 'crucial', 'essential'.

  JUDGE each: Does it announce importance instead of showing it?
    WRONG: 'This is important.'
    RIGHT: 'Without this, X happens.' (shows consequence)

  For each violation, record:
    | Quote | Confidence (HIGH/MED/LOW) |
</pattern_4_emphasis>

<!-- Pattern 5: prose explicit-callbacks ('as mentioned', 'just like') has no code equivalent — code comments rarely cross-reference other sections this way. Skip in code context. -->
<pattern_5_callbacks>
EXPLICIT CALLBACKS (CODE ADAPTATION)

  In code context, check for comments that narrate cross-references:
    WRONG: '# same logic as above', '# see also process_x'
    RIGHT: Extract shared logic into a function. No narrating comment needed.

  For each violation, record:
    | Quote | Confidence (HIGH/MED/LOW) |
</pattern_5_callbacks>

<!-- Pattern 6: prose paragraph-structure analysis has no code equivalent; function-shape analysis (docstring->validate->process->return) is the code-domain analog. -->
<pattern_6_formula>
FORMULA FOLLOWING (CODE)

  EXTRACT: What is the shape of each function?
  (e.g., docstring -> validate -> process -> return)

  JUDGE: Do all functions follow identical shape?
  Also check: cookie-cutter class layouts, repetitive method signatures.

  FLAG if: more than half of functions follow the same structure template.
  PASS if: a meaningful minority (at least 2) are clearly different in shape.

  Note if structure feels templated: YES/NO + example.
</pattern_6_formula>

<!-- Pattern 7: prose mixed-register has no code equivalent; naming register consistency is the code-domain analog. -->
<pattern_7_naming_register>
NAMING REGISTER CONSISTENCY

  EXTRACT: List all identifiers and note their naming style:
    - Terse/abbreviated: ctx, cfg, fn, ans, v
    - Full-word descriptive: context, configuration, function_ref, result, value
    - Mixed: some terse, some verbose in the same scope

  JUDGE: Is naming register consistent within each scope?
    FLAG if: same file mixes `ctx` and `configuration`, or `fn` and `callback_function`
    PASS if: all identifiers in a scope use the same register

  For each inconsistency, record:
    | Scope | Terse Example | Verbose Example | Confidence |
</pattern_7_naming_register>

<!-- Pattern 8: prose euphemistic language ('alignment challenges', 'performance gaps') has no code equivalent — error messages and comments don't use HR-speak. Adapted to vague error messaging. -->
<pattern_8_euphemism>
VAGUE ERROR MESSAGING (CODE ADAPTATION)

  EXTRACT: List error messages, exception strings, and log messages.

  JUDGE: Does each state a specific failure or hide it behind vagueness?
    WRONG: raise ValueError("something went wrong")
    WRONG: raise RuntimeError("invalid state")
    RIGHT: raise ValueError(f"expected int, got {type(x).__name__}")
    RIGHT: assert len(items) > 0, "empty input"

  For each vague message, record:
    | Message | Plain Meaning | Confidence |
</pattern_8_euphemism>

<!-- Pattern 9: sentence-per-paragraph counting has no code equivalent; function-shape variance (lines, nesting, params) is the code-domain analog. -->
<pattern_9_structural_variance>
STRUCTURAL MONOTONY (CODE)

  EXTRACT: For each function, measure:
    | Function | Lines | Nesting Depth | Param Count |
    | name     | ?     | ?             | ?           |

  JUDGE: What is the variance in function shape?
    - Narrow (all functions 5-10 lines, all flat, all 1-3 params): FLAG
    - Wide (includes short utilities AND longer complex functions): PASS

  REQUIRED: Mix of function shapes
    - Short utility (1-3 lines): pure transform, lookup
    - Long complex (15+ lines): multi-branch logic, pipeline

  If no variance, record:
    | Issue | Range | Confidence |
    | Function shape monotony | 5-10 lines all | HIGH |
</pattern_9_structural_variance>

<!-- Pattern 10: prose grounded-openers has no code equivalent; narrating-docstrings is the code-domain analog. -->
<pattern_10_narrating_docstrings>
NARRATING DOCSTRINGS

  EXTRACT: All docstrings and module-level comments.

  JUDGE each: Does it narrate the code or state a useful fact?

  NARRATING (FLAG):
    - 'This function takes X and returns Y' (restates the signature)
    - 'This class is responsible for managing...' (restates the name)
    - 'Helper function to...' (narrates role)
    - 'The following code...' (meta-commentary)
  Pattern: Describes what the code does in prose that adds nothing over reading it

  USEFUL (PASS):
    - 'Retries up to 3x because the upstream API has transient 503s'
    - 'Caller must hold the lock' (precondition not in the type)
    - No docstring at all (name + types tell the story)
  Pattern: States something the reader cannot derive from the signature

  For each narrating docstring, record:
    | Location | Quote | Confidence |
</pattern_10_narrating_docstrings>

<!-- Pattern 11: word-count-per-sentence has no code equivalent; line-complexity variance (SHORT/MEDIUM/LONG) is the code-domain analog. -->
<pattern_11_sentence_rhythm>
LINE COMPLEXITY VARIANCE (CODE)

  EXTRACT: Categorize code lines by complexity
    SHORT: single assignment, return, assert
      - `ans = x + 1`
      - `return ans`
      - `assert cond`
    MEDIUM: conditional, loop header, function call with args
    LONG: complex expression, multi-clause comprehension, long string

  COUNT per category:
    | Category | Count | Example |
    | Short    | ?     | '...'   |
    | Medium   | ?     | '...'   |
    | Long     | ?     | '...'   |

  JUDGE: Is there variety in line complexity?
    FLAG if: 90%+ lines are MEDIUM complexity
    PASS if: Mix includes SHORT (assignments, returns) and LONG (comprehensions)

  If no variance, record:
    | Issue | Breakdown | Confidence |
    | Uniform line complexity | 95% medium | HIGH |
</pattern_11_sentence_rhythm>

<!-- Pattern 12: prose repeated-phrases has no code equivalent; copy-paste code detection is the code-domain analog. -->
<pattern_12_copy_paste>
COPY-PASTE CODE

  EXTRACT: Identify code blocks (3+ lines) that appear nearly identically
  in multiple locations. Also check for near-duplicates (same structure,
  different variable names).

  JUDGE each: Should this be extracted into a shared function?
    FLAG if: same logic appears 2+ times with only name changes
    FLAG if: a function body is repeated with minor parameter differences
    PASS if: similar-looking code handles genuinely different cases

  For each duplicate, record:
    | Location 1 | Location 2 | Lines Duplicated | Confidence |
</pattern_12_copy_paste>

<!-- Pattern 13: prose over-justification has no code equivalent; defensive-coding is the code-domain analog. -->
<pattern_13_defensive_code>
DEFENSIVE CODE

  EXTRACT: List all validation, guard clauses, and error checks.

  JUDGE each: Is it defending against something that can actually happen?
    FLAG: isinstance check on a value whose type is already constrained
    FLAG: None check on a parameter that is never None in any call site
    FLAG: try/except around code that cannot raise that exception
    FLAG: len() > 0 check instead of truthy test
    PASS: assert for documenting an invariant the caller must maintain
    PASS: validation at a system boundary (user input, API response)

  The principle: trust internal code. Validate at boundaries only.

  For each defensive pattern, record:
    | Location | Check | Why Unnecessary | Confidence |
</pattern_13_defensive_code>

OUTPUT: Violation table with quoted text and confidence per pattern.
