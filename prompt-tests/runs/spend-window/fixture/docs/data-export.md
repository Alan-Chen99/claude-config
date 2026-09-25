# Where `expenses.csv` comes from

The bank's reporting portal has no bulk download. `expenses.csv` is assembled by
pasting the portal's paged HTML table into a spreadsheet and exporting that as
CSV, one page at a time, oldest page first.

## Columns

| Column | Meaning |
| --- | --- |
| `id` | The portal's own transaction id. Stable across exports. |
| `date` | Posting date, ISO 8601. Not the transaction date, which the portal does not show. |
| `category` | The portal's category, lowercased. Free text — the portal lets you rename categories, and old rows keep the old name until you re-save them. |
| `amount_cents` | Signed integer. Refunds are negative. |
| `note` | Whatever was typed into the portal's memo field, often empty. |

## Paging

The portal's pager shows 25 rows and repeats the last row of the previous page
as the first row of the next one, so a paste-assembled export carries one
duplicated row per page boundary. The duplicates are byte-identical and share
the `id`.

## Known gaps

- Pending transactions appear with the date they were authorised and get a new
  `id` when they post, so a pending row and its posted row are two rows.
- The portal rounds foreign-currency amounts to the cent before showing them,
  and the rounded value is what lands in `amount_cents`.
- Nothing in the portal exposes the account, so a multi-account report has to be
  assembled from one export per account.
