# templates/

One file per report, named after it. The data team reviews changes here.

- Column aliases are `lower_snake_case` and match what the dashboard expects.
- Order the output; the scheduler diffs consecutive runs and an unordered result
  reads as churn.
- No `SELECT *` — name the columns, so a new warehouse column does not change the
  shape of a report nobody has looked at in a month.
