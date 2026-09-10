# payments-relay runbook

payments-relay forwards settlement records from the ledger service to the
vendor's ingest API. It started life in 2023 as a cron script, moved to a
long-running worker in early 2024, and picked up its current name when the
billing team split off from platform. A few of the older alerts still fire under
the name `ledger-forwarder`; that is this same service. None of that history
changes how you operate it today, but it does explain why several module names
in the source do not match anything in this document, and why the oldest
dashboards have two entries for what is one thing.

## Deploying

Deploys go out through `./deploy.sh <env>`. The script builds the image, pushes
it, and rolls the deployment one pod at a time. A roll takes about four minutes
in production. You can watch it with `kubectl rollout status deploy/relay`, and
if you need to stop it mid-roll, `kubectl rollout pause` works and is safe — the
paused state is a normal state and nothing times out on it.

That command says `deploy/relay`; `INCIDENT-2026-03-14.md` uses
`deploy/relay-worker` throughout. One of the two is wrong and nobody has
established which. Confirm with `kubectl get deploy` before you copy a command
out of either document, and fix whichever is wrong when you find out.

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

## Certificates

The worker presents a client certificate to the vendor when it connects. It is
`relay-worker-client`, issued by the platform CA with a 90-day life, and it
reaches the worker from the `relay-tls` secret. It is not an environment
variable and it is not part of a deploy. Rotating it means reissuing from the
platform CA, updating the secret, and rolling the deployment so the pods mount
the new one.

Nothing rotates it automatically and nothing alerts on its expiry. That is what
took the service down for 51 minutes on 2026-03-14: the certificate expired at
03:04:11, the worker crash-looped from that moment, and from the outside it
looked exactly like a vendor outage — sends at zero, acks at zero, and the
vendor's status page green because the vendor was in fact fine.
`INCIDENT-2026-03-14.md` is the write-up.

**Check the expiry date now rather than when you need it.**

    kubectl get secret relay-tls -o jsonpath='{.data.tls\.crt}' \
      | base64 -d | openssl x509 -noout -enddate

That assumes the secret uses the standard `tls.crt` key, which nobody has
confirmed. If it comes back empty, `kubectl get secret relay-tls -o yaml` will
show you what the keys actually are.

The reason to run it rather than trust the date below is that every rotation
this service has had was manual, done on the day of expiry, which makes the next
expiry exactly 90 days after the last one and makes it somebody's job to
remember. The two rotations on record are 2025-12-14 and 2026-03-14, both by
Marcus, both by hand, exactly 90 days apart; `INCIDENT-2026-03-14.md` records
PLAT-2291 as open for automated rotation with expiry alerting at 14 days, and
gives the expiry after that as 2026-06-12.

Nothing has been written down since, so this document cannot tell you which of
the following is true, and the difference is the whole of the risk:

- PLAT-2291 landed, rotation is automated, and there is nothing to remember —
  in which case delete this list.
- It did not land, someone rotated by hand on 2026-06-12, and on the 90-day
  pattern the certificate now in production expires on or about **2026-09-10**.
- It did not land and nobody rotated, in which case this recurred on 2026-06-12
  and there is a second incident write-up somewhere that this runbook has never
  been told about.

Rotate ahead of the date rather than on it. A rotation on the expiry day is a
production roll under time pressure, and the 90-day cycle puts it on whatever
weekday it happens to land — 2026-06-12 was a Friday, which the Deploying
section asks you to avoid.

## The reconciliation job

It runs at 04:00 on Saturday, compares what we sent against what the vendor
acknowledges receiving, and opens one ticket per discrepancy. The tickets land
in the billing queue, not ours, and someone from billing triages them on Monday
morning.

It has not produced a false positive since it was deployed eleven weeks ago. It
has also not yet run through a month-end close, which is when the ledger service
backdates entries into a period we have already reported on, so treat a
discrepancy raised at the first month-end as unproven rather than as real.

14 March is the one data point on how it behaves after an outage, and it is an
odd one. The service was down from 03:04 to 03:58 that Saturday and the backlog
did not finish draining until 04:40, so the 04:00 run went off in the middle of
it — and came back clean. Nobody has worked out whether that is because the job
tolerates in-flight lag or because the window it happened to compare had already
settled. Do not lean on it in either direction: a clean run during a drain is
not yet evidence that the job is robust to one.

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

## When a page fires

This section exists because of 2026-03-14, when a client certificate expired at
03:04, the worker crash-looped from then on, and it took 51 minutes to read the
first line of crash output that said so. `INCIDENT-2026-03-14.md` is the account
of that night and is the source for the facts here; this section is only the
part that should change what you do next time.

### Look at our side first

Two commands. Under a minute. No theory about what is happening required:

    kubectl get pods                    # the RESTARTS column on the relay pods
    kubectl logs -p deploy/relay-worker | head -20

If that second command comes back "not found", the deployment is `deploy/relay`
and not `deploy/relay-worker`. This document and the 14 March write-up disagree
about which it is and nobody has settled it; `kubectl get deploy` will tell you
in one line. Do not spend longer than that on it.

The first tells you whether the worker is alive. A restart count that is
climbing means it is crash-looping, and a crash-looping pod is a worker failing
to **start**, several times a minute — even when the symptom you were paged
about is that nothing is being **sent**. On 14 March those looked like two
different problems and they were one.

The second tells you why it died. The `-p` is what matters: it gives you the
previous container. Without it, `kubectl logs` gives you the current one, which
on a crash-looping pod is usually still initialising and says nothing. Running
that command at 03:11 would have ended the incident at 03:11.

Do both before you form a view about the vendor. They are close to the only
thing in an outage that is unambiguous, and they cost a minute.

### What the synthetic check can and cannot tell you

The check runs every minute against a fixed record id and pages as
`synthetic-check: no successful send in 3m`. It fires when a send does not
succeed. It cannot tell you why, and specifically it cannot distinguish "the
vendor is down" from "we cannot reach the vendor" — it fails identically in both
cases, with the same alert and the same text. On 14 March it was the second one.

So the check firing is not evidence that the vendor is down. An earlier version
of this runbook said the check will alert on its own if the vendor is down,
which is true as far as it goes and was read — reasonably — as licence for "the
check is firing, therefore the vendor is down". That reading drove the next
forty minutes.

### Four things that looked like evidence on 14 March and were not

Once you are carrying a theory, most of what you can check quickly will appear
to confirm it. These four did:

- **The vendor's status page was green.** It was green because the vendor was
  up. It was discounted as stale — 3am, last updated twenty minutes earlier —
  because it disagreed with the theory. A green status page in the middle of an
  outage you believe in is a reason to doubt the theory, not the page.
- **Their health endpoint returned 200 from a laptop.** That was read as a
  partial outage: their edge fine, their ingest broken. It does not support
  that. A curl from your laptop does not present the client certificate the
  worker mounts, so it cannot tell you whether our pods can complete a TLS
  handshake with them — which on that night was exactly what was failing.
- **A restart came back and immediately crash-looped again.** That was read as
  confirming the cause was external. It is close to the opposite: a process that
  dies again the moment it restarts is failing on its own boot path, before it
  gets far enough to depend on anything the vendor does.
- **Grafana's acks panel read zero.** It reads zero when we are sending and
  getting nothing back, and zero when we are not sending at all. Those are the
  two cases you are trying to separate and the panel renders them identically,
  so it cannot be used to separate them. The 14 March write-up records this as a
  known gap and names no ticket for it.

### Waking people, and calling the vendor

**Understand what you are looking at before you wake anyone up — which on this
service means the two commands at the top of this section, and about a minute of
your time. If a minute has not resolved it, you have done what this asks for.
Wake someone.**

That is a preference, not a rule, and it is worth being clear about whose. It
was written in here after 14 March by the engineer who was on the pager that
night and who wrote `INCIDENT-2026-03-14.md`. It is not a team decision, it has
not been agreed with anyone, and it is not a property of the synthetic check or
of any other alert — it applies to any page on this service. It is written down
because it was not written down anywhere before, and an unwritten preference is
one nobody can weigh or argue with. If you would rather work the other way, that
is a conversation to have, not something you are breaking by doing.

It is not an argument against escalating and it is not a licence to sit on your
own while a queue climbs. Those two commands are the whole of what "understand
what you are looking at" asks for on this service. It is about the minute, not
about the hour after it.

What it argues against is the specific order 14 March went in — the vendor
escalated at 03:19 and Priya woken at 03:26, both before anyone had looked at
the crash output, and Marcus at 03:44 for the same reason. The write-up is
honest that the escalation was deliberate: the queue was climbing, there was no
diagnosis, and getting the vendor on the line felt like the thing that could not
wait. That judgement is not the problem. Doing it before the one-minute check is.

Two things about the vendor's 24h line, both observed once, on 14 March, at 3am
on a Saturday, and neither since:

- It took twelve minutes to get from the automated menu to a human, which is
  the only time anyone has timed it. On that one showing escalating is not the
  fast option, and twelve minutes on hold are twelve minutes not spent reading
  logs.
- Their on-call's first question was for a failing request id. If you do not
  have one, the first part of the call is you establishing, with them listening,
  what you could have established alone.

## Troubleshooting

Check that our worker is up before you work any of these entries; see "When a
page fires" above. Matching a symptom straight to an entry is how 14 March went
wrong — the symptom was "nothing is being sent", it matched "Alerts firing with
no traffic", and the entry that would have solved it at 03:11 is the one
immediately below.

**The worker will not start.** Nine times out of ten this is a missing
environment variable, and the error message names it. Read the first line of the
crash output before doing anything else:

    kubectl logs -p deploy/relay-worker | head -1

If that comes back "not found", the deployment is `deploy/relay`; see "Look at
our side first" above. Use the `-p`. Without it you get the current container, which on a crash-looping
pod is usually still initialising and tells you nothing. The second most common
cause is a migration that has not been run, which looks like a column error in
the first query the worker makes on boot. The third, on the strength of one
occurrence, is an expired client certificate — see the next entry.

Come to this entry even when the worker looks to you like it started fine. On 14
March the reasoning was that the worker was not failing to start, it was failing
to send, so this entry did not apply. A crash-looping pod is failing to start,
several times a minute, and "nothing is being sent" is what that looks like from
the dashboards.

**TLS handshake failures and expired client certificates.** The worker presents
the client certificate `relay-worker-client`, mounted from the `relay-tls`
secret, and it has a 90-day life with no automated rotation. When it expires the
worker crash-loops from the moment of expiry, and the first line of its crash
output is:

    FATAL: TLS handshake failed: certificate expired at <timestamp>

From the outside this is indistinguishable from a vendor outage — sends stop,
acks stop, `pending` climbs, and the vendor's status page stays green because
nothing is wrong on their side. The fix is to reissue from the platform CA,
update the secret, and roll the deployment; Marcus has done both rotations on
record. See "Certificates" above for the expiry schedule and for how to check
the current one, which is worth doing before you are woken by it.

**Alerts firing with no traffic.** The synthetic check runs every minute against
a fixed record id and will alert on its own even when we are sending nothing.
Note what that does and does not establish: it alerts identically whether the
vendor is down or we cannot reach the vendor, so the alert itself does not tell
you which, and on 14 March it was the second. Check that our worker is up before
you check the vendor's status page — and if the status page is green, take that
as evidence rather than as staleness until you have something that contradicts
it. "When a page fires" above has the longer version.

**503s from the vendor.** Nearly always pool exhaustion. Check `WORKERS` first
before you go looking at anything else, because it explains this symptom more
often than every other cause put together.

**Records stuck in `pending`.** The worker marks a record `pending` when it
hands it to the vendor and `sent` when the vendor acknowledges. A record that
sits in `pending` for more than an hour means an acknowledgement was lost, not
that the record was lost. Re-driving it is safe. There is a script for this,
`./redrive.sh <record-id>`, and it takes one id at a time by design.

That is advice about a handful of records, not about a backlog. When sending has
stopped altogether everything piles up in `pending` and none of it needs
re-driving: on 14 March the queue drained on its own within about forty minutes
of the worker coming back, nothing was lost, and that Saturday's reconciliation
came back clean. Hand-driving a backlog is also how February's rate-limiting
happened — see "Access and conventions".

One thing in this entry does not add up, and it is worth knowing before you lean
on it. The definition above says a record becomes `pending` when the worker
hands it to the vendor, but on 14 March `pending` climbed at roughly the ledger's
write rate for 51 minutes while the worker was dead and handing nothing to
anybody. Either records enter `pending` earlier than this says, or the Grafana
panel labelled `pending` counts something other than the record state. Nobody
has checked which. Until somebody does, read a climbing `pending` as "work is
arriving and not completing", which holds under either reading, and do not read
it as "we are sending and not being acknowledged", which holds under only one.

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
