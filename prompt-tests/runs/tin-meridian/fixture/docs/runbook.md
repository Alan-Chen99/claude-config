# Runbook

## Nightly snapshot

Run from cron on the build host:

    0 3 * * *  warden snapshot --name nightly /srv/build

## Restoring a snapshot

1. Stop the writer.
2. Copy the snapshot file back into the snapshot directory.
3. Run `warden verify` and confirm it reports `ok`.
4. Start the writer.

## When verify fails

`warden verify` fails only when a snapshot's bytes have changed since it was
written. Compare the snapshot against the tree it came from before assuming the
store is at fault.
