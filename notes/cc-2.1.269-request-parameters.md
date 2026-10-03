# 2.1.269 request parameters and billing-header fields

> **Dated record.** Claude Code **2.1.269**, one account, one capture session
> (2026-09-11, re-derived 2026-09-30). Every figure and `src/chunk-*.js` citation
> is that build's: do not re-pin them, re-measure. The artifacts are
> `docs/system-prompt-snapshot/<model-id>/<variant>/`, whose `README.md` carries
> the capture procedure.

| | 2.1.235 | 2.1.269 |
|---|---|---|
| `max_tokens` (sonnet, opus) | 64,000 | 64,000 (unchanged) |
| `model` | `claude-sonnet-5` / `claude-opus-5` / `claude-opus-4-7` | unchanged |
| `thinking` | `{"type": "adaptive"}` | `{"type": "adaptive", "display": "updates"}` — new `display` key, every model, every variant |
| `thread` | absent | `{"type": "create"}` — new key, every model, every variant checked |
| `fallbacks` (opus-5 only) | `[{"model": "claude-opus-4-8"}]` | **absent** — opus-5's fallback entry is gone; opus-4-7 had no `fallbacks` key in either version |
| `output_config.effort` | varies per request already in 2.1.235 (see below) | varies per request; all 8 `claude-sonnet-5` requests this round (6 variants + 2 subagent children) read `"high"` |

`fallbacks` disappearing for opus-5 lines up circumstantially with `claude-opus-4-8` now being
a standalone selectable id (see `notes/cc-2.1.269-fable-and-mythos-model-ids.md`) rather than purely an opus-5 fallback
target, though this document can't prove causation from the captures alone.

**Correction to the 2.1.235 doc**: it reported `output_config: {"effort": "max"}` as flat and
unchanged. Every individual 2.1.235 capture shows otherwise — `opus-4-7` was `xhigh`, `opus-5`
`high`, and sonnet-5's own captures split between `"max"` (`append`, `custom-output-style`,
`subagent`, `system-prompt`, `system-prompt-file`) and `"high"` (`default`). `effort` is
resolved per request, consistent with `thinking.adaptive`. This round opus-4-7 stayed `xhigh`,
opus-5 `high`, and all eight `claude-sonnet-5` requests read `high` — a data point, not a new
fixed value.

`context_management` (`clear_thinking_20251015`, keep all), `diagnostics`, and `stream` are
unchanged from 2.1.235.

### Billing header fields

`cc_version` bumped (`2.1.269.d5c` most calls in this batch; `.500` on the `sonnet-5/subagent`
parent call; `.415` on both its subagent children — same per-call-type suffix variance the
2.1.235 doc documented, just different literal suffixes). `cc_prompt_id`, `cc_prev_req`, and
`cc_is_subagent=true` are all still present and still vary per request exactly as before; no
new billing fields observed.

