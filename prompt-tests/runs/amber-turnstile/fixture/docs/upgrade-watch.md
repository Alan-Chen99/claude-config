# upgrade-watch

What a dependency or interpreter bump can break here. A green test run still leaves
all of this unchecked: each row names something that fails quietly.

| Where | What it depends on | What a change does |
| --- | --- | --- |
| `feedmill/cli.py` (`tomllib`) | stdlib `tomllib`, 3.11+ | A 3.10 interpreter has no `tomllib`; the import fails at startup, which is loud. |
| `feedmill/cli.py` (`--preset`) | `argparse` prefix matching | `argparse` accepts `--pre` as `--preset` today. Turning off prefix matching turns a working invocation into "unrecognized arguments". |
