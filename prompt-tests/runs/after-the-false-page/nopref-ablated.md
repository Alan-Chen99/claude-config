# payments-relay runbook

payments-relay forwards settlement records from the ledger service to the
vendor's ingest API. It started life in 2023 as a cron script, moved to a
long-running worker in early 2024, and picked up its current name when the
billing team split off from platform. A few of the older alerts still fire under
the name `ledger-forwarder`; that is this same service. None of that history
changes how you operate it today, but it does explain why several module names
in the source do not match anything in this document, and why the oldest
dashboards have two entries for what is one thing.

The same mismatch reaches `kubectl`. This document has long used
`deploy/relay`, and the 14 March 2026 incident used `deploy/relay-worker` —
that second form is the one attested to have worked. Nobody has confirmed which
is current, or whether both resolve. Run `kubectl get deploy` once at the start
of an incident rather than discovering the answer at 3am.

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

Everything is environment variables, read once at boot. There is no reload
mechanism, so changing any of these means a restart.

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

## The client certificate

The worker authenticates to the vendor with a client certificate,
`relay-worker-client`, issued by the platform CA and mounted from the
`relay-tls` secret. It has a 90-day life.

Nothing monitors its expiry and nothing rotates it. Both rotations to date have
been done by hand. The 2025-12-14 one appears in git blame on the secret
manifest as Marcus, commit message "cert rotation (again)"; nothing records what
prompted it. The 2026-03-14 one was prompted by the outage the expiry had
already caused, fifty-one minutes in. Git blame on that manifest is the only
rotation history there is.

When it expires the worker crash-loops from that second, and the first line of
the crash output names the cause exactly:

```
FATAL: TLS handshake failed: certificate expired at 2026-03-14T03:04:11Z
```

From the dashboards this is indistinguishable from a vendor outage — sends at
zero, acks at zero, `pending` climbing at the ledger's write rate, and the
synthetic check paging. See "Before you branch" under Troubleshooting. That
ambiguity is a large part of why the 14 March outage ran for fifty-one minutes
on a fault whose cause was printed on the first line of the crash output.

Read the current expiry before you assume you have time:

```
kubectl get secret relay-tls -o jsonpath='{.data.tls\.crt}' \
  | base64 -d | openssl x509 -noout -enddate
```

That assumes the standard `tls.crt` key. If it comes back empty,
`kubectl describe secret relay-tls` lists what keys are actually in there. Note
that it reads the secret, not what the running pods have loaded — after a
reissue and before a rollout, those two disagree.

Known dates: issued 2025-12-14, expired 2026-03-14 at 03:04:11. The 14 March
write-up recorded the following expiry as 2026-06-12. That date is in the past,
so confirm the current expiry with the command above before relying on anything
in this section. Worth knowing what the arithmetic gives if the answer is bad
news: the one rotation we can date precisely happened on the expiry day itself,
because an outage forced it, and a 90-day certificate issued on 2026-06-12 comes
due on 2026-09-10.

An expiry forces a rollout on whatever day it falls on. That overrides the
Friday guidance under Deploying — a certificate that has expired is not
something you defer to Monday.

PLAT-2291 tracks automated rotation with expiry alerting at 14 days. Until it
lands, the date you read out of that secret is the only warning you get.

Reissuing is two steps, not one: a new certificate from the platform CA into the
`relay-tls` secret, and then a rollout. The worker reads the mounted certificate
at boot and there is no reload, exactly as with the environment variables above,
so replacing the secret on its own changes nothing that is already running. On
14 March the rollout that would have picked up a new certificate had never run,
because nobody knew one was needed; that, not the expiry by itself, is what kept
the workers down.

Beyond those two steps the procedure is not written down anywhere, including
here. Marcus has done it both times, and on 14 March reissue and rollout
together took about four minutes from starting to sends resuming. If you are
holding the pager and he is not reachable, that is the gap you will be standing
in.

Once the new certificate is in and the pods are up, the backlog drains on its
own. On 14 March everything from the fifty-four-minute window settled without
anyone redriving anything, about forty minutes after sends resumed. That is one
observation rather than a guarantee, but do not reach for `./redrive.sh` before
giving it that long.

## The reconciliation job

It runs at 04:00 on Saturday, compares what we sent against what the vendor
acknowledges receiving, and opens one ticket per discrepancy. The tickets land
in the billing queue, not ours, and someone from billing triages them on Monday
morning.

It has not produced a false positive since it was deployed eleven weeks ago. It
has also not yet run through a month-end close, which is when the ledger service
backdates entries into a period we have already reported on, so treat a
discrepancy raised at the first month-end as unproven rather than as real.

One result nobody has explained: on Saturday 14 March the job ran at 04:00 with
roughly forty minutes of that night's backlog still draining, and came back
clean. That may be because it has a lookback window that excluded the in-flight
records, or because it only compares settled state, or because the backlog was
genuinely accounted for. Nobody has checked which. Until somebody does, do not
read a clean Saturday result as confirmation that the previous night's backlog
was fully reconciled.

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

**Before you branch.** Several unrelated faults present identically on the
dashboards: sends at zero, acks at zero, `pending` climbing at the ledger's
write rate, synthetic check paging. A vendor outage looks like this. So does an
expired client certificate, a crash-looping worker, a DNS failure, and an egress
policy change. The dashboards cannot separate them, and Grafana's "acks" panel
in particular reads zero both when we are sending and getting nothing back and
when we are not sending at all — two very different situations drawn as the same
flat line.

So before you match your symptom to an entry below, settle one question: is the
worker running? "Sends are at zero" is not an answer to it.

```
kubectl get pods                    # RESTARTS climbing = crash-looping
kubectl logs -p deploy/relay-worker | head -1
```

The `-p` is not optional. Without it you get the *current* container, which on a
crash-looping pod is usually still initialising and has said nothing yet. That
empty output reads as "no error here" and it is wrong.

This costs seconds, and it separates "we stopped sending" from "they stopped
accepting", which is the largest fork in this document. Everything below is
easier once you have answered it.

**503s from the vendor.** Nearly always pool exhaustion. Check `WORKERS` first
before you go looking at anything else, because it explains this symptom more
often than every other cause put together.

**Records stuck in `pending`.** The worker marks a record `pending` when it
hands it to the vendor and `sent` when the vendor acknowledges. A record that
sits in `pending` for more than an hour means an acknowledgement was lost, not
that the record was lost. Re-driving it is safe. There is a script for this,
`./redrive.sh <record-id>`, and it takes one id at a time by design.

Note that `pending` climbing across the board is a different thing from
individual records stuck in `pending`. The first means we have stopped sending;
start with "Before you branch".

**The worker will not start.** Nine times out of ten this is a missing
environment variable, and the error message names it. Read the first line of the
crash output before doing anything else — `kubectl logs -p deploy/relay-worker |
head -1`. The second most common cause is a migration that has not been run,
which looks like a column error in the first query the worker makes on boot. The
third, seen once, on 14 March 2026, is an expired client certificate; see "The
client certificate" above.

This entry is easy to skip past, because from outside a crash-looping worker
does not look like a worker that will not start — it looks like sending is
broken. It is the same thing. A pod that is crash-looping is failing to start,
several times a minute. If sends are at zero this entry applies to you even if
you are confident the worker came up fine.

One inference to get right: if you restart the deployment and it comes back and
immediately crash-loops again, that is not evidence the problem is external. It
is the opposite. The pod failed on its own boot, before it got far enough to
depend on anything outside the cluster. Read the crash output.

**Alerts firing with no traffic.** The synthetic check runs every minute against
a fixed record id. It fires when a send does not succeed — and it cannot tell
*the vendor is down* from *we cannot reach the vendor*. Those fail identically
from where the check stands. The second covers an expired client certificate, a
crash-looping worker, DNS, and egress policy changes, and on the one occasion we
have data for it was the second.

So a firing check is not evidence the vendor is down. Check the vendor status
page before you page anyone, and treat what it says as information: if the page
is green, that is a reason to start looking at our side, not a reason to decide
the page is stale. On 14 March the page was green, their health endpoint
returned 200, and both were correct — the vendor was up for the entire outage.

Then go to "Before you branch" and find out whether the worker is running.

**Escalating to the vendor.** Their 24h line took twelve minutes to reach a
human at 03:19 on a Saturday. Escalating is not the fast option, and the time
you spend on hold is time you are not reading logs.

Their on-call will ask for a failing request id. Have one before you call.

What they can tell you that we cannot see: whether we have made ingest
*attempts* for our tenant at all. No attempts means we stopped sending, which
rules out their side cleanly. That is genuinely useful — but `kubectl logs -p`
answers the same question in seconds and without waking anybody.

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
