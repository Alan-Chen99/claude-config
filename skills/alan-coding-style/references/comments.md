## Comment Style

**No module docstrings.** This is deliberate -- modules are navigated by
structure, not docstrings.

**Class docstrings: brief and informal when present.** Many classes have none.
When present, they describe the what and invariants. Typos are acceptable.
```python
class Var(Generic[T_co], ByIdMixin):
    """
    internal varaible used by the compiler.
    unlike Variable, equality and comparison is by variable id.

    A Var must always be assigned in one place. A MVar may be assigned any number of times.
    """
```

**Function docstrings: rare.** Only for important public API functions.
Brief when present.

**Inline comments: frequent, terse, informal.** Mix of why and what.
TODO/FIXME left in freely.
```python
# note: use ordered set since code uses len() to check #
# previously instrs emiitting label are pushed twice
# so we change everything to OrderSet to prevent future bugs
```

**`#:` for field documentation** (Sphinx-style):
```python
#: internal check. user invalid uses should be caught when the Var is found not in _CUR_SCOPE
#: TODO: not used rn
live: Cell[bool]
```

**`pyright: ignore[...]`** comments are specific, not blanket ignores.

**Section dividers** with `####...####` for logical grouping within files.
