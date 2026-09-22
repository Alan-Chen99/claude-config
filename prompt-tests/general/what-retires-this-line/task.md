We spent this morning on `sync.sh` failing in cron. It is fixed. Here is what
came out of it, in the order we found it:

- Every failed run in the last month had `BATCH=500`. We dropped it to 200 and
  nothing has failed in the four days since.
- The vendor's API docs say `/v2/ingest` accepts up to 1000 records per call.
- The failures were bare `502`s from their edge with no body. Their status page
  showed nothing for any of the windows.
- Raj on their support call said our account is on the shared tier, that there
  is a 30-second gateway timeout in front of the endpoint, and that 500 records
  "usually" runs longer than that for accounts on that tier.
- We never reproduced at 500 after that call. We set 200 and moved on.

`sync.sh` has `BATCH=200` in it now and no comment. Put whatever a future agent
needs into the repo so none of this gets re-litigated.
