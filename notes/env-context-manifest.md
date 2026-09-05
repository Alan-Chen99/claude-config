# `env-context-manifest.json`: why three literals need whole-binary counts, not a window

Investigated 2026-09-02 against the installed Claude Code **2.1.235** binary
(`$CLAUDE_CODE_EXECPATH`, ~331 MB). `docs/env-context-manifest.json`'s
`window_literals` are extracted from a fixed byte window around one occurrence
of the anchor string `You have been invoked in the following environment: `.
Three fields this hook reimplements — `Platform: `, `Shell: ` (via `Kml()`),
and the git-stash caution `cTm` — never show up in that window, each for a
different reason, so each gets a `required_literals` entry instead: a
whole-binary occurrence count taken at pin time, which Task 6 re-derives and
diffs. This note is the derivation, with commands, so a future re-pin can
reproduce every number below rather than trust it.

An earlier draft of `required_literals`'s comment attributed the whole split
to "a different string-table region" and got the arithmetic behind the
`Platform: ` count wrong. Both are corrected here; see the two sections below
for what was actually true.

## The binary embeds the app twice

`data.find(ANCHOR)` (Python bytes, first match only) is how the manifest
generator locates its window. But the anchor string occurs **four** times:

```
$ python3 -c "
from pathlib import Path
import os
data = Path(os.environ['CLAUDE_CODE_EXECPATH']).read_bytes()
ANCHOR = b'You have been invoked in the following environment: '
start = 0
while True:
    i = data.find(ANCHOR, start)
    if i < 0: break
    print(i)
    start = i + 1
"
158403952
158412992
309456692
309457862
```

Two clusters, ~9,040 bytes apart within each, and the clusters themselves
~151,052,900 bytes apart. Reading the bytes around each pair confirms two
structurally different embeddings of the same source:

- **~158.4M (both members ~9,040 bytes apart):** individual strings
  separated by non-printable/structural bytes — consistent with a serialized
  V8 code-cache or heap-snapshot representation, where each string is its own
  length-prefixed record. This is the region `window_literals`'s window
  actually scans (anchored on the *first* occurrence, 158403952).
- **~309.46M (members ~1,170 bytes apart):** contiguous, syntactically
  intact minified JS — real `${...}` template syntax, commas, function
  bodies. This reads like an embedded copy of the actual source text
  (plausibly for source maps / `Function.prototype.toString` / stack
  traces), not a code cache.

Each pair's two members are `_dE`'s occurrence of the anchor and `vdE`'s
(the two functions in `globals/21.js` that both open with this anchor
string; `ydE`, which shares most of the same field labels, opens with a
different line and carries no anchor of its own).

This "everything appears twice" pattern is corroborated by every window
literal, not just the anchor:

| literal | whole-binary count | expected from source | note |
| --- | --- | --- | --- |
| `OS Version: ` | 6 | 3 functions (`ydE`,`_dE`,`vdE`) × 2 copies | clean |
| `Is a git repository: ` | 4 | 2 functions (`_dE`,`vdE`) × 2 copies | `ydE` uses "Is directory a git repo: " instead |
| `Primary working directory: ` | 4 | 2 functions (`_dE`,`vdE`) × 2 copies | `ydE` uses "Working directory: " instead |
| `Additional working directories:` | 6 | 3 functions × 2 copies | see note below |

`Additional working directories:` is 6 because it's a **substring** match:
`_dE`/`vdE` use the literal without a trailing space (a standalone array
element, list joined separately), `ydE` uses it *with* a trailing space
followed directly by the joined list. Counting the no-space form as a
substring also counts every occurrence of the with-space form, so
2 (`_dE`) + 2 (`vdE`) + 2 (`ydE`, matched as a prefix) = 6. All six are
genuine env-context fields; there is no unrelated reuse of this one.

## `Platform: ` — the corrected 14-hit accounting

An earlier draft said "three unrelated templates ... also use the same short
label," implying 3×2=6 unrelated hits plus 6 genuine = 12. The real total is
14. Classifying every occurrence by its surrounding 170 bytes:

```
$ python3 -c "
from pathlib import Path
import os
data = Path(os.environ['CLAUDE_CODE_EXECPATH']).read_bytes()
groups = {'genuine': [], 'doctor': [], 'bug-report': [], 'mcp-transport': [], 'unclassified': []}
start = 0
while True:
    i = data.find(b'Platform: ', start)
    if i < 0: break
    ctx = data[max(0,i-80):i+90]
    if b'Additional working directories' in ctx or b'Is directory a git repo' in ctx or b'Is a git repository' in ctx or b'OS Version' in ctx:
        groups['genuine'].append(i)
    elif b'Environment Info' in ctx or b'Terminal:' in ctx:
        groups['doctor'].append(i)
    elif b'Commit:' in ctx or b'Package manager' in ctx or b'linux-x64' in ctx:
        groups['bug-report'].append(i)
    elif b'Node version' in ctx or b'NODE_OPTIONS' in ctx:
        groups['mcp-transport'].append(i)
    else:
        groups['unclassified'].append(i)
    start = i + 1
for k, v in groups.items(): print(k, len(v), v)
"
genuine 6 [158397984, 158403664, 158412896, 309455579, 309456250, 309457753]
doctor 2 [170869833, 312739426]
bug-report 2 [164926720, 310717526]
mcp-transport 4 [269344450, 269960834, 308569822, 308736692]
```

6 + 2 + 2 + 4 = 14, zero unclassified. `doctor` is a `**Environment Info**`
markdown diagnostics block (`- Platform: ` / `- Terminal: ` / `- Version:`).
`bug-report` is a `Commit: .../Platform: linux-x64/...Package manager:`
template. `mcp-transport` is a `Node version: ..., Platform: linux,
Environment: ${Le({NODE_OPTIONS:...})}` logging line that appears **four**
times, not two — the MCP-transport code that builds it is itself bundled
twice inside the app, independent of (and on top of) the whole-app 2×
duplication described above.

Only 6 of 14 whole-binary hits are this hook's own fields. A rename scoped
to just `ydE`/`_dE`/`vdE` would take the count from 14 to 8 — still nonzero,
so a bare presence check would report "unchanged." A whole-binary **count**
catches it; see `docs/env-context-manifest.json`'s `_comment`.

## `Shell: ` — floor, not region

An earlier draft claimed `Kml()`'s literals "live in a different region of
the binary's string table than the anchor's window, at any window size."
That's false for the probe actually chosen. Measured:

```
$ python3 -c "
from pathlib import Path
import os, re
data = Path(os.environ['CLAUDE_CODE_EXECPATH']).read_bytes()
ANCHOR = b'You have been invoked in the following environment: '
a0 = data.find(ANCHOR)
sp = data.find(b'Shell: PowerShell')
print('Shell: PowerShell offset', sp, 'delta from first anchor', sp - a0)
def lits(after):
    window = data[max(0,a0-3000):a0+after]
    return sorted({m.decode() for m in re.findall(rb'[\x20-\x7e]{12,}', window)})
l1, l2 = set(lits(1500)), set(lits(13000))
print('AFTER=1500 ->', len(l1), 'literals')
print('AFTER=13000 ->', len(l2), 'literals; added:', l2 - l1)
"
Shell: PowerShell offset 158416816 delta from first anchor 12864
AFTER=1500 -> 13 literals
AFTER=13000 -> 15 literals; added: {'knowledge_cutoff', 'Shell: PowerShell'}
```

`Shell: PowerShell` sits +12,864 bytes past the first anchor and +3,824 past
the second — inside the *same* isolated-string-table region as everything
else in `window_literals`, just past the current window's edge. Widening
`AFTER` to 13000 does pull it in (plus `knowledge_cutoff`, an unrelated
object-property-name string from the model-cutoff lookup, at delta +11,680 —
this note measures two new literals at that width, not the "exactly one"
an earlier pass reported; the discrepancy doesn't change the conclusion).

The literal actually used in the common (non-Windows) case, the bare
`` `Shell: ${t}` `` template, compiles to a standalone 7-byte fragment
`"Shell: "`, confirmed isolated by non-printable delimiter bytes on both
sides in the same window already scanned. Being a discrete record in this
string-table format, it can never grow past 7 printable bytes by widening
the window — it is blocked by the `{12,}` regex floor alone, the same
reason `Platform: ` (10 bytes) is blocked, not by distance or region.

Rejected probe: the bare `Shell: ` (7 chars) itself — sub-floor for
`window_literals`, and if used directly for `required_literals` it would be
just as noisy as `Platform: `: 13 whole-binary hits, most of them unrelated
bash-tool/PowerShell-spawn error strings (`Failed to spawn PowerShell: `,
`PowerShell: pre-spawn error (cwd/argv redacted)`, `This tool is for
terminal operations via PowerShell: git, npm, docker...`). Chosen probe:
`Shell: PowerShell` (17 characters — corrected from an earlier "18"), which
occurs exactly 3 times, all confirmed as `Kml()`'s own text: twice in the
readable-source copy (the short-circuit return, and as the prefix of the
longer dual-tool message), once in the isolated-string-table copy. Zero
false positives — none of the unrelated PowerShell strings above match this
exact phrase order.

## `cTm` — the third blind spot: non-ASCII forces UTF-16

`src/claude_config/env_context/render.py`'s `STASH_CAUTION` is cc's `cTm`
(`globals/21.js:13688`) copied verbatim. Neither existing mechanism watches
it: `window_literals`'s window doesn't reach it, and even a naive
"just search the whole binary for this exact string" approach silently
fails, because the string contains an em-dash (U+2014):

```
$ python3 -c "
from pathlib import Path
import os
data = Path(os.environ['CLAUDE_CODE_EXECPATH']).read_bytes()
STASH_CAUTION = ('The git stash stack is shared with the main checkout and all other worktrees, '
    'and other Claude sessions may push or pop it concurrently. Never use bare '
    '\`git stash\` / \`git stash pop\` — you could pop another session\'s changes. ...')
print(data.count(STASH_CAUTION.encode()))
"
0
```

Zero — not because the string is gone, but because its UTF-8 bytes
(including the 3-byte em-dash) don't match how the binary actually stores
it. The **worktree clause** (`_dE`'s other conditional message, also
containing an em-dash) demonstrates why directly. Its ASCII prefix "This is
a git worktree" is *squarely inside* `window_literals`'s current window —
byte 158403248, well within [158400952, 158405452] — yet never appears in
the extracted literals. The raw bytes there are:

```
54 00 68 00 69 00 73 00 20 00 69 00 73 00 20 00 61 00 20 00 67 00 69 00
74 00 20 00 77 00 6f 00 72 00 6b 00 74 00 72 00 65 00 65 00 20 00 14 20
20 00 61 00 6e 00 20 00 69 00 73 00 6f 00 6c ...
```

Every ASCII byte is followed by `00` — UTF-16LE. `14 20` read as one
little-endian code unit is `0x2014`, the em-dash itself. Because a single
non-Latin-1 character forces the *entire* string object into two-byte
representation (not just the character itself), even the plain-ASCII-looking
prefix "This is a git worktree" is null-interleaved and invisible to the
`[\x20-\x7e]{12,}` regex — which can only ever match single bytes between
the nulls, never a run of 12. No window size fixes this; the fix is a
literal that doesn't cross a non-ASCII boundary.

`cTm`'s own ASCII copy exists, at the readable-source region:

```
$ python3 -c "
from pathlib import Path
import os
data = Path(os.environ['CLAUDE_CODE_EXECPATH']).read_bytes()
prefix = 'The git stash stack is shared with the main checkout'
print(data.find(prefix.encode()))
"
309468685
```

Only one ASCII/UTF-8 hit exists (not two, unlike the window_literals
entries above) — the isolated-string-table copy of this same field is
presumably UTF-16, like the worktree clause, and simply invisible to a
plain byte search; this note does not claim to have located it definitively,
only to have ruled out the UTF-8 encoding at that copy. A UTF-16LE-encoded
copy of the same prefix *does* exist, but at a third, unrelated-looking
location (offset 95,064,544, ~63.3M bytes *before* the first anchor) —
recorded here as observed, not explained; the string table's layout
evidently doesn't mirror source order closely enough to predict this.

**Probe chosen:** rather than the reviewer-suggested 52-character prefix
(`"The git stash stack is shared with the main checkout"`), this note uses
a longer, still-unambiguous 182-character prefix that extends up to (but
not across) the em-dash:

```
The git stash stack is shared with the main checkout and all other worktrees,
and other Claude sessions may push or pop it concurrently. Never use bare
`git stash` / `git stash pop` 
```

(trailing space intentional — it's the space before the em-dash in the
source). Both the 52-char and the 182-char prefix land on the exact same
single offset (309468685); the longer one was chosen because it is more
sensitive to a wider span of possible future edits to this message while
staying clear of the encoding hazard demonstrated above. Any prefix that
reaches past the em-dash — up to and including the full 540-character
string — returns a count of 0 for the same reason the worktree clause is
invisible; this was verified, not assumed, before picking the boundary.

## Summary

| literal | whole-binary count | why not in `window_literals` |
| --- | --- | --- |
| `Platform: ` | 14 (6 genuine + 8 unrelated: doctor 2, bug-report 2, mcp-transport 4) | under the `{12,}` floor (10 chars) |
| `Shell: PowerShell` | 3 (all `Kml()`) | stands in for the bare `Shell: ` field, itself under the floor (7 chars) |
| `cTm` probe (182-char prefix) | 1 | ~150M bytes from the anchor, and the field itself is non-ASCII (UTF-16 in at least one copy) |

Reused method note: whole-binary counts here are plain byte-substring
counts (`bytes.count`), which only find ASCII/UTF-8-encoded occurrences.
Anything stored as UTF-16 elsewhere in the binary is invisible to these
counts too — the counts are a lower bound on total occurrences, not a
census. That's fine for drift detection (a genuine rename/removal still
changes the ASCII-visible count), but it's why `cTm`'s baseline is 1 and
not higher despite at least one other (UTF-16) copy being known to exist.
