# Data model

Field-by-field reference for the records `billing/` reads and writes. Open this
when you are adding a field or trying to work out what one means.

## `Invoice`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `str` | ULID, not a UUID. Sorts by creation time. |
| `customer` | `str` | Account slug, lowercase. |
| `lines` | `list[Line]` | At least one; an empty invoice is rejected at assembly. |
| `total` | `Money` | Sum of the lines. Recomputed on every write, never stored from the caller. |
| `issued_at` | `datetime` | UTC, tz-aware. Naive datetimes raise. |

## `Line`

| Field | Type | Notes |
| --- | --- | --- |
| `sku` | `str` | Free-form; nothing validates it. |
| `qty` | `int` | May be negative — that is how credits are represented. |
| `unit` | `Money` | Price per unit before tax. |

## `Money`

Wraps an amount and a three-letter currency code. Arithmetic between two
different currencies raises `CurrencyMismatch`. Comparison does not — `<` on
mixed currencies compares the amounts and says nothing about the codes.
