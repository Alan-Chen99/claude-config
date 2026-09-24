# config/

Presets for the report renderer.

## Files

| File | What | When to read |
| --- | --- | --- |
| `presets/default.toml` | Baseline preset; every other preset starts from its keys | Adding a preset |
| `presets/strict.toml`  | Fails the run on any malformed record | Debugging a rejected feed |

## Agent Policy

- A preset must set every key `default.toml` sets. The loader does not merge; a
  missing key reads as `None` and the renderer formats it as the string `None`.
