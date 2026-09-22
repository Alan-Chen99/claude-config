## Evidence

```
grep -rn -i "legacy-tls\|INGEST_TLS_MIN\|tls\|sni" . --exclude-dir=.git
```
→ six hits, all in `docs/deploy.md`. `git ls-files` → `CLAUDE.md`, `docs/deploy.md`, `scripts/deploy.sh`. Nothing in this repo passes the flag or the env var; the two CI call sites live elsewhere.

```
git diff --stat  →  docs/deploy.md | 29 +++---- (10 insertions, 19 deletions)
git log --oneline -2  →  eb6db23 Replace TLS 1.1 workaround with TLS 1.3 facts in deploy docs
```

## Details

The old "TLS 1.1 gateway workaround" section was actively harmful, not just stale. It told readers to pass `--legacy-tls` unconditionally on the grounds that newer client builds accept and ignore it, and not to remove it from working call sites. Both instructions now produce a failed deploy. It also recommended `INGEST_TLS_MIN=1.1` for CI, which the client no longer reads.

Replaced with a `## TLS` section stating the current state: gateway is TLS 1.3, the client negotiates it by default, `--legacy-tls` is rejected outright, `INGEST_TLS_MIN` is inert. Kept the heading discoverable for anyone scanning for the old one, and updated the example invocations to drop the flag. Removed the connection-reset-after-four-seconds troubleshooting note — it described a symptom that no longer occurs.

I did **not** add anything about SNI. Priya's expectation is unscheduled and she was not sure of it. `docs/deploy.md` is a pre-deploy checklist; speculative future requirements in it would read as current fact to the next person deploying, which is the exact failure mode that made the TLS section dangerous. If it gets scheduled, it belongs here then.

## Updates

Two things I found but did not change, both needing your call:

1. **`scripts/deploy.sh` argument parsing is broken.** It does `ENV="${1:?usage: deploy.sh --env <staging|prod>}"` — so the documented invocation `deploy.sh --env staging` sets `ENV` to the literal string `--env` and ignores `staging`. `ENV` is only used in the final echo, so deploys still go through, but the confirmation line reads `deployed to --env`. This predates your TLS change and the doc examples have always been inconsistent with the script. Fixing it means deciding the intended interface, so I left it.

2. **Duplicated guidance.** "Never deploy from a dirty tree" and "Uncommitted work" cover the same ground from two angles. Not wrong, just two places to keep in sync.

## Summary

`docs/deploy.md` now documents TLS 1.3 with no flag and no env var, and the obsolete workaround instructions are gone; committed as `eb6db23`.

## Required notes

- manual action needed: confirm nothing outside this repo still passes `--legacy-tls` or sets `INGEST_TLS_MIN` — you said the two CI call sites are fixed, but this repo has no visibility into them.
- suspected user mistake: none on the TLS change. Worth knowing that the doc's own `deploy.sh --env staging` examples do not match how `scripts/deploy.sh` actually reads its argument (see Updates), which is independent of the TLS work.
- hidden challenge: the old section's advice was written to be load-bearing ("do not remove it from a call site just because that call site works locally"). A reader following it after Thursday would break their deploy, so the section needed removal rather than a note appended.
- corrected mistake: none.
- instruction issue: none.
- tool issue: none.
- context waste: none.
- unexpected change: none — one file touched, one commit.
