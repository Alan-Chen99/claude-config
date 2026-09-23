Hi Priya — could you put something to Norvell about the stock export?

Their file changed on 2026-09-21. The timestamp column was renamed from `updated` to `updated_at`, and the values went from `2026-09-20 03:14:00` to `2026-09-21T02:04:11Z` — naive local time to UTC with an explicit Z. Both changes landed in the same file on the same day, which reads like a deliberate release rather than drift on their side. It killed our import two nights running, so /stock was serving Sunday's stock until this afternoon. We've fixed our end and now accept either format.

Two things worth asking them:

- Is the new format permanent, or did someone flip a flag? We'd like to know if it can flip back.
- Can they send us a changelog for export changes? Finding this out from the job dying isn't great, and this is the second time they've moved something under us.

If they're willing to answer a third: was the old `updated` column Bremen local time? We assumed UTC when we stored it, and if it was local we've been about two hours off for as long as we've had the feed. I'd rather have that confirmed by them than inferred by us.
