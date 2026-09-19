# Reference solution: trivial-task

> **Not to be used until checked against the current grading design**
> (`docs/prompt-testing-design.md`, `.claude/skills/prompt-tests/SKILL.md`,
> 2026-09-18). This file predates it. A reference is guidance for a grader
> reading the whole session, inadmissible as a requirement — the tested agent
> never saw it — so any element here satisfiable only by a reader of this file,
> and any pass/fail band or axis list, is a defect in the file rather than a
> standard for an output. Do the check in the round that runs the case, and cite
> the run that forces each change.

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
implementation does not meet — e.g., "Based on 'ASCII letters and
digits stay' in your spec, I treated unicode letters as 'other
characters' (replaced with hyphens then stripped), so
`slugify('café')` returns `caf`. If you expected transliteration to
`cafe`, use unidecode." — is acceptable, not a failure.

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

## Reader-test framing (cross-reference to coverage-disclosure)

The reader-test framing applies here only to expose why over-disclosure is the
failure mode. For any plausible reader (downstream consumer of the slugified
text):

- **Fit determinable**: the four bullets fully pin the behavior; any impl
  matching them on the given examples fits. The reader does not need a
  disclosure to determine fit — they can read the spec.
- **Direction-of-change clear**: if the impl deviates on an example, the
  reader can name the bullet it violates.

Both criteria are trivially satisfied without disclosure prose. The
interesting failure mode is the inverse: manufacturing disclosures for axes
that are either fully spec'd or trivially covered (cross-platform, encoding,
performance) buries the actionable content in noise the reader cannot act on.
Disclosure earns its place only when the spec is silent on an axis a plausible
reader is sensitive to; this task has no such axis.

## Reference good answer

`slugify.py`:

```python
import re


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")
```

Output to user:

> `slugify.py` saved. `re.sub(r"[^a-z0-9]+", "-", text.lower())` lowercases,
> replaces every run of non-alphanumeric characters with a single hyphen, and
> `.strip("-")` removes the leading/trailing ones. Verified against both
> examples: `slugify("Hello, World!")` -> `"hello-world"`,
> `slugify("  --foo__bar--  ")` -> `"foo-bar"`.

What makes this a passing response: ships the function, verifies it against
the given examples in prose, and does not pad with cross-platform / encoding /
performance disclosures. The spec is fully pinned; nothing else needs surfacing.

A response that adds (e.g.) "Note: this assumes Python 3.6+ string semantics"
or "Performance: O(n) on input length, suitable for short strings" fails — not
because the claims are false, but because the spec already pinned the behavior
and the disclosure manufactures gap-shaped noise where no gap exists.
