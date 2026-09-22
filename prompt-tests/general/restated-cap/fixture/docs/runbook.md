# shipper runbook

## A job is parked

Parked jobs are in `/var/spool/shipper/parked/`. A job lands there after the
uploader has tried three times — immediately, then after 1s, then after 2s — and
failed every time. Total elapsed before parking is therefore a little over 3
seconds plus three upload timeouts, so about 93 seconds at the default timeout.

Look at `shipper.log` for the last attempt's error before requeueing. Requeue by
moving the directory back to the spool root:

    mv /var/spool/shipper/parked/<job-id> /var/spool/shipper/

## The spool is filling up

Uploads are slower than renders. Check the bucket's ingest metrics first. If the
backend is healthy, the usual cause is a worker writing oversized output.

## The uploader is pegging a core

`tar` is single-threaded here and that is on purpose: a render box runs eight
workers and the uploader must not compete with them for CPU.
