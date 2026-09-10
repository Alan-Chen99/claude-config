# payments-relay runbook

payments-relay forwards settlement records from the ledger service to the
vendor's ingest API. It started life in 2023 as a cron script, moved to a
long-running worker in early 2024, and picked up its current name when the
billing team split off from platform. A few of the older alerts still fire under
the name `ledger-forwarder`; that is this same service. None of that history
changes how you operate it today, but it does explain why several module names
in the source do not match anything in this document, and why the oldest
dashboards have two entries for what is one thing.

The same drift reaches the Kubernetes objects. This document says
`deploy/relay`; the commands people actually run say `deploy/relay-worker`, and
that is the form known to have worked under pressure on 14 March. Nobody has
established which is correct or whether both resolve. Run `kubectl get deploy`
once at the start rather than discovering the answer at 3am.

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

The environment variables are not the whole of what the worker needs at boot.
The client certificate is mounted from a secret rather than passed as a
variable, and it is the other thing that will stop the worker starting. It has
its own section, below, because unlike anything on this list it expires on a
date.

## The client certificate

The worker authenticates to the vendor with a client certificate,
`relay-worker-client`, issued by the platform CA and mounted into the pod from
the `relay-tls` secret. It has a 90-day life. **The current one expires
2026-06-12.**

Nothing monitors that date. Nothing rotates the certificate, the worker does not
warn as it approaches, and no alert fires when it passes. Every rotation so far
has been done by hand on the secret manifest and followed with a rollout to pick
the new one up. PLAT-2291 is open to automate rotation with expiry alerting at
14 days; until it lands, the date above is the only warning that exists, and it
exists only because it is written here. If you are reading this after 2026-06-12
and nothing has changed, that is the first thing to check.

An expired certificate stops the TLS handshake, so the worker dies on boot and
crash-loops. From outside it is indistinguishable from the vendor being
unreachable: sends fall to zero, acks fall to zero, and nothing in our metrics
or dashboards contains the word "certificate". The first line of the crash
output says it plainly. That is the whole of 14 March; see
`INCIDENT-2026-03-14.md`.

Diagnosing it is not the same as fixing it. The replacement is issued from the
platform CA, and on 14 March that was done by someone with CA access rather than
by the on-call. If you are on the pager and you find an expired certificate, you
will need that person, so find out now who they are on your rotation — this
document does not know, and 3am is a bad time to learn it. The fix itself is
quick: reissue, update the `relay-tls` secret, roll the deployment. From reading
the log line to sends resuming was seven minutes on the night.

## The reconciliation job

It runs at 04:00 on Saturday, compares what we sent against what the vendor
acknowledges receiving, and opens one ticket per discrepancy. The tickets land
in the billing queue, not ours, and someone from billing triages them on Monday
morning.

It has not produced a false positive since it was deployed eleven weeks ago. It
has also not yet run through a month-end close, which is when the ledger service
backdates entries into a period we have already reported on, so treat a
discrepancy raised at the first month-end as unproven rather than as real.

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

## Escalating

We would rather understand what we are looking at before we wake anyone up.

That is a preference, not a rule. Nobody has agreed it as policy and nobody will
enforce it. It is written down here because it was not written down anywhere,
and because on 14 March the order things were done in cost considerably more
than the fault did. It is also not a rule about any particular alert — it
applies to the pager generally.

What it asks for is small. Before you wake someone, be able to say what you have
observed, what you have ruled out, and what you currently think is happening.
"I don't know yet" is a complete answer to the third one. It is worth noticing,
though, that at 03:26 on 14 March the honest answer to "is our worker running?"
was also "I don't know" — and those are different gaps. One is a conclusion you
have not reached. The other is a check you have not run. That particular check
takes about ten seconds and is the first entry under Troubleshooting.

Two things make escalating feel faster than it is. The vendor's 24h line took
twelve minutes to reach a human on 14 March — automated menu, then hold — so
whatever else escalation is, it is not the quick option, and those twelve
minutes come out of your attention rather than from somewhere else. And waking
someone is not itself progress: both times someone was woken that night, the
useful thing they did was ask a question the on-call could have asked
themselves.

None of that is an argument for holding the pager alone. Being stuck is a real
state and it is worth waking someone for. When you do, say that you are stuck
rather than handing over a theory — a theory is contagious, and on 14 March the
theory was wrong for the best part of an hour and got more confident as it went.
Prefer someone who knows this service over the party you believe is at fault.
That is what ended it that night.

If you do call the vendor, two things save time. Have a failing request id
ready; it is the first thing they ask for and on 14 March we did not have one.
And ask whether they are seeing ingest *attempts* from our tenant, not whether
they are seeing errors. Attempts separate "we cannot reach you" from "you are
broken", which is the question you are actually there to answer. On 14 March
that reply — no attempts for about twenty-five minutes — was the most decisive
fact anyone produced, and it arrived twenty minutes before anybody acted on it.

## Troubleshooting

The entries below are symptoms as you would describe them at 3am, and they
overlap. More than one can be true at once, and the entry that best matches your
first description of the problem is not necessarily the one that solves it. On
14 March the entry that solved it was "The worker will not start" and the entry
that matched was "The synthetic check is alerting" — and the one that matched
was the wrong one, for forty minutes. If an entry has not resolved things within
a few minutes, come back and read the others rather than digging deeper into the
first.

**Settlements have stopped.** Start here, whatever the alert said. The first
question is not what is broken but whose it is, and there is a cheap check that
settles it:

    kubectl get pods | grep relay

Restart counts climbing, or pods not in `Running`, means the fault is ours and
you are looking at a worker that cannot start — go to that entry. Pods healthy
with a stable restart count means we are up and running, and the failure is
somewhere downstream of us.

Do not try to answer this from the dashboard. Grafana's "acks" panel reads zero
when we are sending and getting nothing back, and also when we are not sending
at all; sends-at-zero and acks-at-zero is the identical picture for "the vendor
is ignoring us" and "we are dead", which are precisely the two things you are
trying to tell apart. `pending` climbing does not separate them either — see the
`pending` entry below for why that number means less than it looks like it
means.

**The synthetic check is alerting.** The check runs every minute against a fixed
record id, independently of real traffic, so it fires whether or not we are
sending anything of our own. What it tells you is that a send failed. It does
not tell you why, and in particular it cannot distinguish the vendor being down
from us being unable to reach the vendor — it fails identically in both cases.
On 14 March it was the second one, while an earlier version of this entry said
it meant the first.

So read it as "a send failed", and nothing further, then go to "Settlements have
stopped" to find out whose failure it is.

The vendor's status page is worth about ten seconds. On 14 March it said green,
twenty minutes stale, and it was correct — and it was dismissed as stale
precisely because this runbook had already supplied a story that it
contradicted. If you catch yourself explaining away a piece of evidence, that is
worth a moment on its own: it is cheaper to doubt the theory than to keep buying
exceptions for it.

**503s from the vendor.** Nearly always pool exhaustion. Check `WORKERS` first
before you go looking at anything else, because it explains this symptom more
often than every other cause put together. A 503 also tells you something no
alert does: we reached them. Whatever else is wrong, it is not that we cannot
get to the vendor at all.

**Records stuck in `pending`.** The worker marks a record `pending` when it
hands it to the vendor and `sent` when the vendor acknowledges. A record that
sits in `pending` for more than an hour means an acknowledgement was lost, not
that the record was lost. Re-driving it is safe. There is a script for this,
`./redrive.sh <record-id>`, and it takes one id at a time by design.

That description does not survive contact with 14 March, and the discrepancy is
unresolved. The worker was dead from 03:04 and sending nothing at all, and
`pending` still climbed at roughly the ledger's write rate — which cannot happen
if handing a record to the vendor is what puts it in `pending`. Either records
are created `pending` by the ledger and the worker only ever moves them out, or
something else is going on. Nobody has checked, and until somebody does, treat
the paragraph above as describing one record rather than a pile of them.

The operational consequence: the size of a `pending` backlog is not evidence
that acknowledgements were lost. A backlog that grew during an outage is most
likely just the ledger having carried on writing while we were down. On 14 March
it drained on its own by 04:40, a little over forty minutes after the worker
came back, with nothing redriven and nothing lost. Redrive individual records
that are both old and isolated. Do not redrive a backlog — that is the February
incident.

**The worker will not start.** This entry covers crash-looping, and that is
worth saying out loud, because on 14 March it did not read that way from
outside: sending was the visible failure, so an entry about starting looked like
the wrong entry for forty minutes. A pod that crash-loops is a pod that fails to
start, several times a minute. If the restart count is climbing, you are in the
right place.

Read the first line of the crash output before you do anything else:

    kubectl logs -p deploy/relay-worker | head -1

The `-p` matters. Without it you get the current container, which on a
crash-looping pod is usually still initialising and says nothing useful; `-p`
gives you the one that just died, which is the one carrying the error.

Three causes account for nearly all of these, and that first line names which:

- A missing environment variable. The most common by a distance, and the message
  names the variable.
- A migration that has not been run, which looks like a column error in the
  first query the worker makes on boot.
- An expired client certificate, which appears as a TLS handshake failure with
  `certificate expired at ...` on it. See "The client certificate" above for the
  next expiry date and for why you will need someone else to fix it.

A restart is not a diagnostic step here. If a pod crash-loops again immediately
after you restart it, that is the fault being local and reproducible — close to
the opposite of what it feels like at the time.

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
