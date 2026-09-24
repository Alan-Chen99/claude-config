# Store layout

A store is one file. It holds a JSON array, and each element is an entry:

```json
{"at": "2026-03-01T17:40:00Z", "text": "paid the invoice"}
```

`at` is UTC ISO 8601. `text` is free-form and may contain newlines.

Reading loads the whole array; writing rewrites the whole file from the
in-memory list.

## Design Decisions

**A JSON array rather than one object per line.** Ordinary JSON tools read an
array without a wrapper, which is what makes the `jq` line in `README.md` work,
and a store is expected to stay small enough that rewriting it is cheap.

**`text` is not escaped or trimmed.** Entries come from a human at a shell
prompt; mangling what they typed is worse than a store that needs quoting when
it is printed.
