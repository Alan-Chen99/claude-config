# Codex greeting capture

2026-10-19, `codex-cli 0.163.0`, `gpt-6.1-sol`, low reasoning, configured CLI
`exec` in `/root/claude-config-work`. Answer: `Hello!`.

The [snapshot](system-prompt-snapshot/codex-gpt-6.1-sol/exec-say-hello/)
contains sanitized WebSocket frames, both terminal responses, CLI events,
new/original session logs, provenance/hashes, generated `prompt.md`, eleven
`tools/*.md` files and `summary.json`. Headers/credentials are excluded;
persistent account/device IDs are redacted. Linkage IDs remain.

## Token accounting

API counts include framing. Text estimates use `tiktoken 0.14.0 / o200k_harmony`;
this available OpenAI encoding is not a verified production tokenizer.

| Part | Text estimate | API input |
|---|---:|---:|
| Tools | — | 8,280 |
| Base instructions | 4,212 | 4,216 |
| Local Git/tone | 273 | 276 |
| Skill catalog | 1,473 | 1,473 |
| Permissions | 68 | 67 |
| Collaboration mode | 200 | 199 |
| Plugin recommendations | 247 | 247 |
| Multi-agent role | 530 | 534 |
| Delegation restriction | 52 | 56 |
| Global/project instructions | 1,892 | 1,895 |
| Environment | 97 | 97 |
| `say hello` | 2 | 6 |
| Assistant-output entry's input attribution | — | 2 |
| **Total** | **9,046 text-only** | **17,348** |

**Zero unattributed input tokens.** Output 6, reasoning 0, total **17,354**;
12,288 input tokens cached. `summary.json` also counts each tool's description
and JSON locally. Exact per-tool API costs are unavailable: tools are attributed
together. Compact tool JSON measures 9,455 tokens; its serialization differs
from the service's tool rendering.

`001-request.json` uploads tools and base instructions with `generate=false`.
Its response reports 12,498 input: 8,280 tools + 4,216 base + residual framing 2.
`003-request.json` sends five conversation messages, referring to that response
through `previous_response_id`; its 17,348 input includes inherited context.
Adding both usage totals counts the prefix twice and establishes no billing
conclusion. `store=false` coexists with request chaining. Parameters/transport
metadata remain visible, rather than being silently counted as prompt text.

## Sources and surprises

Paths below are relative to `/repos/codex/codex-rs/`, revision
`83086188ae0614bd882818ff1aa23f3194962012`. Binary/source build identity is
unproven; captured bodies establish installed behavior.

- Base: `models-manager/models.json`, selected model's
  `model_messages.instructions_template`, also in `~/.codex/models_cache.json`.
  Assembly: `prompts/src/model_instructions.rs`, `core/src/context/base_instructions.rs`.
  **Surprise:** “can you” authorizes action; text explicitly describes user
  frustration with confirmation and imposes extensive writing rules.
- Tools: `core/src/tools/spec_plan.rs`, `core/src/tools/code_mode/execute_spec.rs`;
  `core/src/client.rs` handles Responses Lite serialization/prewarm/chaining.
  **Surprise:** `functions.exec` embeds 6,478 tokens of descriptions/API declarations.
  Web/image instructions: `ext/web-search/web_run_description.md`,
  `ext/image-generation/imagegen_description.md`. Web rules require browsing for
  many topics and govern citations/copyright. Deferred tools are not fully exposed.
- Git/tone: this repo's `codex/config.toml`, linked into `~/.codex/`.
  **Surprise:** automatic commits are local configuration.
- Skills: `ext/skills/src/catalog_prompt.rs`, installed `SKILL.md` metadata.
  **Surprise:** 19 catalog entries accompany a greeting; no bodies are loaded.
  Seventeen other local skills were omitted for missing `description` metadata.
- Permissions: `prompts/src/model_messages/permissions.rs`,
  `prompts/src/permissions_instructions.rs`. Collaboration:
  `prompts/src/model_messages/collaboration.rs`; model metadata can override
  `collaboration-mode-templates/templates/default.md`.
- Delegation: `prompts/src/model_messages/multi_agent.rs`,
  `prompts/src/multi_agent_instructions.rs`. **Surprise:** delegation teaching
  is followed by a restriction against proactive delegation.
- Project/environment: `core/src/agents_md.rs`, `core/src/context/user_instructions.rs`,
  `core/src/context/world_state/environment.rs`. Global `~/.codex/AGENTS.md`
  and project `CLAUDE.md` fallback become user instructions.
- Plugins: `core/src/context/recommended_plugins_instructions.rs`.
  **Surprise:** recommendations for uninstalled plugins accompany a greeting.

## Verification and limits

`original-vscode-session.jsonl` preserves the earlier `test: say hello` session:
**18,507 input / 6 output**, larger catalog/permissions, no CLI recommendation
block. This is a CLI variant, not that host's exact wire replay. Its separately
counted text is 10,405 tokens (10,402 when joined). Missing wire tools/attribution
prevent an exact retrospective split; the [earlier report](../notes/codex-say-hello-prompt-map.md)'s
8,105-token gap is not a measured tools subtotal.

The renderer verifies base text, every input item, assistant content, response
linkage, CLI/session usage and attribution sums. Service tokenizer/rendering
and hidden instructions remain unobservable. Zero accounting residual does not
prove absence of hidden instructions.

## Reproduce

Use a new private scratch directory and unused port. Start the dedicated proxy:

```bash
CODEX_CAPTURE_DIR="$SCRATCH" mitmdump -q --listen-host 127.0.0.1 -p 19161 \
  -s docs/system-prompt-snapshot/capture_codex.py
```

In another shell:

```bash
HTTPS_PROXY=http://127.0.0.1:19161 HTTP_PROXY=http://127.0.0.1:19161 \
SSL_CERT_FILE="$HOME/.mitmproxy/mitmproxy-ca-cert.pem" \
codex exec -m gpt-6.1-sol --json 'say hello' < /dev/null > "$SCRATCH/exec.jsonl"
```

Stop the proxy after completion. It retains terminal events, not all response
deltas. Live configuration/authentication are used; normal caches may refresh.
Review prompt bodies for secrets; copy matching sanitized session logs/provenance.
Regenerate:

```bash
uv run --no-project --with tiktoken==0.14.0 python \
  docs/system-prompt-snapshot/render_codex.py \
  docs/system-prompt-snapshot/codex-gpt-6.1-sol/exec-say-hello
```

The renderer rejects changes to the observed two-request protocol/attribution.
