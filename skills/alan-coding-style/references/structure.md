## Code Structure

### Module Layout

1. `from __future__ import annotations` (when present)
2. Imports (formatter-managed)
3. Project-specific initialization (if needed)
4. Constants and module-level state
5. Classes and functions, separated by `####...####` section dividers
6. No `__all__` (not used)

Internal modules use leading underscore: `_core.py`, `_api.py`, `_utils.py`,
`_transforms/`. Public modules don't: `config.py`, `functions.py`, `devices.py`.

### Section Separators

Use `################################################################################` lines
to divide logical sections within large files. Core modules may reach 1000+
lines; most modules are 200-800 lines. Don't split just to reduce line count —
split at public API boundaries.

### `__init__.py` Conventions

Re-export facade with explicit `as` aliases: `from ._api import Foo as Foo`.
The `from X import Y as Y` pattern makes pyright/autoflake happy about re-exports.
Category comments group related re-exports.

### Imports

Formatter-managed ordering. Style rules:

- Never wildcard imports in source (OK in tests: `from sicc import *`).
- One import per line (enforced by formatter).
- `from rich import print as print  # autoflake: skip` overrides builtin print
  in many modules.
