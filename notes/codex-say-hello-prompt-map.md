# Codex’s prompt for “say hello”

2026-10-19, **gpt-6.1-sol**, codex **0.163.0**, default mode, low reasoning. `test: say hello` → `Hello!`, no tools. **Input: 18,507 tokens**, including 12,160 cached; output: 6; reasoning: 0.

Evidence: [rollout](</root/.codex/sessions/2026/10/19/rollout-2026-10-19T02-52-07-01a15212-d198-7ad3-90aa-fda77b7f5be9.jsonl>) (`L` = physical line). Source `/repos/codex` at `83086188ae0614bd882818ff1aa23f3194962012`. Cwd: `/root/claude-config-work` (VS Code).

## Parts and counts

Counts: **tiktoken 0.14.0, `o200k_harmony`**, **approximate for GPT-6.1**. Logged total is authoritative.

| Part | Tokens | Evidence |
| --- | ---: | --- |
| Builtin model base (developer) | 4,212 | L1 `.payload.base_instructions.text` |
| Your Git policy/tone markers (developer) | 273 | Start of L3 |
| Skills catalog: 29 descriptions/paths/root aliases (developer) | 2,342 | L3 `<skills_instructions>`; no bodies loaded |
| Permissions/escalation policy (developer) | 803 | L3 `<permissions instructions>` |
| Default collaboration mode (developer) | 200 | L3 `<collaboration_mode>` |
| Multi-agent role, four slots, fork/tool rules (developer) | 530 | L4 |
| Explicit-request-only delegation policy (developer) | 52 | L5 |
| Global/project AGENTS instructions (user) | 1,892 | L6 through `</INSTRUCTIONS>` |
| Environment: cwd/shell/date/timezone/filesystem (user) | 97 | Remaining L6 |
| `test: say hello` (user) | 4 | L10 |
| **Sum of separately tokenized parts** | **10,405** | Includes split-boundary effects |
| **Sum after concatenating each message’s text** | **10,402** | Base 4,212; L3 3,616; L4 530; L5 52; L6 1,988; L10 4 |
| **Unresolved remainder** | **8,105** | Reported total minus preceding row |
| **Complete input, reported** | **18,507** | L15 `.payload.info.last_token_usage.input_tokens` |

`say hello`: 2 tokens.

**8,105 is an unresolved remainder:** tools, service-added instructions, framing and tokenizer differences may contribute. No full wire/backend prompt was captured; individual counts remain unknown.

## Builtin source map

Under `/repos/codex/codex-rs/`:

| Part | Source |
| --- | --- |
| Base | `models-manager/models.json`: `gpt-6.1-sol` → `model_messages.instructions_template`; selected by `prompts/src/model_instructions.rs` |
| Base role/request serialization | `core/src/context/base_instructions.rs`, `core/src/client.rs` |
| Skills catalog/body loading | `ext/skills/src/catalog_prompt.rs`, `ext/skills/src/host_prompt.rs` |
| Permissions composition | `prompts/src/permissions_instructions.rs`, `prompts/src/model_messages/permissions.rs` |
| Permission templates | `prompts/templates/permissions/sandbox_mode/danger_full_access.md`, `prompts/templates/permissions/approval_policy/on_request.md` |
| Collaboration selection/fallback | `prompts/src/model_messages/collaboration.rs`, `collaboration-mode-templates/templates/default.md` |
| Multi-agent selection/composition | `prompts/src/model_messages/multi_agent.rs`, `prompts/src/multi_agent_instructions.rs` |
| AGENTS/environment | `core/src/agents_md.rs`, `core/src/context/user_instructions.rs`, `core/src/context/world_state/environment.rs` |
| Tool assembly/definitions | `core/src/tools/spec_plan.rs`, `core/src/tools/handlers/`, `core/src/tools/code_mode/` |

The 21,769-character base matches the checkout catalog and `~/.codex/models_cache.json` **byte for byte**; the old `core/gpt*_prompt.md` files are not its source. The base is serialized as a **developer** message. Active collaboration text matches the cached catalog; the checkout catalog differs, so its fallback cannot establish historical wording.

Local Git/tone: `codex/config.toml`, `developer_instructions`. Global `~/.codex/AGENTS.md` → `/workspace/docker/claude-home-CLAUDE.ionos.md`; project `CLAUDE.md` loads via your fallback. Skill/plugin roots: L3; host tools can originate outside this tree.

## Instructions that may surprise you

Present even for the greeting:

- **Builtin:** says “The user gets very frustrated” with permission questions; requires authorized preparation before seeking approval.
- **Builtin:** interprets “can you…” as an action request; urges persistence, potentially creating worktrees/draft PRs.
- **Builtin:** discourages headings, named words, contrastive phrasing and unnecessary apologies; prefers interactive visuals when useful.
- **Builtin:** requires announcing skill use; an explicitly invoked skill can authorize messaging other people (conditional).
- **Catalog:** spends 2,342 tokens advertising skills including animated pets and Google Slides.
- **Team policy:** teaches delegation, then separately restricts spawning to explicit user/AGENTS/skill requests.
- **Permissions:** includes extensive escalation advice alongside full filesystem/network access; approval policy remains on-request.
- **Your config:** commits completed changes with a session trailer. This is not builtin policy.
- **Your config:** auto-loads project `CLAUDE.md` despite that file’s statement that it is not auto-loaded.

## Verification

Read five input messages/answer and inspected 16 records. No compaction/rewind. L7–9 state/settings are **not extra prompt copies**.

Runtime corroboration: `~/.codex/logs_2.sqlite`, rows 11557 (low reasoning), 11665 (18,513 total).

Recount: tokenize L1’s base, then concatenated `.payload.content[].text` per L3/L4/L5/L6/L10 using `tiktoken.get_encoding('o200k_harmony').encode(text, disallowed_special=())`. Split L3 at the three wrapper openings and L6 at `<environment_context>` for the component table. Read usage at L15.
