# Intent Markers

Markers suppress QR checks for intentional code patterns.

## Format

`:MARKER: [what]; [why]`

- Semicolon separator REQUIRED
- `[what]` = specific pattern being marked
- `[why]` = rationale (invariant relied upon, safety guarantee, etc.)

## Markers

| Marker     | Purpose                          | Example                                              |
| ---------- | -------------------------------- | ---------------------------------------------------- |
| `:PERF:`   | Performance-critical intentional | `:PERF: unchecked bounds; loop invariant i<len`      |
| `:UNSAFE:` | Safety-critical intentional      | `:UNSAFE: raw pointer; caller ensures lifetime`      |
| `:SCHEMA:` | Data contract divergence         | `:SCHEMA: field unused; migration pending, rollback` |

## Validation

QR validates each marker's format (semicolon present, `[why]` non-empty):

- Valid marker: skip the relevant category checks for the marked code
- Missing semicolon or empty `[why]`: report MARKER_INVALID (MUST)
- Unmarked code: full scrutiny
