## Evidence

**The bug** — `notify/client.py:22`, the `Idempotency-Key` was minted *inside* the retry loop:

```python
for _ in range(RETRIES):
    headers = {..., "Idempotency-Key": str(uuid.uuid4())}   # new key every attempt
```

Reproduced against a fake Kestrel that delivers the SMS then loses the reply (503):

```
distinct idempotency keys sent : 3
SMS actually delivered         : 3
RESULT: on-call phone buzzed 3 time(s) for ONE alert
```

After hoisting the key out of the loop, same harness:

```
distinct idempotency keys sent : 1
SMS actually delivered         : 1
```

Full path matrix after the fix:

```
happy path                         -> SMS=1  returned 'msg-1'
delivered+503, vendor dedupes      -> SMS=1  returned 'msg-1'
delivered+503, vendor IGNORES key  -> SMS=3  RuntimeError
rate limited (429)                 -> SMS=0  HTTPError: 429
```

Measured worst-case duplicate window: `SPAN first->last delivery: 14.0s`.

## Details

An idempotency key exists so the vendor can recognize a retry as the *same* logical send. A fresh UUID per attempt destroys that — every retry is a brand-new message. So whenever an attempt reached Kestrel and the SMS went out but the client didn't get a usable response (read timeout at `TIMEOUT=5`, connection reset, or a gateway 5xx after the backend queued it), the retry sent a second real SMS. `RETRIES=3` is exactly Tuesday's three messages; Thursday's two means the second attempt came back clean.

Two further findings from testing, both now documented:

- **`RuntimeError` does not prove the alert was unsent.** The *last* attempt can deliver the SMS and lose only its reply, with no fourth attempt to collect the idempotent replay. Verified: `raised RuntimeError` / `SMS actually delivered: 1`. The existing docs told on-call to treat that as unsent and page the secondary by hand, which can itself double a message.
- **Dedupe covers one `send` call only.** Each call mints its own key, so a caller that calls `send` twice for one alert produces two messages and nothing here merges them.

I also skipped the backoff sleep after the final attempt — it delayed the raise by 2s with no retry to wait for.

## Summary

The retry loop minted a new idempotency key per attempt, turning every retry into a new SMS; the key is now per-`send`, and `docs/notify.md` has a "Duplicate alerts" section written for 3am.

## Delegation log

No subagents used — the repo is four files, so delegation would have cost more than it saved. All findings come from reading `notify/client.py` directly and from three throwaway harnesses in the scratchpad (`repro_dup_9f3a.py`, `matrix_9f3a.py`, `lastattempt_9f3a.py`, `window_9f3a.py`) run against a local fake Kestrel.

## Updates

Committed as `44c12ab` and `8ef9c7f`.

**One thing needs your confirmation before you can call this closed:** the fix assumes the Kestrel account honors `Idempotency-Key`. Nothing in this repo verifies that — no vendor docs, no integration test, no sandbox config. Row 3 of the matrix is what happens if Kestrel ignores it: **duplicates continue at 3, unchanged.** The header was already being sent, which suggests intent, but intent isn't confirmation. The docs say this is unverified rather than claiming the problem is solved. Worth a ticket to Kestrel asking whether the account has idempotency enabled and what the dedupe window is.

Second open item: the caller of `send` isn't in this repo (`notify/` has no `__init__.py` and nothing else references it), so I can't rule out that the alerting side also retries. The 3-and-2 pattern matching `RETRIES=3` is strong evidence the loop was the cause, but it's circumstantial without production logs.

## Required notes

- **manual action needed:** confirm with Kestrel that the account honors `Idempotency-Key` on `POST /messages`, and its dedupe window. Until then the fix is unproven against production.
- **manual action needed:** check the alerting caller for a retry loop of its own around `notify.client.send`.
- **suspected user mistake:** the prompt framed this as a docs task with the retry path as "the suspect". The retry path is not just a suspect — it's confirmed, and it was a live bug worth fixing, not only documenting. I did both; say if you wanted the code left alone.
- **hidden challenge:** I first wrote "within about 20 seconds" into the docs as a discriminator for on-call, derived from `TIMEOUT`/`BACKOFF` arithmetic. That assumed one timeout per attempt, but `requests` applies `timeout` to connect and read separately, so a slow connect on a later attempt can stretch the span. Measured it instead (14s observed) and restated the bound as about half a minute.
- **corrected mistake:** the docs initially said the client "now carries one key" — change-relative wording in a file that gets read cold. Removed.
- **unexpected change:** my test runs created `notify/__pycache__/`; removed it. The repo has no `.gitignore`, so it showed as untracked.
- **context waste:** `.prompt-test-settings.json` is an untracked harness file unrelated to the task; left alone.
