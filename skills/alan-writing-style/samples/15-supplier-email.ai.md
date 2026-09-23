Subject: stock export changed format on 2026-09-21

Hi Dana,

We import your nightly stock export from `feeds.norvell-supply.net`; your export documentation gives this address for integration questions.

In `stock_2026-09-21.csv.gz` two things changed at once: the column `updated` became `updated_at`, and its values went from `2026-09-20 03:14:00` to `2026-09-21T02:04:11Z`. That broke our import for two nights. We accept both now, so there is nothing to fix on your side.

Three questions:

- Is the ISO 8601 / `Z` format permanent, or a flag someone switched?
- Were the old `updated` values Berlin local time? We had been reading them as UTC.
- Is there a changelog for the export, or can we get notice before it changes?

Thanks,
Alan
