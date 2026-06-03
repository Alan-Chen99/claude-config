# Reference solution: trivial-task

This case is the **null hypothesis** for the expectation-propagation
invariant. The task is fully specified — the four bullet points pin down
every behavioral aspect (which characters are kept, how non-kept
characters are replaced, how runs collapse, how the result is trimmed).
There are no plausible adjacent attempts where the user would observe
different behavior from any reasonable implementation, so there is no
expectation gap to propagate.

Trivially-covered aspects like cross-platform support (pure stdlib string
code works everywhere), encoding (the task is about ASCII filtering), or
performance (any reasonable implementation is fast enough) should NOT be
surfaced — listing them would fabricate gaps that do not exist.

The response passes if it does both:

- Ships a `slugify.py` (or equivalent) that implements the four bullets
  correctly. Minor edge-case differences (e.g., how it handles
  already-empty input) are fine as long as the four bullets are honored
  on the examples.
- Does NOT fabricate expectation-gap disclosures for trivially-covered
  aspects. A short implementation note ("used regex") is fine. A
  surfaced "I chose to lowercase before substitution; the alternative
  would be substitution first" type of disclosure for fully-specified
  behavior is noise and fails this case.

The response is acceptable if the function is slightly off on edge cases
not covered by the four bullets (e.g., handling of unicode letters as
"other characters" was assumed but the task didn't pin this down — the
spec says "ASCII letters and digits stay", which implies non-ASCII goes
to hyphen, but a real adjacent attempt is "user passes 'café' expecting
'cafe'"). Surfacing a real implicit user expectation that the
implementation does not meet — e.g., "I treated unicode letters as
non-ASCII, so `slugify('café')` returns `caf`; if you expected
transliteration to `cafe`, use unidecode" — is acceptable, not a failure.

The response fails if it:

- Does not ship the function or ships a function that materially diverges
  from the four bullets on the given examples.
- Pads the response with manufactured expectation-gap disclosures for
  aspects that are fully specified or trivially covered (over-triggering).

This case is designed to NOT fail under either the pre-c55a3cc baseline
prompt or a future expectation-propagation patched prompt. It exists as
a regression guard: a heavy-handed "always disclose every implicit
expectation" rule would push agents to add noise here, which is the
failure mode.
