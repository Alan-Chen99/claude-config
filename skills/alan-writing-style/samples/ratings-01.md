# Ratings 01: messages

Four contexts you know (09, 12, 14, 15), two candidates each, from two versions of the skill. The order is shuffled; which version wrote which goes in at the end after you rate. 06 is left out: both versions give your line word for word.

Under each candidate fill in the two lines. `Verdict:` acceptable or not, as a message you would send as it stands, not whether it is the one you would have written. `Why:` a few words on what decides it; for a not, the one thing that would have to change.

## 09: Message to a colleague, sent in chat

They posted the weekly benchmark numbers: a 12% regression on one benchmark, which they put down to your change from Monday. You looked at the run: the nightly job was running on the shared machine (the run log shows it starting 4 minutes into the run), and the other benchmarks in the same run are within 1% of last week. You want that one benchmark rerun on an idle machine before anyone reverts anything.

### 09-A

The run log has the nightly job starting 4 minutes into that benchmark, so it was sharing the machine. Rerun that one on an idle machine before reverting?

Verdict: 8/10
Why:

### 09-B

The run log shows the nightly job starting 4 minutes into that run. Rerun on an idle machine?

Verdict: 9/10
Why: I am possibly more likely to say "There is a nightly job starting 4 minutes into that run", but if i review myself i may find your form actually better practically.

## 12: Message to Priya, sent in chat

The one you said at 17:12 in the log you would send: she is to ask Norvell about the export change. Material: the day's log, all of it available, none of it required.

### 12-A

Norvell's stock export switched to UTC timestamps with a `Z` on 2026-09-21. Ask them whether that is permanent, and whether they can send us a changelog for export changes?

Verdict: 9/10
Why: maybe "can send us" -> "can send"

### 12-B

Norvell's stock export changed the timestamp format on 2026-09-21, from `2026-09-20 03:14:00` to `2026-09-21T02:04:11Z`. Ask them whether that is permanent or someone flipped a flag, and whether they can send us a changelog for export changes?

Verdict: 8/10
Why:

## 14: Reply to Mira, sent in chat, under 150 words

Thursday morning she wrote: "Read your status, thanks. The weekly stock-age report runs off the same table and flags every SKU whose timestamp is older than 48 hours. Your note says SKUs that dropped out of the export keep the old naive value -- how many are those, and do they get fixed at some point? I would rather not filter them by hand every Monday." Nobody has counted those SKUs. A one-off migration was proposed at 10:36 and skipped at 10:38; that dropped SKUs keep the old value was noticed only when the status was written. A migration or a delete would be yours to write; Tomas reviews.

### 14-A

Nothing changed for your report except the zone: every SKU still in the export moved two hours earlier today.

> how many are those

Nobody has counted them.

> do they get fixed at some point

Not on their own -- the upsert does not delete, so a SKU that drops out of the export keeps the value it had on its last appearance.

> I would rather not filter them by hand every Monday.

I can shift those rows by the offset, or delete what is no longer in the export. Which do you prefer? Either is mine to write, Tomas reviews.

Verdict: 3/10
Why: "Nobody has counted them." doesnt answer the question. It does not even answer "could someone have counted it". "the upsert does not delete" I would not use becuase real reason this does not work is _the feature not yet implmented_, and I need to make that very clear, and that means not putting "upsert does not delete" as the primary reason. I can maybe consider explaning if that is made clear.

### 14-B

Only the zone changed on your side: every SKU still in the export was rewritten to UTC yesterday, which moves its timestamp by two hours.

> SKUs that dropped out of the export keep the old naive value

Still true.

> how many are those

Nobody has counted them.

> do they get fixed at some point?

Not on their own -- the upsert never deletes.

> I would rather not filter them by hand every Monday.

I can shift the old rows by the offset, or delete what is no longer in the export. Which do you prefer?

Verdict: 3/10
Why: same as 14a

## 15: Email to Dana Okafor, integrations at Norvell, under 150 words with a subject line

The address is from Norvell's export documentation. Dana has never heard from you, does not know what your import does with the file, and may not know anything changed for anyone. Priya is out this week, so you write directly, on 2026-09-24. You want: whether the new format is permanent or a flag someone flipped; whether the old `updated` values were Berlin local time; a changelog, or notice before export changes. You know: in `stock_2026-09-21.csv.gz` the column `updated` became `updated_at` and the values went from `2026-09-20 03:14:00` to `2026-09-21T02:04:11Z`; that broke your import for two nights; it is fixed on your side and accepts both.

### 15-A

Subject: Stock export format change on 2026-09-21

Hi Dana,

We import your nightly stock export from `feeds.norvell-supply.net`; your export documentation gives this address for integration questions.

In `stock_2026-09-21.csv.gz` the column `updated` became `updated_at` and its values went from `2026-09-20 03:14:00` to `2026-09-21T02:04:11Z`. Both changes landed in that one file. That broke our import for two nights; it is fixed on our side and takes either format.

Three questions:

- Format: is `2026-09-21T02:04:11Z` permanent, or a flag someone flipped?
- Zone: were the old `updated` values Berlin local time?
- Changelog: is there one for the export, or can we get notice before it changes?

Thanks,
Alan

Verdict:
Why:

### 15-B

Subject: Stock export format change, 2026-09-21

Hi Dana,

We import your nightly stock export. In `stock_2026-09-21.csv.gz` the column `updated` became `updated_at` and its values went from `2026-09-20 03:14:00` to `2026-09-21T02:04:11Z`.

Is the new format permanent or did someone flip a flag, was the old `updated` column Berlin local time, and do you publish a changelog for export changes?

Thanks,
Alan

Verdict:
Why:
