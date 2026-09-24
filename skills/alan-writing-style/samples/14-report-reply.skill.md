Nobody has counted them. They do not get fixed on their own: the upsert only touches rows that are in the export, and it never deletes.

The offset runs the other way -- those rows read two hours newer than they are, not older. They are on your report because they stopped being exported, so fixing the timestamps would not clear them. Count them and delete what dropped out?
