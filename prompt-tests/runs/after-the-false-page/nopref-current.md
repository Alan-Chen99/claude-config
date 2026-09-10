# payments-relay runbook

payments-relay forwards settlement records from the ledger service to the
vendor's ingest API. It started life in 2023 as a cron script, moved to a
long-running worker in early 2024, and picked up its current name when the
billing team split off from platform. A few of the older alerts still fire under
the name `ledger-forwarder`; that is this same service. None of that history
changes how you operate it today, but it does explain why several module names
in the source do not match anything in this document, and why the oldest
dashboards have two entries for what is one thing.

Two deployment names appear below: `deploy/relay` under Deploying, and
`deploy/relay-worker` under Troubleshooting. Each is copied from somewhere it
was observed working, at different times. Nobody has confirmed whether they are
one object or two. Run `kubectl get deploy` and use what you see there rather
than trusting either.

## Deploying

Deploys go out through `./deploy.sh <env>`. The script builds the image, pushes
it, and rolls the deployment one pod at a time. A roll takes about four minutes
in production. You can watch it with `kubectl rollout status deploy/relay`, and
if you need to stop it mid-roll, `kubectl rollout pause` works and is safe — the
paused state is a normal state and nothing times out on it.

We deploy through that script rather than through the platform team's `shipit`
pipeline. Both were run in parallel through most of 2024 and both worked; we
stayed on the script because the team already knew it, not because `shipit` ever
failed us. If you want to move it, that is a conversation to have, not a change
to just make.

Migrations are not part of the deploy. You run `./migrate.sh` yourself, and the
order depends on what the migration does. A migration that adds a column runs
before the restart, because the new code writes to that column on boot and will
crash-loop without it. A migration that drops or renames a column runs after the
rollout finishes, because in-flight requests on the not-yet-replaced pods still
reference the old name and will 500 for as long as the roll takes.

Try not to deploy on a Friday unless someone from billing is around. Nobody
enforces this and it is not a rule, but the reconciliation job runs Saturday
morning, and a bad Friday deploy tends to get discovered by a customer instead
of by us.

## Configuration

Everything the worker reads at boot is an environment variable, with one
exception: the client certificate, which is mounted from a secret and has its
own section below. Environment variables are read once at boot and there is no
reload mechanism, so changing any of them means a restart.

`WORKERS=4`. The vendor's connection pool allows five concurrent connections per
tenant and the admin console holds one of them open permanently, so four is the
ceiling rather than a tuning choice. Going above it produces `pool exhausted` on
the vendor side, which reaches us as an undifferentiated 503.

`RETRY_BACKOFF=2s`. This was the first value anyone typed and it has never been
measured against anything. If retry behaviour ever needs work, this is a fine
place to start.

`BATCH_SIZE=200`, which is the vendor's documented maximum.

`STRICT_ORDERING=0`. We think the vendor ingests a batch in the order we send
it — that is what their acknowledgements have always looked like — but we have
never put the question to them and they have never documented it. Nothing we run
today depends on the answer.

`LOG_LEVEL=info`. Debug is extremely loud — one line per record — and the log
pipeline starts dropping above roughly two thousand lines a second, so turning
on debug in production can lose the exact lines you turned it on to see.

`SHUTDOWN_GRACE=30`. Seconds the worker waits for in-flight sends before exiting.

## Certificates

The worker authenticates to the vendor with a client certificate,
`relay-worker-client`, issued by the platform CA and mounted into the pod from
the `relay-tls` secret. It is not an environment variable and it is not baked
into the image, which is why it does not appear in the list above and why it is
easy to forget the worker has a credential at all.

The certificate has a 90-day life. Nothing rotates it, nothing monitors its
expiry, and no alert fires as it approaches. Every rotation so far has been a
person deciding to do it: the 2025-12-14 rotation was done by hand, and the
2026-03-14 one was done by hand at 03:55 after the certificate had already
expired and taken production down for 54 minutes.

**The next expiry is 2026-06-12.** That date is the only warning that exists,
and it lives in this document rather than in any system. PLAT-2291 tracks
automated rotation with an expiry alert at 14 days; until it lands, this
paragraph is the alerting.

The reissue procedure is undocumented. The 2026-03-14 rotation was done by
Marcus, from the platform CA, and the write-up of that night does not record the
commands or what access they needed. Right now the procedure exists in one
person's head. Somebody should get it written down here before 2026-06-12,
rather than reconstructing it at three in the morning for a second time.

## The reconciliation job

It runs at 04:00 on Saturday, compares what we sent against what the vendor
acknowledges receiving, and opens one ticket per discrepancy. The tickets land
in the billing queue, not ours, and someone from billing triages them on Monday
morning.

It has not produced a false positive since it was deployed eleven weeks ago. It
has also not yet run through a month-end close, which is when the ledger service
backdates entries into a period we have already reported on, so treat a
discrepancy raised at the first month-end as unproven rather than as real.

A clean run does not by itself mean an outage did no damage. On 2026-03-14 the
job ran at 04:00 while a backlog from that night's stall was still draining, and
came back clean; the backlog did not finish clearing until 04:40. Nobody has
worked out whether the job would have caught a genuine loss in that window or
whether records still queued on our side are simply invisible to it. If you have
had an incident overnight on a Friday, a clean Saturday reconciliation is not
the confirmation you want it to be.

## Environments

There is production, and there is your laptop. There is no staging.

This is not an oversight that someone is getting around to fixing. The vendor
bills per tenant, and finance turned down a request for a second tenant in
March; ask them before assuming one can be spun up.

## Access and conventions

Repository conventions — branch naming, commit format, review requirements —
all live in `CONTRIBUTING.md`, and that file is what governs. The section that
catches people out is section 4, on force-pushing, so read it before you rebase
anything that has already been pushed.

Production access is through the bastion. Request it in #platform-access; it is
granted for eight hours at a time and does not auto-renew.

Do not run `./redrive.sh` in a loop. That went in after one incident in
February, when someone redrove about nine hundred records in a shell loop and
the vendor rate-limited the whole tenant for an hour; it has not come up since,
and nobody has worked out where the actual threshold is.

## Troubleshooting

The entries below are titled by cause. Several unrelated faults present with the
same symptom — settlements have stopped — so the entry that matches the words on
your pager is often not the entry that matches your fault.

If sends are at zero, confirm the worker is up **and staying up** before you
look at anything outside the cluster. `kubectl get pods`, and read the RESTARTS
column rather than READY: a crash-looping pod cycles through Running and looks
healthy at a glance. This check costs ten seconds and it is where the last
outage was. On 2026-03-14 it was skipped, and the cause was found 51 minutes
later on the first line of the crash output.

**503s from the vendor.** Nearly always pool exhaustion. Check `WORKERS` first
before you go looking at anything else, because it explains this symptom more
often than every other cause put together.

**Records stuck in `pending`.** The worker marks a record `pending` when it
hands it to the vendor and `sent` when the vendor acknowledges. A single record
that sits in `pending` for more than an hour while everything around it moves
means an acknowledgement was lost, not that the record was lost. Re-driving it
is safe. There is a script for this, `./redrive.sh <record-id>`, and it takes
one id at a time by design.

That reading holds for one stuck record. It does not hold for a rising queue.
`pending` climbing in bulk means the sending side has stopped, not that
acknowledgements are being lost, and redriving is the wrong response to it —
there is nothing wrong with the records. On 2026-03-14 `pending` climbed at
roughly the ledger's write rate for 54 minutes while the worker was crash-
looping and nothing was being sent at all.

Once the worker is healthy again the backlog drains without intervention. The
one time this has been measured, a 54-minute stall took 42 minutes to clear.
Resist redriving to hurry it along; see the February rate-limiting incident
under Access and conventions.

Unresolved: the mechanism in the first paragraph says `pending` is set at
handoff, which does not explain `pending` climbing while nothing is being handed
over. Either the state is set earlier than described, or the Grafana panel
named `pending` counts something other than the database state of the same name.
Nobody has checked which. Until somebody does, treat `pending` as a symptom to
corroborate rather than a fact to reason from.

**The worker will not start, or is crash-looping.** Nine times out of ten this
is a missing environment variable, and the error message names it. Read the
first line of the crash output before doing anything else. The second most
common cause is a migration that has not been run, which looks like a column
error in the first query the worker makes on boot. The third is an expired
client certificate, below.

Get the crash output with `-p`:

    kubectl logs -p deploy/relay-worker | head -1

Without `-p` you get the current container, which on a crash-looping pod is
usually still initialising and tells you nothing. That flag is the difference
between a four-minute incident and a fifty-one-minute one.

Two things about this entry are worth knowing before you need it. First, a
crash-looping worker does not present as "the worker will not start" — from
outside the cluster it presents as "we have stopped sending", because the pod
exists, cycles, and never gets far enough to do any work. If nothing is moving,
this is still the entry you want. Second, a restart that comes straight back
into a crash loop is evidence the fault is ours, not the vendor's: the pod is
failing before it does any work, so nothing external has had the chance to be
involved yet.

**`TLS handshake failed: certificate expired`.** The client certificate has
expired; see Certificates above. The worker crash-loops from the moment of
expiry, sends drop to zero, `pending` climbs at the ledger's write rate, and the
synthetic check pages about three minutes later.

Everything outside the worker looks healthy while this is happening, and that is
the trap: the vendor is up, their status page is green and correct, DNS
resolves, their IP is reachable from a pod, and egress is unchanged. The first
line of the previous container's log names the certificate and the exact expiry
timestamp. Fix is to reissue from the platform CA and roll it out.

Expiry is not a random event. The date is known months ahead and it is written
down under Certificates. The next one is 2026-06-12.

**Alerts firing with no traffic.** The synthetic check runs every minute against
a fixed record id, independently of whether we are sending anything, so it will
alert even when the queue is empty.

What it cannot do is tell you whose fault it is. The check fails identically
whether the vendor is down or we cannot reach the vendor, and "we cannot reach
the vendor" covers every fault on our own side of the connection: a dead worker,
an expired certificate, blocked egress. Read this alert as "the path to the
vendor is broken somewhere along its length", and start at our end, because our
end is cheaper to check and is where the last one was.

Check the vendor status page, and if it is green, believe it until you have
evidence from our side that contradicts it. On 2026-03-14 the page was green and
accurate, was dismissed as stale on the grounds that nobody updates a status
page at 3am on a Saturday, and every observation after that was read as support
for an outage that was not happening.

Be careful what your reachability checks actually prove. A curl from your laptop
gets a 200 from the vendor's edge without touching ingest, and a reachability
check from a pod exercises the network path without exercising the client
certificate. On 2026-03-14 both came back healthy while the worker could not
complete a TLS handshake. If you want to know whether the worker can talk to the
vendor, look at the worker.

**Reading the `acks` panel.** Grafana's acks panel reads zero in two unrelated
situations: we are sending and getting nothing back, and we are not sending at
all. The panel does not distinguish them, and the second is the more common
cause. Corroborate against the sends panel and the pod restart count before you
conclude anything from acks on its own.

## Escalating to the vendor

Escalating is not the fast option and it is not free. Their 24-hour line has
been timed once, on 2026-03-14: twelve minutes of automated menu and hold before
a human. Those twelve minutes cost you your own attention as well as theirs, at
the point in an incident when you can least spare it. If you are escalating
because you have run out of ideas rather than because you have a diagnosis, do
the cheap local checks while you wait rather than instead of waiting.

Their on-call will ask for a failing request id. Have one before you call. If
you cannot produce one, treat that as a finding rather than an inconvenience:
no failing request usually means no request.

The most useful thing their on-call can tell you is not whether they are having
problems, but whether they are seeing ingest *attempts* from our tenant. No
errors and no attempts means we stopped sending and the fault is ours. On
2026-03-14 that answer was given at 03:31, twenty minutes before it was acted
on. If you get it, believe it and turn round.

## Appendix: local setup

You need Python 3.11 or newer. On macOS, `brew install python@3.11`; on Debian
and Ubuntu, `apt install python3.11 python3.11-venv`. Then make a virtualenv in
the repository root with `python3.11 -m venv .venv`, activate it with
`source .venv/bin/activate`, and install the dependencies with
`pip install -r requirements-dev.txt`. The test suite is `pytest -q` and takes
about ninety seconds. If `pytest` cannot find the package, you have almost
certainly forgotten to activate the virtualenv, which is the single most common
setup problem and worth checking before anything else.

There is a `docker-compose.yml` in the repository root that brings up a local
Postgres on port 5433. It is only used by the tests; nothing in normal operation
touches it.
