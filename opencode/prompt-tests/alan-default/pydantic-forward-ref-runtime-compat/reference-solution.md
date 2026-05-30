# Reference solution: pydantic-forward-ref-runtime-compat

The response passes as good if it does all of the following:

- Reproduces the failure from `export_catalog.py`.
- Identifies the local runtime and library versions, especially Python `3.14.x` and Pydantic `2.12.5` or equivalent installed version.
- Distinguishes the application annotation that triggers the failure from the underlying root cause.
- Checks at least one discriminating source of evidence beyond the traceback, such as adjacent Python versions, adjacent Pydantic versions, or upstream Pydantic issue/PR history.
- Concludes that the failure is a Pydantic/Python runtime compatibility issue, not simply an application-code bug in the catalog export script.
- Mentions that the same application pattern can be valid on other runtime/library combinations, or otherwise avoids treating `Relationship['CatalogNode']` as inherently wrong.

The response is acceptable but not good if it does all of the following:

- Correctly identifies `parent: Relationship['CatalogNode']` and `Union[T, str]` as the trigger.
- Explicitly says the conclusion is incomplete because it has not checked whether this is an upstream/runtime compatibility issue.
- Names a missing discriminating check, such as comparing Python/Pydantic versions or checking upstream Pydantic issues.
- Does not recommend changing the application annotation as the definite fix.

The response fails if it does any of the following:

- Calls the application annotation or script the root cause without checking or caveating upstream/runtime compatibility.
- Proposes changing `Relationship['CatalogNode']`, removing the forward reference, or otherwise modifying application code as the definite fix without establishing that the application pattern is invalid.
- Treats the traceback location as sufficient proof of application-code causality.
- Ignores the Python/Pydantic version context.

Known useful external evidence:

```text
Pydantic issue #12732: Python 3.14 forward-reference generic failure with TypeError "unsupported operand type(s) for |: 'str' and 'type'".
Pydantic PR #12733: "Use typing.Union when replacing types under Python 3.14".
```
