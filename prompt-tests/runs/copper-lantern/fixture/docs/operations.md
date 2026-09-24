# Operations

## Nightly prune

Run from cron on the build host:

    0 3 * * *  spool prune --days 30

Retention shorter than a day is not expressible, so the job runs nightly and up
to 24 hours of extra retention is accepted.

## Recovering a spool

`index.jsonl` is the only metadata. If it is lost, the artifact files remain but
their recorded times do not, so rebuild it from the file modification times.
