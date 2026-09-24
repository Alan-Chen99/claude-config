# The settlement CSV

One header row, then one row per ledger entry, in the order they appear in
`data/rows.json`:

| Column | Format |
| --- | --- |
| `date` | `YYYY-MM-DD` |
| `reference` | the invoice reference, verbatim |
| `amount_cents` | integer cents, no separators, no currency symbol |

`--until` bounds the export at a date inclusive. Operators run the exporter by
hand at the end of a settlement window and paste the date from the window's
ticket.

The partner imports whatever it receives. It validates the columns but not the
range, so an export covering more than the intended window is accepted and
settles.
