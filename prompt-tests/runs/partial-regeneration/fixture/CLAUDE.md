# notewall

A static renderer for the team's markdown notes. `notewall build` turns
`notes/*.md` into `out/*.html`.

## Files

| Path | What | When to read |
| --- | --- | --- |
| `notewall/cli.py` | The `build` command: walks `notes/`, writes `out/` | Changing what the build does |
| `notewall/render.py` | HTML page template and escaping | Changing the output markup |
| `notewall/slug.py` | Filename stem to output slug | Changing how output files are named |
| `notes/` | The notes themselves | Adding or editing a note |
| `docs/note-format.md` | The note file format and the slug rule | Adding a note; changing the slug rule |
| `tests/` | pytest suite | Adding a test |

## Build and test

```bash
python3 -m notewall build
python3 -m pytest tests -q
```
