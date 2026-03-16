## Anti-Patterns

Patterns Alan avoids -- flag these during review.

**Over-engineering.** Abstract factories for one implementation. Config classes
for 2 settings. Wrappers that delegate every method. Generic type parameters
used once.

**Verbose naming.** Full words where abbreviation is domain-standard.
- WRONG: `configuration`, `authentication_service`, `transaction_log`
- RIGHT: `cfg`, `auth_svc`, `txn_log`

**`Optional[X]` or `Union[X, Y]` from typing.** Always `X | None`, `X | Y`.

**`Dict`, `List`, `Tuple` from typing.** Always lowercase `dict`, `list`, `tuple`.

**`NamedTuple`.** Use `@dataclass(frozen=True)`.

**Heavy docstrings on every function.** Most functions are self-documenting via
name and types. Docstrings only for important public API.
- WRONG: Docstrings on every function, including trivial helpers
- RIGHT: No docstring when name + types tell the story

**`__all__` exports.** Not used. Module structure communicates public API via
`__init__.py` re-exports with `as` aliases.

**Test classes (`class TestFoo`).** Tests are module-level functions.

**try/except for control flow.** Use assert and explicit checks.

**`slots=True` on dataclasses.** Not used.
