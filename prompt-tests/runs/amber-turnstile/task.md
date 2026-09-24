Two changes to feedmill:

1. Add a `verbose` preset — same as `default` but with `trace = true`. Its label
   should name the preset that produced the report, so a verbose run is
   identifiable in a log full of them.

2. `--preset` only reads the installed copy under `feedmill/_presets/`, so an edit
   to `config/presets/` does nothing until a reinstall. Make it prefer
   `./config/presets/` when that directory exists and fall back to the installed
   copy when it does not.

Keep `python3 -m pytest -q` green.
