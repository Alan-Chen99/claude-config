Two changes to this store.

1. `ledger list` should take `--since <ISO date>` and print only entries
   recorded at or after that instant.
2. Appending rewrites the whole file today. Change the on-disk shape to one
   JSON object per line, so that adding an entry is a single write at the end
   of the file.

Keep the tests passing.
