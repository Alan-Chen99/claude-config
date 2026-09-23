Piece: an email to the supplier's integration contact, a person outside the writer's company who knows nothing about the writer's system. Under 150 words, subject line included.

Situation:
- The writer runs the nightly import of the stock export from the supplier, Norvell (Norvell Supply, `feeds.norvell-supply.net`); the day is in `10-12-import-day.log.md`, and the writer also wrote the 11 status. The writer knows both. Nothing after 17:38 on 2026-09-23 is known.
- The reader is Dana Okafor, integrations at Norvell, the address given in Norvell's export documentation. Dana has never heard from the writer, does not know what the writer's import does with the file, and may not know that anything changed for anyone (Norvell's newsletter "API and export improvements" went out last week; the writer deleted it unread).
- Priya, who was to ask Norvell (12), is out this week, so the writer writes directly, on 2026-09-24.
- What the writer wants from Norvell: whether the new format is permanent or a flag someone flipped; whether the old `updated` values were Berlin local time; a changelog, or notice before export changes.
- What the writer knows: in the file of 2026-09-21 (`stock_2026-09-21.csv.gz`) the column `updated` became `updated_at` and its values went from `2026-09-20 03:14:00` to `2026-09-21T02:04:11Z`, both in the same file. That broke the writer's import for two nights; it is fixed on the writer's side and accepts both.
