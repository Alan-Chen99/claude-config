#!/usr/bin/env bash
# Generates build.log in the scratch cwd. Deterministic: the same 1200 lines
# every run, so arms differ only in the harness setting under test.
#
# Structure is load-bearing. The cause is a resolver WARNING in the first 25
# lines; the symptoms are an AttributeError cascade from line ~300; the last
# lines are a disk-full OSError that is a consequence of the retry policy, not
# the cause. A short tail read therefore yields a confident wrong answer.
set -euo pipefail
python3 - <<'PY'
import random
r = random.Random(20260925)
mods = ["svc-billing","svc-ledger","svc-auth","svc-notify","pkg-common","pkg-money",
        "pkg-retry","adapters-psql","adapters-redis","adapters-s3","cli-admin","web-api"]
pass_names = ["roundtrip","idempotent","empty_input","unicode_keys","large_payload","retry_budget",
              "timeout_propagates","cancel_midflight","schema_v2","null_coalesce","tz_aware",
              "leap_second","paging_cursor","backpressure","partial_write","checksum","replay",
              "dedup_window","fanout","cold_start"]
fail_names = ["rounding","bankers_rounding","currency_convert","tax_split","invoice_total",
              "refund_partial","proration","discount_stack","fx_rate_pin","minor_units",
              "allocation_remainder","statement_render"]

head = ["nightly build 4471 starting on runner-07 (linux/amd64, 8 vCPU, 16G)",
        "git rev 9f2c1ab8 on main, 3 commits since 4470",
        "toolchain: python 3.12.4, uv 0.5.11, gcc 13.2.0, node 22.3.0",
        "cache: restored 1.8G from s3://ci-cache/nightly/main (hit)"]
head += [f"resolve: {m} -> lockfile ok ({r.randint(11,94)} deps)" for m in mods]
head += ["resolve: computing unified environment for 12 workspace members",
         "WARNING resolver: conflicting requirements for libfoo:",
         "WARNING resolver:   pkg-money   requires libfoo==2.4.1 (pinned, lockfile line 812)",
         "WARNING resolver:   svc-billing requires libfoo>=3.0.0 (pyproject.toml line 24)",
         "WARNING resolver: no version satisfies both; keeping the pin, installing libfoo 2.4.1",
         "WARNING resolver: svc-billing will run against an older libfoo than it declares",
         "installed 412 packages in 21.4s"]

mid = []
for m in mods:
    for k in range(4):
        mid.append(f"build {m}: compiled {r.randint(8,61)} files in {r.randint(200,4200)}ms")
    mid.append(f"build {m}: artifact {m}-0.{r.randint(3,41)}.{r.randint(0,9)}-py3-none-any.whl ok")
for m in mods:
    if m in ("svc-billing","pkg-money"):
        continue
    n_items = r.randint(60,180)
    mid.append(f"pytest {m}: collected {n_items} items")
    for n in pass_names:
        mid.append(f"pytest {m}/tests/test_{n}.py::test_{n} PASSED [{r.randint(1,240)}ms]")
    mid.append(f"pytest {m}: {n_items} passed in {r.randint(4,90)}.{r.randint(0,9)}s")

tail = []
def billing_attempt(attempt):
    out = [f"pytest svc-billing: collected 164 items (attempt {attempt}/3)"]
    for n in fail_names:
        out.append(f"pytest svc-billing/tests/test_{n}.py::test_{n} FAILED [{r.randint(1,40)}ms]")
        out.append("pytest   AttributeError: module 'libfoo' has no attribute 'Decimal128'")
    for n in pass_names[:9]:
        out.append(f"pytest svc-billing/tests/test_{n}.py::test_{n} PASSED [{r.randint(1,240)}ms]")
    out.append(f"pytest svc-billing: 12 failed, 152 passed in {r.randint(20,80)}.{r.randint(0,9)}s")
    out.append("pytest svc-billing: writing core dumps for 12 failures to /tmp/ci-cores")
    for k in range(6):
        out.append(f"core: /tmp/ci-cores/pytest-{attempt}-{k}.core ({r.randint(380,520)}M)")
    return out

tail += billing_attempt(1)
tail.append("pytest pkg-money: collected 88 items")
tail += [f"pytest pkg-money/tests/test_{n}.py::test_{n} PASSED [{r.randint(1,240)}ms]" for n in pass_names[:14]]
tail.append("pytest pkg-money: 88 passed in 31.2s")
tail.append("retry: svc-billing failed, policy nightly-flake-retry allows 2 more attempts")
tail += billing_attempt(2)
tail.append("retry: svc-billing failed again, 1 attempt left")
tail += billing_attempt(3)
tail += ["retry: attempts exhausted for svc-billing",
         "df: /tmp 14.9G used of 15.0G (99%)"]
tail += [f"core: write /tmp/ci-cores/pytest-3-{6+k}.core truncated at {r.randint(11,180)}M" for k in range(8)]
tail += ["report: generating junit xml to /tmp/ci-out/junit.xml",
         "report: Traceback (most recent call last):",
         'report:   File "/opt/ci/report.py", line 88, in write_junit',
         "report:     fh.write(tree.tostring())",
         "report: OSError: [Errno 28] No space left on device",
         "BUILD FAILED (exit 1) after 21m18s"]

# Pad the passing middle to land on exactly 1200 lines. Padding never moves the
# head or the tail, so the cause stays at the top and the misleading symptom
# stays on the last line.
k = 0
while len(head) + len(mid) + len(tail) < 1200:
    m = mods[k % 12]
    mid.append(f"pytest {m}/tests/test_{pass_names[k % 20]}_{k % 7}.py::test_variant PASSED [{r.randint(1,240)}ms]")
    k += 1

lines = head + mid + tail
assert len(lines) == 1200, len(lines)
with open("build.log", "w") as fh:
    for n, text in enumerate(lines):
        fh.write(f"[{12 + (n*7)//3600:02d}:{((n*7)//60) % 60:02d}:{(n*7) % 60:02d}] {text}\n")
PY
test "$(wc -l < build.log)" = 1200
grep -q 'OSError' <(tail -8 build.log)
grep -q 'WARNING resolver' <(head -25 build.log)
