# Reports

## Adding one

1. Write the SQL under `templates/`, using `$dataset` and `$run_date` rather than
   literal values.
2. Add an entry to `reports.toml` naming the template, the variables and the
   cadence.
3. Add it to the table below.
4. `python3 render.py <name>` and read the query before it goes anywhere.

## Strict rendering

`render.py --strict` fails on any placeholder that is not a declared variable,
which is how a misspelled variable name gets caught before the query runs. The
scheduler does not pass it yet; wiring it in is on the data team's list.

## The reports

| Name | Cadence | What |
| --- | --- | --- |
| `daily_active` | daily 06:00 UTC | Distinct users hitting a profile path |
| `signup_funnel` | weekly Mon 07:00 UTC | Counts per signup step for the trailing week |
