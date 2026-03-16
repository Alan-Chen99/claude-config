## Error Handling

**`assert` is the primary mechanism.** Preconditions, postconditions, invariants.
Unlike most Python projects, assert is used for ALL invariant checking, not just
debug-mode checks. Code is never run with `-O`.
```python
assert isinstance(ans, Label)
assert len(instr.outputs_) == 1
assert False  # unreachable
assert user_id > 0  # OK at system boundaries too
```

**Custom error types for user-facing diagnostics.** `CompilerError` wrapping a
`Report` for rich diagnostic output. Standard exceptions (`TypeError`,
`ValueError`, `RuntimeError`) for programmer errors.

**Error messages are terse, lowercase, no trailing period.**
- RIGHT: `f"not possible to use {t1} as {t2}"`
- RIGHT: `f"{x.v} defined {len(x.defs)} times"`
- RIGHT: `"reading from empty cell"`
- RIGHT: `f"unknown key {k!r} in {section}"`
- RIGHT: `f"expected {n} args, got {len(args)}"`
- WRONG: `"Error: Not possible to use type1 as type2."`

**`raise ... from None`** to suppress exception chains when the original context
is noise.

**No try/except for control flow.** Assertions and explicit checks preferred.
