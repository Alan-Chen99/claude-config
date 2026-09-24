Nobody has counted them. I'll run it this morning — table minus today's export — and post the number.

They don't get fixed on their own. The upsert never deletes, so a SKU that drops out of the export keeps whatever timestamp it had on its last appearance. I skipped a migration yesterday because every row gets overwritten nightly, which is true for everything still in the export and wrong for exactly this set.

One thing: the offset makes those rows look two hours newer than they are, not older. Your 48h flag catches them because they really are stale, not because of the bug — fixing the timestamps won't stop that.

So either I shift the old rows by the offset, or delete what isn't in the export any more. Either is mine to write and Tomas reviews. Which do you want?
