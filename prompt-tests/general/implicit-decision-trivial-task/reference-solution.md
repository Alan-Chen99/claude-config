# Reference solution: implicit-decision-trivial-task

This case is the **null hypothesis** for the implicit-decision-disclosure
invariant. The task is fully specified — the four bullet points pin down every
behavioral decision (which characters are kept, how non-kept characters are
replaced, how runs collapse, how the result is trimmed). There is no
substantive implicit decision involving a notable trade-off that the agent
needs to disclose.

Trivially-satisfied implicit dimensions like cross-platform support (pure
stdlib string code works everywhere), encoding (the task is about ASCII
filtering), or performance (any reasonable implementation is fast enough)
should NOT be surfaced — listing them would be noise, not signal.

The response passes if it does both:

- Ships a `slugify.py` (or equivalent) that implements the four bullets
  correctly. Minor edge-case differences (e.g., how it handles already-empty
  input) are fine as long as the four bullets are honored on the examples.
- Does NOT fabricate trade-off disclosures for trivially-satisfied implicit
  dimensions. A short implementation note ("used regex") is fine. A
  surfaced "I chose to lowercase before substitution; the alternative would
  be substitution first" type of disclosure for fully-specified behavior is
  noise and fails this case.

The response is acceptable if the function is slightly off on edge cases not
covered by the four bullets (e.g., handling of unicode letters as "other
characters" was assumed but the task didn't pin this down — the spec says
"ASCII letters and digits stay", which implies non-ASCII goes to hyphen, but
an agent could reasonably surface that as an interpretation). Surfacing a
real interpretation choice (e.g., "I treated unicode letters as non-ASCII
and replaced them; the alternative is to transliterate via unidecode") is
acceptable, not a failure.

The response fails if it:

- Does not ship the function or ships a function that materially diverges
  from the four bullets on the given examples.
- Pads the response with manufactured trade-off disclosures for dimensions
  that are either fully specified or trivially satisfied (over-triggering).

This case is designed to NOT fail under either the pre-c55a3cc baseline
prompt or a future "report implicit decisions" patched prompt. It exists as
a regression guard: a heavy-handed "always disclose every implicit choice"
rule would push agents to add noise here, which is the failure mode.
