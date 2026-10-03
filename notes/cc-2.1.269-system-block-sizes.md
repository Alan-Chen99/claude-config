# The 2.1.269 system prompt is four blocks, and not one size

> **Dated record.** Claude Code **2.1.269**, one account, one capture session
> (2026-09-11, re-derived 2026-09-30). Every figure and `src/chunk-*.js` citation
> is that build's: do not re-pin them, re-measure. The artifacts are
> `docs/system-prompt-snapshot/<model-id>/<variant>/`, whose `README.md` carries
> the capture procedure.

The `system` array still carries 4 text blocks, same cache placement as 2.1.235: blocks 2 and 3
carry `cache_control`; only block 2 sets `scope: global` (block 3 omits `scope`, so it falls
back to org scope).

Sizes below are **characters**, measured directly from `request.json`; for the byte-identity
questions this doc cares about they are the stronger evidence — the 2.1.235 doc's per-tool
token table showed `Skill` at 977 sonnet-tokens vs 909 opus-tokens on identical text, a
tokenizer artifact. Whole-request **token** totals (`system_tokens` / `tools_total_tokens`)
are exact, measured by `count_tokens` at capture time into each variant's `summary.json`.

| Block | Content | Cache | Opus 4.7 | Sonnet 5 | Opus 5 | Fable 5 | Opus 4.8 |
|---|---|---|---|---|---|---|---|
| 0 | Billing header (`cc_version=2.1.269...`) | none | 132 | 132 | 132 | 132 | 132 |
| 1 | Identity (`"You are Claude Code, Anthropic's official CLI for Claude."`) | none | 57 | 57 | 57 | 57 | 57 |
| 2 | Static behavioral rules | 1h, global scope | 10,676 | 10,574 | 1,210 | 1,210 | 1,152 |
| 3 | Session guidance, memory, environment (ecosystem facts only — see below), context mgmt | 1h, org scope | 16,895 | 17,128 | 8,546 | 9,571 | 5,278 |

Every figure above is the `default` variant, and block 2 is not a pure function of the model:
its opening sentence tracks the active output style. With one selected, `helps users with
software engineering tasks` becomes `helps users according to your "Output Style", which
describes how you should respond to user queries`, and sonnet-5's block 2 measures 10,631 chars
rather than 10,574 (`sonnet-5/custom-output-style/request.json` against
`sonnet-5/default/request.json`; `append` and `subagent` both stay at 10,574). Calling the block
static is true of a release, not of a session.

Block 1 is unchanged byte-for-byte from 2.1.235 for every model that existed to compare. Block
0 is the billing header: `cc_version` (`2.1.235.cf9` -> `2.1.269.d5c`), a per-run `cch` hash and
`cc_prompt_id` change on every capture, its 132-char layout does not. Opus 4.7, Sonnet 5 and
Opus 5's block 2 is each unchanged byte-for-byte from 2.1.235 (10,676/10,574/1,210), so all of
their version-over-version change is in block 3 — `notes/cc-2.1.269-block3-relocation.md`. Block 2 is not
one shared text per branch either — `notes/cc-2.1.269-prompt-split-per-model-id.md` is why 1,210/1,210/1,152
is not a typo.

Total `system_tokens` per variant (from `summary.json`, exact):

| Variant | Opus 4.7 | Sonnet 5 | Opus 5 | Fable 5 | Opus 4.8 |
|---|---|---|---|---|---|
| `default` | 8,702 | 8,745 | 3,252 | 3,556 | 2,266 |
| `custom-output-style` | — | 8,761 | — | — | — |
| `append` | — | 8,754 | — | — | — |
| `subagent` | — | 8,743 | — | — | — |
| `system-prompt` / `system-prompt-file` | — | 116 / 114 | — / 117 | — | — |

2.1.235 comparison (opus-4-7/sonnet-5/opus-5): 9,329 / 9,368 / 3,860 — every total dropped,
entirely out of block 3 (tools are priced in `tools_total_tokens`). Opus 4.8's 2,266 is a
quarter of Sonnet 5's 8,745, so "the 2.1.269 system prompt" was never one size either.
`sonnet-5/default`'s 8,745 is a corrected figure: the first capture read 8,664 with
`SendFeedback` and `EndConversation` missing — see
`notes/cc-2.1.269-upfront-roster-flag-flicker.md`.

