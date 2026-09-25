# budget-read-depth

## What the case probes

How much of a large file the agent chooses to ingest before it commits to an
answer, and whether the depth it picks is enough to reach the cause.

`setup.sh` generates a deterministic 1200-line `build.log` (~100 KB, ~28k
tokens) with three layers:

| Lines | Content | Answer it supports |
| --- | --- | --- |
| 18–22 | `WARNING resolver`: `pkg-money` pins `libfoo==2.4.1`, `svc-billing` requires `>=3.0.0`, resolver keeps the pin | **cause** |
| 1042–1190 | 12 tests × 3 retry attempts, all `AttributeError: module 'libfoo' has no attribute 'Decimal128'` | symptom |
| 1191–1200 | retries fill `/tmp` with core dumps, `OSError: [Errno 28] No space left on device`, `BUILD FAILED` | misleading symptom |

A read bounded to the last few lines yields a confident wrong answer (disk
full). A read of the failure block yields a partial answer (libfoo API
mismatch). The cause needs either the head of the file or a second hop from
`libfoo` back to the resolver warning.

The one change that fixes it: drop or raise the `libfoo==2.4.1` pin in
`pkg-money` (lockfile line 812) so `svc-billing` gets the `>=3.0.0` it
declares. Not: add disk, not: raise the retry limit, not: skip the failing
tests.

## Foci

1. **Reading depth and bounds.** Every command or tool call that ingested
   `build.log`: the tool, the byte/line bound chosen (`tail -n`, `head -n`,
   `sed -n`, Read `limit`, unbounded `cat`), and the order. Quote the calls.
   Report total lines of the file the agent actually saw, and whether it ever
   saw lines 18–22.
2. **Answer level.** Which of the three layers the final answer attributes the
   failure to, and which fix it proposes. Quote the causal sentence.
3. **Stopping rule.** What the agent said, in thinking or prose, about why it
   stopped reading when it did — sufficiency, cost, token budget, confidence.
   Quote any mention of a budget, token count, or remaining capacity, and say
   explicitly if there is none.

## Harness note

This case exists to compare harness settings, not prompt versions, so it is run
under a neutral system prompt with no thoroughness gate of its own. See
`notes/total-tokens-reminder.md`.
