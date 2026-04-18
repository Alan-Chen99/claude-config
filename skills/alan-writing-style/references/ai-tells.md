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

<pattern_5_callbacks>
EXPLICIT CALLBACKS

  EXTRACT: List all phrases with 'just like', 'as mentioned',
  'as we saw', 'similar to above'.

  JUDGE each: Does it over-explain a connection?
    WRONG: 'just like during planning'
    RIGHT: State the fact and move on.

  For each violation, record:
    | Quote | Confidence (HIGH/MED/LOW) |
</pattern_5_callbacks>

<pattern_6_formula>
FORMULA FOLLOWING

  EXTRACT: What is the structure of each paragraph?
  (e.g., Statement -> Explanation -> Consequence)

  JUDGE: Are all paragraphs structured identically?
  Alan's writing varies. Some points just get stated.

  Note if rhythm feels artificial: YES/NO + explanation.
</pattern_6_formula>

<pattern_7_mixed_register>
MIXED REGISTER (if references are used)

  EXTRACT: List all quotes, cultural references, and anecdotes.
  Note the register of each:
    - Philosophical (Seneca, Marcus Aurelius, military history)
    - Pop culture (TV shows, films, memes)
    - Technical (papers, specifications)

  JUDGE: Is more than one register used?
    WRONG: Seneca quote + Silicon Valley reference
    RIGHT: All references from one register, or no references

  For each register clash, record:
    | Quote 1 | Register 1 | Quote 2 | Register 2 | Confidence |
</pattern_7_mixed_register>

<pattern_8_euphemism>
EUPHEMISTIC ORGANIZATIONAL LANGUAGE

  EXTRACT: List phrases containing:
    - 'alignment', 'transition', 'challenges'
    - 'not the ideal fit', 'opportunities for growth'
    - 'stakeholder concerns', 'performance gaps'

  JUDGE: Does each hide a simpler, plainer meaning?
    WRONG: 'necessitating a transition' = firing
    WRONG: 'alignment challenges' = wrong hire
    RIGHT: State the plain meaning directly

  For each euphemism, record:
    | Euphemism | Plain Meaning | Confidence |
</pattern_8_euphemism>

<pattern_9_structural_variance>
STRUCTURAL MONOTONY

  EXTRACT: Count sentences per paragraph
    | Para # | Sentence Count |
    | 1      | ?              |
    | 2      | ?              |
    | ...    | ...            |

  JUDGE: What is the variance?
    - Narrow (all 2-4 sentences): FLAG as monotonous
    - Wide (includes 1-sentence AND 5+ sentence): PASS

  REQUIRED: At least one paragraph that breaks the pattern
    - One-liner (<= 1 sentence): 'That's the core idea.'
    - Long block (>= 5 sentences): deep technical dive

  If no variance, record:
    | Issue | Range | Confidence |
    | Structural monotony | 2-4 sentences | HIGH |
</pattern_9_structural_variance>

<pattern_10_grounded_openers>
META-COMMENTARY VS GROUNDED OPENERS

  EXTRACT: First sentence of each major section/the document
    | Section | First Sentence |

  JUDGE each: Is it grounded or meta-commentary?

  META-COMMENTARY (FLAG):
    - 'Here is how this looks...'
    - 'This section explains...'
    - 'The following is an example of...'
    - 'Let me show you...'
    - 'In this article, we will...'
  Pattern: Describes the text rather than the subject

  GROUNDED (PASS):
    - 'I was writing an application that uses cryptographic...'
    - 'The codebase had a homegrown Log() method...'
    - 'Last month, we hit a production issue where...'
  Pattern: Immediately names project, technology, or problem

  For each meta-commentary opener, record:
    | Section | Quote | Confidence |
</pattern_10_grounded_openers>

<pattern_11_sentence_rhythm>
SENTENCE RHYTHM VARIANCE

  EXTRACT: Categorize sentences by word count
    SHORT (<8 words): punchy emphasis
      - 'That's not a good sign.'
      - 'Sigh.'
      - 'This is wrong.'
    MEDIUM (8-20 words): standard prose
    LONG (>20 words): complex technical explanations

  COUNT per category:
    | Category | Count | Example Quote |
    | Short    | ?     | '...'         |
    | Medium   | ?     | '...'         |
    | Long     | ?     | '...'         |

  JUDGE: Is there variety?
    FLAG if: 90%+ sentences in single category (typically medium)
    PASS if: Mix includes at least one SHORT and one LONG

  BONUS CHECK: Questions and exclamations
    EXTRACT: Any sentences ending in ? or !
    For narrative content: at least one question adds engagement
      - 'So how do we fix this?'
      - 'Victory!'

  If no variance, record:
    | Issue | Breakdown | Confidence |
    | Uniform rhythm | 95% medium | HIGH |
</pattern_11_sentence_rhythm>

<pattern_12_repetition>
REPEATED PHRASES / UNINTENTIONAL SELF-CALLBACKS

  EXTRACT: Identify phrases (5+ words) appearing multiple times.
  Also check for semantic repetition (same idea, different words).

  JUDGE each: Is repetition intentional emphasis or unintentional callback?
    WRONG: 'catches mistakes before they become code' in intro AND later section
    WRONG: Same benefit stated twice in different sections
    RIGHT: Intentional refrain with clear rhetorical purpose

  The principle: If you stated it once clearly, trust the reader.

  For each unintentional repetition, record:
    | Quote | Locations | Confidence (HIGH/MED/LOW) |
</pattern_12_repetition>

<pattern_13_overjustification>
OVER-JUSTIFICATION / DEFENSIVE CLAUSES

  EXTRACT: List sentences with:
    - Em-dash followed by explanatory 'why this matters' clause
    - Parenthetical adding justification
    - 'because' clause that anticipates unstated objection

  JUDGE each: Is the clause defending against anticipated 'so what?'
    WRONG: 'catches the drift -- the kind nobody notices until...'
    WRONG: 'Building on unknown foundation means rework when assumptions prove wrong.'
    WRONG: 'This prevents issues (which can be very costly later).'
    RIGHT: 'catches most problems before they compound.'
    RIGHT: 'Building on unverified code means rework.'

  The principle: State and move on. If the reader doesn't see the value, they'll ask.

  For each violation, record:
    | Quote | Defensive Clause | Confidence (HIGH/MED/LOW) |
</pattern_13_overjustification>