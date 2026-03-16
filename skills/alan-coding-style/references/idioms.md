## Language-Specific Idioms

### Python

**`match/case` for AST dispatch:**
```python
match node:
    case ast.Name(id=name):
        check(node, name, "name")
    case ast.arg(arg=name):
        check(node, name, "arg")
    case _:
        pass
```

**f-strings exclusively.** No `.format()`, no `%`.

**`pathlib.Path`** for file handling. `Path(__file__).parent` for relative paths.

**`contextlib.contextmanager`** used extensively. Many functions are generators
yielding into a `with` block.

**`yield from`** for delegating to sub-generators.

### Bash

`set -euo pipefail`. Functions for reusable logic. `[[ ]]` conditionals.
`$((arithmetic))`.
