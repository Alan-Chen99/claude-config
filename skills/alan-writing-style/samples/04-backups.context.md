Piece: a section for the README of a home-server repo explaining how the home directory is backed up and why that way. Register: doc. Readers run the same server.

Facts:
- Goal: a copy of `/home` that survives a dead disk and a bad `rm`, restorable without the server.
- Chosen: nightly `restic` snapshot to a USB disk plugged into the server, keeping 30 daily and 6 monthly snapshots. Restore was tested once, from a laptop: 40 minutes for 120 GB.
- Cost of the chosen option: the USB disk sits next to the server, so a fire or a theft takes both. Accepted; the photos that matter are also on a phone.
- Rejected: cloud backup (Backblaze B2). About 6 dollars a month for the same data; the first upload of 120 GB took 5 days on this connection and a full restore would take about as long.
- Rejected: `rsync` to the USB disk. Simpler, but one copy: a bad `rm` is mirrored the next night. This is what caused the loss that started this.
- Note: the disk stays plugged in; a `cron` line runs the snapshot at 03:00 and mails on failure. Two failures in 4 months, both the disk not mounting after a power cut.
