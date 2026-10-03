# Fable and Mythos: which model ids answer, and what prompt they get

> **Dated record.** Claude Code **2.1.269**, one account, one capture session
> (2026-09-11, re-derived 2026-09-30). Every figure and `src/chunk-*.js` citation
> is that build's: do not re-pin them, re-measure. The artifacts are
> `docs/system-prompt-snapshot/<model-id>/<variant>/`, whose `README.md` carries
> the capture procedure.

2.1.269's model registry carries `claude-fable-5`, `claude-fable-5-1`, `claude-mythos-5` and
`claude-mythos-5-1`. `fable-5/default` is captured; the account's entitlement changed
mid-investigation — a request to `claude-fable-5` returned HTTP 429, `"Fable 5 requires usage
credits..."`, while a `claude-sonnet-5` control in the same minute succeeded, and after the
upgrade the same id captured normally. `claude-fable-5-1` and `claude-opus-4-8` answer too;
`claude-mythos-5` returns HTTP 404, `"There's an issue with the selected model
(claude-mythos-5). It may not exist or you may not have access to it."` — absent rather than
gated.

`fable-5/default`: `model: claude-fable-5`, 4 blocks, **3,556** `system_tokens`, 14 upfront
tools / 18 deferred (`tools_total_tokens` 30,287), `thread: {"type":"create"}`,
`output_config: {"effort":"high"}`, `thinking:{"type":"adaptive","display":"updates"}`, no
`fallbacks` key — every one matching `opus-5/default`, tool roster included (all 15 `tools[]`
entries byte-identical text; `opus-4-8/default` matches too, at the same 30,287), so tools are
uniform across the compressed branch even where the prompt text is not. Fable-5 sits on the
compressed branch with opus-5, settled empirically rather than from the registry's
`lean_prompt` capability.

The `# Environment` block's self-description — `"The most recent Claude models are the Claude
5 family and Haiku 4.5. Model IDs — Fable 5.1: 'claude-fable-5-1', Opus 5: 'claude-opus-5',
Sonnet 5: 'claude-sonnet-5', Haiku 4.5: 'claude-haiku-4-5-20251001'"` — names
`claude-fable-5-1`, not the `claude-fable-5` that captured here, and never mentions
`claude-opus-4-8`, `claude-mythos-5` or `claude-mythos-5-1`; 2.1.235 named `claude-fable-5`.
The self-reported roster undersells the registry.

Separately: a `regenerate.py --model claude-fable-5 default` run from before the entitlement
upgrade was reported to have produced a capture whose `request.json` carried `model:
claude-sonnet-5` but the compressed `# Harness` prompt at 3,557 system tokens — the prompt
built for the *requested* model, the id reflecting the model billed. Not in this tree and
unverifiable from disk; the warning stands: **the `model` field in a captured `request.json`
does not always identify the model the prompt was built for.**

