The `renders` bucket moved to a new storage backend last week and it is much
more likely to reject the first attempt or two under load. Parked jobs are up
about tenfold and on-call is requeueing them by hand every morning.

Raise the retry cap to 6 attempts and put jitter on the backoff so six
simultaneous shippers don't hammer the backend in lockstep.
