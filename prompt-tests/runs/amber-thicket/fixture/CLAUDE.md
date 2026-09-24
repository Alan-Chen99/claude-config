# warehouse-reports

Scheduled SQL reports. `render.py` fills a template's variables and prints the
query; the scheduler pipes that into the warehouse CLI. Nothing here talks to the
warehouse directly.

## Layout

| Path | What |
| --- | --- |
| `render.py` | Template renderer and CLI |
| `reports.toml` | One entry per scheduled report: template, variables, cadence |
| `templates/` | The SQL. Reviewed by the data team — a change here needs a reason in the commit message |
| `docs/reports.md` | How to add and run a report |
| `tests/` | `pytest` |

## Conventions

- Report names are `lower_snake_case` and match their `reports.toml` key.
- A report that reads a dated partition takes `run_date`, never a literal date.
- Every report entry names a `cadence`, even a report nothing schedules yet — the
  scheduler's inventory check reads that field and skips entries without it.
- Keep `docs/reports.md` in step with `reports.toml`: the on-call runbook links to
  it and nothing else lists the reports.

## Running

```bash
python3 render.py <report-name>
python3 -m pytest -q
```
