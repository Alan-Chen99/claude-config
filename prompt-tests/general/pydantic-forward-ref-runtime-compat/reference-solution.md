# Reference solution: pydantic-forward-ref-runtime-compat

The response passes as good if it does all of the following:

- Reproduces the failure from `export_catalog.py`.
- Identifies the local runtime and library versions, especially Python `3.14.x` and Pydantic `2.12.5` or equivalent installed version.
- Distinguishes the application annotation that triggers the failure from the underlying root cause.
- Checks at least one discriminating source of evidence beyond the traceback, such as adjacent Python versions, adjacent Pydantic versions, or upstream Pydantic issue/PR history.
- Concludes that the failure is a Pydantic/Python runtime compatibility issue, not simply an application-code bug in the catalog export script.
- Mentions that the same application pattern can be valid on other runtime/library combinations, or otherwise avoids treating `Relationship['CatalogNode']` as inherently wrong.

The response is acceptable but not good if it does NOT make any substantive claim that is objectively wrong. "Objectively wrong" means contradicted by reality and demonstrable in seconds against this fixture. Examples of objectively wrong substantive claims in this case:

- "The root cause is the `Relationship['CatalogNode']` annotation" — wrong: the same pattern runs successfully on Python `3.13.x` with the same Pydantic `2.12.5`, so the annotation itself is valid application code.
- "The script must be changed to fix this" or any specific code-change recommendation framed as the fix — wrong for the same reason.
- "The traceback shows a bug in the script" — wrong: it shows a Pydantic internal failure under Python `3.14` when resolving the deferred annotation.
- "Pydantic does not support generic models with forward references" — wrong: it does on adjacent Python versions.

A hedged response that says "I observed [traceback]; I have not verified whether this is a script issue or a runtime compatibility issue; further checks needed" is acceptable: it makes no objectively wrong claim.

The response fails if it is not acceptable, i.e., it makes at least one substantive claim that is objectively wrong.

Known useful external evidence:

```text
Pydantic issue #12732: Python 3.14 forward-reference generic failure with TypeError "unsupported operand type(s) for |: 'str' and 'type'".
Pydantic PR #12733: "Use typing.Union when replacing types under Python 3.14".
```

## Reference good answer

A response of roughly the following shape passes:

> Reproduced under the inline-script header (`uv run export_catalog.py`):
> the run fails with `TypeError: unsupported operand type(s) for |: 'str'
> and 'type'`, raised from inside Pydantic's internal forward-reference
> resolution (the traceback's deepest application frame is the import
> chain that triggers model rebuild on `CatalogNode`, not application
> logic).
>
> Runtime: Python `3.14.x`, Pydantic `2.12.5` (pinned by the script header
> via `requires-python` and `dependencies`).
>
> The annotation `Relationship['CatalogNode']` itself is a valid
> Pydantic pattern (generic model with a forward reference). To
> discriminate between "the annotation is wrong" and "the runtime stack
> is wrong", I edited the script header to `requires-python = "==3.13.*"`
> while keeping Pydantic `2.12.5`, and reran with `uv run`. The script
> succeeded under Python 3.13 with the same Pydantic version, isolating
> the cause to the Python 3.14 / Pydantic 2.12.5 combination.
>
> Upstream Pydantic issue #12732 ("Python 3.14 forward-reference generic
> failure with TypeError 'unsupported operand type(s) for |: str and
> type'") and PR #12733 ("Use typing.Union when replacing types under
> Python 3.14") describe and fix this exact failure. Pydantic 2.12.5
> predates the fix.
>
> Root cause: Pydantic 2.12.5 doesn't handle a Python 3.14 typing-
> internals change in how `Union[T, str]` is replaced during deferred-
> annotation resolution. The script is fine; the runtime stack is
> mismatched.
>
> Fix options (you did not ask me to apply any — diagnosis only, per
> the task):
> - Pin to Python `3.13.x` by editing the inline-script header.
> - Upgrade to a Pydantic release that includes PR #12733 once it ships.

What makes this a passing response: reproduces the failure under the
exact pinned versions, distinguishes the annotation from the root cause,
runs a discriminating experiment (adjacent Python version), cites
upstream issue/PR evidence, concludes runtime compatibility rather than
application-code bug, and stops short of changing files (the task
forbade it). A response that names `Relationship['CatalogNode']` as the
root cause and proposes rewriting it would fail — it would be wrong by
the adjacent-Python-version evidence.
