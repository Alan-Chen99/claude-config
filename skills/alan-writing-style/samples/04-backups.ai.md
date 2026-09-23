## Backups

`/home` is snapshotted nightly with `restic` to a USB disk plugged into the server. Retention is 30 daily and 6 monthly snapshots. A `cron` line runs the snapshot at 03:00 and mails on failure.

The goal is a copy of `/home` that survives two different kinds of failure — a dead disk and a bad `rm` — and that can be restored without the server. The restore has been tested once, from a laptop: 120 GB came back in 40 minutes.

### Why not `rsync`

An `rsync` to the same USB disk is simpler, but it gives you one copy rather than a history, so a bad `rm` is mirrored to the disk the next night. That is the loss that started this.

### Why not cloud backup

Backblaze B2 would cost about 6 dollars a month for the same data. The obstacle is the connection, not the price: the first upload of 120 GB took 5 days, and a full restore would take about as long.

### What this does not cover

The USB disk sits next to the server, so a fire or a theft takes both. That is accepted: the photos that matter are also on a phone.

### Operational notes

The disk stays plugged in. There have been two failures in 4 months, both of them the disk not mounting after a power cut.
