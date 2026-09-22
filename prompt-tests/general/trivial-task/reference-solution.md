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

## Why this case is kept

The only case that fails when the agent writes **more**. Every other case here
can be satisfied by adding a sentence, so without this one an edit that makes
agents verbose reads as an improvement everywhere it is measured.
