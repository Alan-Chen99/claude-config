# Round 34 — Why gpt-5.5 and kimi-k3 diverge on crossing behavior (wire-level diff)

> **Direct predecessor: [`round-33.md`](./round-33.md).** R33 established that (a) kimi cells cross 1-3× and import old-worktree vocabulary; (b) gpt-5.5 cells codified-skip via demotion/deletion with zero crossings; (c) F103 self-report from 6 forks says gpt-5.5's skip is "absence not override". R33's kimi n=1 sanity check confirmed the followup format elicits accurate self-reports (3/3 citations verified). The remaining question: **what actually differs between the two models' inputs that could produce this divergence?** R34 investigates by capturing wire-level requests from both providers.

## Method

Rebuilt opencode from source (`/repos/opencode` at commit `c675fe184` — F62 wire-level instrumentation) via `bun run --cwd packages/opencode --conditions=browser src/index.ts` since the installed nix binary `1.15.5+7dcdc3d` predates the F62 hooks. Set `OPENCODE_F62_LOG_DIR=/tmp/f62-probe` to enable request capture at `provider.ts:1567` (pre-Codex-rewrite) AND `plugin/codex.ts` (post-rewrite).

Ran two minimal probes: agent prompt = *"You are a helpful assistant. Answer briefly."*, user message = `"Hi."`, no tools permitted. Model 1 = `openai/gpt-5.5` xhigh. Model 2 = `opencode-go/kimi-k3`. Same env vars, same `OPENCODE_CONFIG_CONTENT`, same disable-flags (`OPENCODE_DISABLE_PROJECT_CONFIG=1`, `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1`).

Diffed the captured request bodies (`/tmp/f62-probe/*.req`).

## Findings — what's the same

**Visible system-prompt content is bit-identical except for one line.**

`diff /tmp/gpt-instructions.txt /tmp/kimi-instructions.txt`:
```
2c2
< You are powered by the model named gpt-5.5. The exact model ID is openai/gpt-5.5
---
> You are powered by the model named kimi-k3. The exact model ID is opencode-go/kimi-k3
```

Both instructions strings are 7278/7283 chars (5-char diff = length of the model-name string difference). Everything else — agent prompt content, `<env>` block, `<available_skills>` list (30+ skills), the same paragraph telling the model to load skills, all identical bit-for-bit.

## Findings — what differs

Four axes of difference, only one of which is a plausible behavioral driver.

### 1. Endpoint and API format (structural)

| | gpt-5.5 | kimi-k3 |
|---|---|---|
| Endpoint | `chatgpt.com/backend-api/codex/responses` (Codex OAuth via plugin rewrite from `api.openai.com/v1/responses`) | `opencode.ai/zen/go/v1/chat/completions` |
| API family | OpenAI Responses API (`input`, `instructions`) | Chat Completions (`messages`) |
| Tool schema | `{type,name,description,parameters}` (flat) | `{type,function:{name,description,parameters}}` (nested) |

Structural difference; not a behavioral cause on its own.

### 2. **Text verbosity default (candidate causal driver)**

At `/repos/opencode/packages/opencode/src/provider/transform.ts:1140`:

```typescript
if (input.model.api.id.includes("gpt-5.") &&
    !input.model.api.id.includes("codex") &&
    !input.model.api.id.includes("-chat") &&
    input.model.providerID !== "azure") {
  result["textVerbosity"] = "low"
}
```

**All gpt-5.x models (except gpt-5-codex, gpt-5-chat, azure) get `text.verbosity: "low"` hardcoded** by opencode's transform layer. There is no user-facing config to override this. The variant setting (`xhigh` in R30) controls `reasoningEffort`, not `textVerbosity` — the two are orthogonal.

**Kimi-k3 gets no verbosity setting.** Kimi does not match any branch in the transform function that adds verbosity, top_p, or temperature (kimi-k2 gets temp=0.6/1.0, but kimi-k3 does not match `id.includes("kimi-k2")`).

Wire-level confirmation from the probe:
- gpt-5.5 request body: `"text": {"verbosity": "low"}` present
- kimi-k3 request body: no `text` field, no `verbosity` field

**Behavioral implication**: OpenAI's `text.verbosity: "low"` parameter biases the model toward brief, direct output. In agent contexts, brevity often extends to fewer exploratory tool calls — "just answer" competes with "gather context first". This is a plausible client-side driver of gpt-5.5's *"PROMPT.md is stale → rewrite it"* pattern vs kimi's *"let me check the prior worktree for context first"* pattern.

### 3. Reasoning parameters (structural + F62)

| | gpt-5.5 | kimi-k3 |
|---|---|---|
| `reasoning.effort` | `"xhigh"` (from user variant) | (not set) |
| `reasoning.summary` | `"auto"` — but Codex backend reduces to headings only (F62) | (not set — kimi produces reasoning-content its own way) |
| `include: ["reasoning.encrypted_content"]` | yes (prompt-cache reuse) | no |

F62 is a *measurement* confound (we can't see gpt-5.5's full internal deliberation), not a behavioral cause. But the fact that we can't see gpt-5.5's reasoning means we cannot rule out that motivations surface internally there and are dismissed without visible trace — which was the F103 confound in R33.

### 4. Server-side backend policy (opaque)

The Codex OAuth backend (`chatgpt.com/backend-api/codex/responses`) is a distinct product from OpenAI's public Responses API. It applies its own server-side policies:

- **Verified F62 policy**: reduces `reasoning_summary_text` to single bold headings (~39 chars mean).
- **Suspected but unverified**: the Codex backend may apply additional prompt content or behavioral biases beyond what we see in the client-side request. Codex CLI is designed as an action-oriented terminal engineer; if similar biases are injected server-side, they would show up as gpt-5.5-specific behavior on Codex OAuth even with identical client-side requests.

To test this, one could route the same probe through the public OpenAI API (`OPENCODE_AUTH_CONTENT` API-key override per opencode-subcommand skill C1 mitigation) and compare with Codex OAuth. Not run in R34.

## Answer to the user's question

**Yes, the prompts are essentially the same.** The visible system prompt content is bit-identical except for a single line stating the model name. The agent prompt, `<env>` block, skills list, and user task are all identical.

**The defaults that differ, in order of behavioral relevance**:

1. **`text.verbosity: "low"`** — hardcoded default for gpt-5.x models in opencode's transform layer, no user-facing override. Biases toward brief output; plausibly biases toward fewer exploratory reads. **Candidate causal driver.**

2. **Codex backend policy (server-side)** — Codex OAuth endpoint applies verified F62 summary-reduction and possibly other unverified behavioral shaping. **Candidate causal driver; not directly testable without endpoint swap.**

3. **API format** (Responses vs Chat Completions) — structural; no direct behavioral impact.

4. **Reasoning-summary encoding** — measurement confound (limits *our* visibility), not behavioral driver.

## F104 — hardcoded gpt-5.x verbosity default in opencode (new)

`/repos/opencode/packages/opencode/src/provider/transform.ts:1129-1148` sets `textVerbosity: "low"` for all gpt-5.x models except gpt-5-codex, gpt-5-chat, and Azure. This is a default hardcoded by opencode, not by OpenAI's API defaults and not by user config. The variant setting (xhigh/high/medium/low) controls `reasoningEffort`, orthogonal to `textVerbosity`. Kimi-k3, kimi-k2-thinking, and other non-gpt-5 models do not receive this setting.

Load-bearing implications:
- Any prior gpt-5.5-vs-other-model behavioral comparison in this note-corpus (R11 onward — since gpt-5.5 became the primary probe model) has been confounded by this default.
- Any R30 finding that reads as "gpt-5.5 is more action-oriented / less exploratory" than kimi/DeepSeek/Qwen may be partly attributable to `textVerbosity: "low"` rather than model-family character.
- The finding is **testable**: patch transform.ts to strip the setting, rebuild opencode, rerun R30 kimi-baseline-broken-equivalent on gpt-5.5, compare crossing behavior.

## F105 — provider-prompt SKIP when agent supplies its own prompt (revised)

**Initial R34 draft claim was wrong.** opencode DOES inject different provider prompts per model family — but only when the agent config lacks a `prompt` field. The mechanism is at `/repos/opencode/packages/opencode/src/session/llm.ts:116`:

```typescript
// use agent prompt otherwise provider prompt
...(input.agent.prompt ? [input.agent.prompt] : SystemPrompt.provider(input.model)),
```

Either/or, no merge. If the agent has a `prompt`, that prompt is used and the provider-specific prompt is **entirely skipped**.

The provider prompts (from `/repos/opencode/packages/opencode/src/session/system.ts:19-33`):
- `gpt-4 / o1 / o3` → `PROMPT_BEAST` (11080 chars)
- `gpt-codex` → `PROMPT_CODEX` (7390 chars)
- other `gpt-*` (including gpt-5.5) → `PROMPT_GPT` (9284 chars)
- `gemini-*` → `PROMPT_GEMINI` (15372 chars)
- `claude*` → `PROMPT_ANTHROPIC` (8212 chars)
- `trinity` → `PROMPT_TRINITY` (7748 chars)
- `kimi*` → `PROMPT_KIMI` (8695 chars)
- fallback → `PROMPT_DEFAULT` (8528 chars)

Content differences are substantial. `gpt.txt` opens *"You are OpenCode... a deeply pragmatic, effective software engineer... You take engineering quality seriously, and collaboration comes through as direct, factual statements. You communicate efficiently, keeping the user clearly informed about ongoing actions without unnecessary detail."* — a brevity-and-action bias. `kimi.txt` opens *"You are OpenCode, an interactive general AI agent... Your primary goal is to help users with software engineering tasks by taking action... default to taking action with tools."* — an action bias but no brevity-or-quality axis.

**But in R30's setup** the agent config was `"prompt": "{file:...identity-outcome-clean.md}"` — so `input.agent.prompt` was truthy, and the provider prompt was SKIPPED for both gpt-5.5 and kimi-k3. R30 sessions saw:
1. Agent prompt (identity-outcome-clean.md) — same content for both
2. `SystemPrompt.environment()` output — model-name line (differs) + env block (same)
3. `SystemPrompt.skills()` output — skills list (same)

No provider-prompt content in either session. My F62 probe confirms this shape (both instructions strings are 7278/7283 chars — matches agent-prompt + env + skills, no additional provider content).

**Corrected F105**: opencode's `agent.prompt` REPLACES the provider prompt entirely — no merge. When R30's identity-outcome-clean.md was in play, both models saw the same content minus the model-name line. When no agent.prompt is set (e.g., default `chat` agent, or when the config omits `prompt`), models see different provider prompts with distinct behavioral biases (gpt-family gets brevity/quality framing; kimi-family gets action-only framing). This is a hidden trap: any user who assumes "same agent config = same system prompt across models" is right only when `agent.prompt` is set.

**Implication for R34**: F105's original claim ("no provider-conditional prompt content in opencode probe setups") is correct FOR R30's inline-agent-prompt setup, but incorrect as a general opencode statement. Behavior divergence between gpt-5.5 and kimi-k3 in R30 is genuinely NOT driven by provider-prompt content (both were skipped). Testable next: run the same identity-outcome-clean.md as a `.opencode/agents/*.md` file (loaded via `agent.load()`) vs inline — should be identical since both paths result in `agent.prompt` being set.

## Open (carried into round 35+)

- **F104 causal test.** Patch transform.ts to remove `textVerbosity: "low"` for gpt-5.5, rebuild opencode, rerun R30 kimi-baseline-broken-equivalent task on patched gpt-5.5. If crossing emerges → verbosity was causal. If no crossing → the driver is either Codex backend server-side or model-family training.
- **F62 backend-swap causal test.** Same as above but with `OPENCODE_AUTH_CONTENT` API-key override → route through public API `api.openai.com/v1/responses`. If crossing emerges on public API with same client-side settings → Codex backend server-side was causal. If not → verbosity or model.
- **Cross-model kimi-k2-thinking / qwen probes.** Both have visible reasoning like kimi-k3. If they also cross (like kimi-k3), the crossing behavior is a general "verbose-model + no-verbosity-cap" pattern. If they don't, kimi-k3 is idiosyncratic.
- **Retroactive R30 correction candidate.** If F104 test confirms verbosity causality, R30's F5/F6/F8 gpt-5.5-vs-kimi comparisons should be footnoted with the confound and re-evaluated under matched-verbosity conditions.

## Methodological notes

- **Rebuild path**: `nix shell nixpkgs#bun -c bun run --cwd packages/opencode --conditions=browser src/index.ts run --agent <name> ...` runs opencode directly from source. Necessary when the installed binary lacks F62 hooks. First run is slow (~10-30s of bun startup) but works identically to the installed binary otherwise.
- **F62 capture setup**: set `OPENCODE_F62_LOG_DIR=<dir>` before invoking. Files pattern `<epoch>-<slug>-<provider>-<model>.req`/`.res`. For Codex-OAuth requests, additional `*CODEX*.req`/`.res` files capture the post-rewrite state (URL + Bearer header updated). For non-OAuth requests, only pre-rewrite `.req` files appear.
- **First-request-is-title-generator**: opencode's first API request per session is a call to a title-generator agent (hardcoded instructions to output a single-line thread title). The real user probe is the SECOND request. Diff the 21KB requests, not the 3KB ones, for actual agent behavior.
