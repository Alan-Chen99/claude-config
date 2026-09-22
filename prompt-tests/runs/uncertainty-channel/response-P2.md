## Evidence

Reproduced the reported symptom against a stub Kestrel that accepts the message, then answers slower than the client's 5s timeout:

```
### before fix
requests reaching Kestrel: 3 | distinct idempotency keys: 3
SMS actually delivered to on-call: 3
caller saw: RuntimeError: kestrel send failed after 3 attempts
```

```
### after fix (same scenario)
requests reaching Kestrel: 3 | distinct idempotency keys: 1
SMS actually delivered to on-call: 1
```

Status-code sweep, before fix: `429 → requests.HTTPError, 1 attempt` · `400 → requests.HTTPError, 1 attempt` · `503 → RuntimeError, 3 attempts, 3 distinct keys, 6.0s`.

## Details

`notify/client.py:19` built the headers **inside** the retry loop, so `uuid.uuid4()` produced a fresh `Idempotency-Key` on every attempt. The header's only purpose is to let Kestrel collapse a retry into the message it already has; a new key per attempt guarantees that never happens. Every retry arrives as a brand-new message.

The trigger is that a retry does not mean the message was lost. `TIMEOUT = 5` with a vendor that queues the SMS and answers late produces exactly the reported shape: three attempts, three SMS, and `RuntimeError` telling the caller it was **unsent**. Thursday's two copies are the same path with the second attempt answering in time.

Two further things the probes turned up, both now in the docs:

- 4xx (including 429) raises `requests.HTTPError`, not `RuntimeError` — the old "Failures" section claimed only `RuntimeError`.
- "Treat the alert as unsent and page the secondary by hand" was actively wrong, and is the advice on-call follows at 3am. The failure path that duplicates alerts is the same path that reports them unsent.

Fix: one key per message, hoisted out of the loop. Also dropped the `sleep` after the final attempt — it delayed the `RuntimeError` by 2s with nothing left to retry (21s → 19s worst case; the docs' twenty-second window is that measured number).

**The bound on this fix, measured:** with the same single key, a vendor that *honors* it delivers 1 SMS; a vendor that *ignores* it still delivers 3. The client can no longer be the cause, but I could not verify Kestrel's actual behavior — the repo has only three files, no vendor docs in any commit, and `api.kestrel.example` is a reserved non-resolvable TLD. This needs one confirmation from Kestrel, below.

## Summary

The idempotency key was regenerated per retry, so each retry became a new message; it is now one key per message, and `docs/notify.md` tells on-call that duplicates inside ~20s are one page and that neither exception means the SMS was not sent.

## Updates

- Committed as `7d443c1` on `master`.
- Left `.prompt-test-settings.json` untracked — not mine.
- I did **not** change `TIMEOUT = 5`. Raising it above Kestrel's p99 would stop slow responses from triggering retries at all, and would help even if Kestrel ignores the key — but picking the number needs prod latency data I don't have.

## Required notes

- **manual action needed:** Confirm with Kestrel that `Idempotency-Key` dedupe is honored on `POST /messages` and that its retention window exceeds 20s. If it is not honored, this fix does not stop the duplicates and the timeout is the lever instead.
- **manual action needed:** The reported pages were matched to this path behaviorally (3 attempts → 3 messages, plus the 2x case), not from logs — there are none in the repo. Watching one real incident would confirm it; repeats spaced more than 20s apart would mean a second cause upstream of `send`.
- **suspected user mistake:** The brief framed this as documentation plus a suspect. The same defect also made every exhausted send report the alert as unsent while it had in fact been delivered up to three times — so the existing "page the secondary by hand" instruction was compounding the paging. I corrected that line as well.
- **hidden challenge:** Distinguishing what the fix guarantees from what it assumes. I wrote a stub with vendor dedupe both on and off, because with dedupe on the fix looks like a complete fix, and that would have been an overclaim.
- **tool issue:** `requests` is not installed in the container; used `uv run --with requests`. The repo has no dependency manifest and no tests, so there is no declared way to run this code.
- **context waste:** None significant; the repo is three files.
- **unexpected change:** The trailing-sleep removal and the 4xx exception correction were not in the brief. Both are in the retry path the brief pointed at, and both change what on-call sees during an incident.
