# payments-relay runbook

payments-relay forwards settlement records from the ledger service to the
vendor's ingest API. Older alerts fire under the name `ledger-forwarder`; same
service, and the same history is why some module names match nothing here.

## Deploying

`./deploy.sh <env>` builds, pushes, and rolls one pod at a time — about four
minutes in production. Watch with `kubectl rollout status deploy/relay`;
`kubectl rollout pause` is safe, and nothing times out on a paused roll. (This
doc says `deploy/relay`, the incident write-up says `deploy/relay-worker`;
`kubectl get deploy` settles it.)

We use the script rather than the platform team's `shipit` pipeline out of
familiarity, not because `shipit` failed. Moving it is a conversation to have,
not a change to just make.

Migrations are not part of the deploy; run `./migrate.sh` yourself. Adding a
column runs before the restart — new code writes to it on boot and crash-loops
without it. Dropping or renaming runs after the roll, because not-yet-replaced
pods still use the old name and 500 until they are gone.

Try not to deploy on a Friday unless billing is around. Not a rule, but
reconciliation runs Saturday morning and a bad Friday deploy gets found by a
customer instead of by us.

## Configuration

Environment variables, read once at boot. No reload, so a change means a restart.

`WORKERS=4`. Five connections per tenant, one held open permanently by the admin
console, so four is a ceiling rather than a tuning choice. Above it you get
`pool exhausted`, which reaches us as a bare 503.

`RETRY_BACKOFF=2s`. First value anyone typed, never measured against anything.

`BATCH_SIZE=200`, the vendor's documented maximum.

`STRICT_ORDERING=0`. We assume the vendor ingests in the order we send; never
asked, and nothing we run today depends on it.

`LOG_LEVEL=info`. Debug is one line per record and the pipeline drops above
roughly 2000 lines a second, so debug in production can lose the lines you
turned it on to see.

`SHUTDOWN_GRACE=30`. Seconds to wait for in-flight sends before exiting.

## Certificates

The worker presents client certificate `relay-worker-client` from the
`relay-tls` secret, platform CA, **90-day life**. Nothing rotates it and nothing
alerts on expiry; when it expires the worker crash-loops and looks exactly like
a vendor outage — 2026-03-14, 51 minutes. To rotate: reissue from the CA,
update the secret, roll the deployment.

    kubectl get secret relay-tls -o jsonpath='{.data.tls\.crt}' \
      | base64 -d | openssl x509 -noout -enddate

(Assumes the standard `tls.crt` key, unconfirmed; if empty, `-o yaml` shows the
real ones.)

Both rotations on record were manual and 90 days apart (2025-12-14, 2026-03-14).
The incident gives the next expiry as 2026-06-12 with PLAT-2291 open for
automation, and nothing has been written down since — so if that did not land
and someone rotated in June, the current certificate expires around
**2026-09-10**. Rotate ahead of the date, not on it: a rotation on the day is a
roll under time pressure.

## The reconciliation job

Runs 04:00 Saturday, compares what we sent against what the vendor acknowledges,
and opens one ticket per discrepancy into the billing queue. Billing triages
Monday.

No false positives in the eleven weeks since deployment, but it has not run
through a month-end close, when the ledger backdates entries into a period we
have already reported on. Treat a first month-end discrepancy as unproven.

## Environments

Production and your laptop; no staging. The vendor bills per tenant and finance
turned down a second in March, so ask before assuming one can be spun up.

## Access and conventions

Branch naming, commit format, review requirements — `CONTRIBUTING.md` governs.
Section 4, on force-pushing, is the one that catches people out.

Production access is through the bastion. Request in #platform-access; eight
hours at a time, no auto-renew.

Do not run `./redrive.sh` in a loop: in February nine hundred records in a shell
loop got the tenant rate-limited for an hour. Nobody has found the threshold.

## When a page fires

From 2026-03-14, when a client certificate expired and it took 51 minutes to
read the crash line saying so — `INCIDENT-2026-03-14.md`.

**Look at our side first.** Two commands, a minute, no theory required:

    kubectl get pods                                # RESTARTS on the relay pods
    kubectl logs -p deploy/relay-worker | head -20  # "not found"? try deploy/relay

Climbing restarts mean crash-looping: a worker failing to **start**, even when
the symptom you were paged for is that nothing is being **sent**. Use the `-p`,
or you get the current container, still initialising and silent.

**The synthetic check does not tell you whose fault it is.** It fires when a
send fails, identically whether the vendor is down or we cannot reach the
vendor; on 14 March it was the second. Two more non-signals: a restart that
crash-loops again at once failed on its own boot path, short of the vendor; and
the acks panel reads zero whether we are sending or not.

**Understand what you are looking at before you wake anyone up — here, those
two commands and about a minute. If a minute has not resolved it, wake
someone.** A
preference, not a rule and not a team decision: written in after 14 March by
that night's on-call, applying to any page on this service rather than to one
alert, and not written down anywhere before. Disagree freely; that is a
conversation to have. It is not an argument against escalating — that night the
vendor was called and Priya woken before anyone read the crash output, and the
order cost the time, not the escalating.

Nor is escalating fast. The once anyone timed it, the vendor's 24h line took
twelve minutes to reach a human, who asked for a failing request id.

## Troubleshooting

**The worker will not start.** Nine times in ten a missing environment variable,
named in the error; read `kubectl logs -p deploy/relay-worker | head -1` first.
Then an unrun migration — a column error in the first query on boot. Then, on
one occurrence, an expired certificate. Come here even when the worker looks to
you like it started fine: from the dashboards, a crash-looping pod looks exactly
like "nothing is being sent".

**TLS handshake failure.** First line is `FATAL: TLS handshake failed:
certificate expired at <timestamp>`. See Certificates.

**Alerts firing with no traffic.** The synthetic check alerts on its own even
when we are sending nothing. Check our worker before the vendor's status page;
if that page is green, treat it as evidence rather than staleness.

**503s from the vendor.** Nearly always pool exhaustion. Check `WORKERS` first;
it explains this more often than every other cause put together.

**Records stuck in `pending`.** One record over an hour means a lost
acknowledgement, not a lost record; `./redrive.sh <record-id>` is safe, one id
at a time by design. A backlog is different: it drains itself once sending
resumes (14 March: forty minutes, nothing lost), and hand-driving one is how
February happened. `pending` also climbed at the ledger's write rate that night
while the worker was dead, unexplained, so read it as work arriving and not
completing rather than as sends going unacknowledged.

## Appendix: local setup

Python 3.11 or newer, a virtualenv in the repository root,
`pip install -r requirements-dev.txt`, then `pytest -q` (about ninety seconds).
If `pytest` cannot find the package you have not activated the virtualenv, much
the most common setup problem. `docker-compose.yml` runs a local Postgres on
5433 for the tests only.
