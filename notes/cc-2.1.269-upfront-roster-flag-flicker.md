# The upfront tool roster is not a pure function of version and model id

> **Dated record.** Claude Code **2.1.269**, one account, one capture session
> (2026-09-11, re-derived 2026-09-30). Every figure and `src/chunk-*.js` citation
> is that build's: do not re-pin them, re-measure. The artifacts are
> `docs/system-prompt-snapshot/<model-id>/<variant>/`, whose `README.md` carries
> the capture procedure.

Timeline, from this batch's own file timestamps (`cc_version=2.1.269.d5c` on every capture):

| Time | Capture(s) | Upfront / deferred |
|---|---|---|
| 19:10 | `opus-5/default` | 14 / 18 |
| 19:29 | `opus-4-7/default` | 14 / 21 |
| 19:31 | `sonnet-5/default`, first capture | **13 / 17** |
| 19:32-19:39 | the other 5 sonnet-5 variants, and `opus-5/system-prompt-file` | 14 / 18 |
| 21:16 | `sonnet-5/default`, re-capture | 14 / 18 |
| 21:44 | `fable-5/default`, first capture | **13 / 17** |
| 22:04 | `fable-5/default`, re-capture (the one on disk) | 14 / 18 |

Two anomalous runs across two models, both missing exactly `SendFeedback` and
`EndConversation`, both non-reproducible on a same-variant re-capture. **The mechanism is
identified** from the 2.1.269 decompile:

- **`SendFeedback`** is gated on the GrowthBook flag `tengu_juniper_relay`: its `isEnabled()`
  (`src/chunk-dbb93264.js:181066`) calls `iL()`, which requires the `feedbackDrafts` setting
  not be `"off"` and `rCn()` to hold — an entrypoint/provider chain ending in
  `I("tengu_juniper_relay", !1)` on every path, `CLAUDE_CODE_SEND_FEEDBACK=true` included
  (`src/chunk-dbb93264.js:180877-180888`). Hardcoded fallback **false**.
- **`EndConversation`** is gated on `tengu_umber_kestrel`, same shape and fallback — `zGt`
  (`src/chunk-t7d8rn9f.js:92-100`), consumed at `src/chunk-1qj1h00h.js:276-279`.
- **Why both vanish together**: both resolve through one per-process GrowthBook client, `Tt()`
  (`src/chunk-5cs6j3p3.js:24712-24732`), and one method, `getFeatureValueWithSource`
  (`src/chunk-5cs6j3p3.js:9166-9197`), whose order is the load-bearing part: it checks this
  process's own fetch result `this.remoteEvalFeatureValues.get(key)` first, and if the key is
  absent **but the map has any keys** (`.size > 0`) it returns the hardcoded default — the
  on-disk cache (`cachedGrowthBookFeatures`) is consulted only when the map is empty. One fetch
  that succeeds but lacks a key turns that flag off for the process's life whatever the disk
  cache says; a payload missing both keys turns both tools off together.
- **This also explains `opus-4-7` never showing `EndConversation`**: `zGt` first requires the
  model to clear a per-family threshold, `[["opus",[4,8]],["sonnet",[5]],["fable",[5]],
  ["mythos",[5]]]` (`src/chunk-t7d8rn9f.js:62`), compared by `MZt`
  (`src/chunk-970xe2g2.js:20-32`). `claude-opus-4-7` parses to `[4,7]` and fails `>= [4,8]`;
  `claude-sonnet-5` and `claude-fable-5` clear `[5]` trivially, so for them the flag is the only
  variable — exactly the pair that flickered. `SendFeedback`'s gate has no version check; one
  opus-4-7 capture cannot say whether it is immune to the flicker.

**Inferred, not observed**: that the proximate cause was a GrowthBook fetch that succeeded
with an incomplete payload — the only path yielding both flags false against a warm, correct
disk cache (`/root/.claude.json` caches both as `true`). The exchange itself was never
captured: the MITM proxy logs only Messages-shaped bodies, so
`api.anthropic.com/api/eval-authed/*` never reaches it. Capturing that endpoint would close
this.

Consequence: a single capture's tool inventory is not by itself evidence about a version — a
flag-gated tool can be present or absent independent of version and model id. A comparison
that trusts one capture's tool count without cross-checking siblings or re-capturing could
attribute an account-side flicker to a CLI release; two independent occurrences, both clearing
on re-capture, is why this is a finding and not noise.

