## Backups

- Goal: a copy of `/home` that survives a dead disk and a bad `rm`, restorable without the server.
- Chosen: nightly `restic` snapshot to a USB disk plugged into the server, keeping 30 daily and 6 monthly snapshots. Restore tested once, from a laptop: 120 GB in 40 minutes.
- Cost: the disk sits next to the server, so a fire or a theft takes both. Accepted -- the photos that matter are also on a phone.
- Rejected, `rsync` to the same disk: simpler, but one copy, so a bad `rm` is mirrored the next night. That is what caused the loss that started this.
- Rejected, cloud backup (Backblaze B2): about 6 dollars a month for the same data, but the first upload of 120 GB took 5 days on this connection and a full restore would take about as long.
- Operation: the disk stays plugged in, and a `cron` line runs the snapshot at 03:00 and mails on failure. Two failures in 4 months, both the disk not mounting after a power cut.
