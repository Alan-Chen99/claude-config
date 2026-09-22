## Evidence

```
$ grep -rn -i "legacy.tls\|TLS_MIN\|tls\|sni" . --exclude-dir=.git
docs/deploy.md:34,36,40,44,45,57   # only site in the repo

$ find . -name '*.yml' -o -name '*.yaml' -o -name 'Makefile'
(nothing — no CI config in this repo)

$ ./argtest.sh --env staging      # isolated repro of deploy.sh's arg line
deployed to --env

$ git log --oneline -2
e72c6b3 docs: gateway requires TLS 1.3
b25a749 ingest-api deploy docs
```

## Details

The whole `## TLS 1.1 gateway workaround` section was false in every claim: the gateway version, the instruction to pass `--legacy-tls` unconditionally, the "safe because newer clients ignore it" reassurance, the four-second-reset diagnostic, and the `INGEST_TLS_MIN=1.1` CI recommendation. Replaced with `## Gateway TLS`: 1.3 is negotiated by default, `--legacy-tls` must not be passed, `INGEST_TLS_MIN` is gone and should be removed where still exported.

Three judgement calls:

- **The flag warning stays, inverted.** The old doc actively told people to pass it unconditionally and not to remove it from call sites. That instruction is now in shell history, personal scripts, and people's heads. Silently deleting the section would leave them with a failing deploy and no explanation, so the section says the flag is now rejected and why it used to look harmless.
- **SNI is not in the doc.** Nothing scheduled, and Priya was not sure. A pre-deploy doc that everyone reads is the wrong place for a maybe — it would either be ignored or acted on prematurely. It belongs there once there's a date or a confirmed requirement.
- **The example invocations are gone rather than updated.** Their only purpose was to demonstrate the flag. Removing them also removed a second problem — see below.

I did not touch the two CI call sites: they're outside this repo (no CI config here) and you already fixed them.

## Summary

`docs/deploy.md` now describes the TLS 1.3 gateway and warns against the flag that used to be mandatory; committed as `e72c6b3`.

## Updates

- The doc says only that the call fails with `--legacy-tls`, not *how*. The vendor client isn't installed here, so I could not verify the error text. If you have it, a more specific symptom line would be worth adding — that's exactly what made the old four-second-reset note useful.

## Required notes

- **suspected user mistake:** `scripts/deploy.sh` reads `$1` as the environment, but its own usage string says `--env <staging|prod>` and the old docs showed `deploy.sh --legacy-tls --env staging`. As written, `deploy.sh --env staging` sets `ENV="--env"` (repro above). It only reaches the final `echo`, so it has been cosmetic, but the script and its usage message disagree. My edit removed the only doc examples, so the docs no longer show a broken invocation — the script is still inconsistent with itself. Fixing it changes deploy.sh behavior, so I left it for you: either parse `--env`, or change the usage string to positional.
- **instruction issue:** the pre-output hook forbids replying while uncertainties remain, but "what error text does a client I don't have print" is not resolvable from here. I removed the unverifiable mechanism claim from the doc instead and surfaced the gap.
- **context waste:** none — the repo is four files.
- **unexpected change:** none. `.prompt-test-settings.json` was untracked at session start and I left it that way.
