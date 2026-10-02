# skills/telegram-hitl/

## Files

| File | What | When to read |
| --- | --- | --- |
| `SKILL.md` | The rules an agent follows on the channel: sending, topics, listening, waiting. 1,000-token cap in `doc-budget.toml` | Using the channel; any edit here is paid by a removal |
| `listen.py` | The log reader: the listener armed under `Monitor`; `--wait`, a foreground call that returns the next message(s); `--peek`, one pass; `topics` | Changing what is announced or how a wait ends |
| `README.md` | What the listener guarantees (R1–R7), why the wait is a foreground call and what `BASH_MAX_TIMEOUT_MS` does, the measured harness facts under it | Before changing `listen.py` or the Listening rules; diagnosing a loop that hung on a listener or advanced past a human |

Design record: `docs/superpowers/specs/2026-09-12-telegram-hitl-design.md`.
Tests: `tests/test_telegram_hitl_skill.py`.
