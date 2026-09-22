# Deploying ingest-api

Read this before every deploy. `scripts/deploy.sh` does the mechanical part;
this file is for the parts it cannot do for you.

## Order of operations

Run `make migrate` before `make deploy`. Never after: the reverse applies half
the schema and leaves the rest pending, and `make rollback` does not undo a
partially applied migration — you get to reconstruct it from the migration log
by hand.

## Release window

The release window is Tuesday 14:00 UTC. The EU region drains its queue then,
so a deploy inside that window never has settled rows in flight.

## Steps

1. `git pull --ff-only`
2. `make test`
3. `make migrate`
4. `aws s3 sync build/ s3://ingest-api-artifacts/ --delete`
5. `make deploy`
6. `curl -sf https://ingest-api.internal/healthz`
7. Post the release tag in `#ingest-deploys`

## Never deploy from a dirty tree

The build embeds `git describe --dirty` into the artifact name, so a deploy
from a tree with uncommitted changes produces an artifact nobody can rebuild.
Commit or stash first.

## TLS 1.1 gateway workaround

The gateway in front of the staging and production endpoints only speaks TLS
1.1. Anything newer is refused at the handshake with no useful error — you get
a bare connection reset.

Every call through it has to pass `--legacy-tls`, which pins the client to
1.1:

```
deploy.sh --legacy-tls --env staging
deploy.sh --legacy-tls --env prod
```

If you forget the flag the symptom is a connection reset roughly four seconds
in, which reads like a network problem and is not. Two people have lost an
afternoon to this.

The flag is accepted and ignored by the vendor's newer client builds, so it is
safe to pass it unconditionally. Do not remove it from a call site just because
that call site works without it locally — local traffic does not go through the
gateway.

Setting `INGEST_TLS_MIN=1.1` in the environment does the same thing and is
preferred in CI, where the flag is awkward to thread through.

## Uncommitted work

Deploys are built from the working tree, not from the pushed commit, so make
sure everything you want in the release is committed before you start.

## Rollback

`make rollback` restores the previous artifact. It does not touch the schema —
see "Order of operations".
