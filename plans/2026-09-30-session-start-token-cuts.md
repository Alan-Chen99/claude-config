# Session-start token cuts — decisions of 2026-09-30

Evidence: session `890f76e2` ("say hello", cc 2.1.269, claude-fable-5-1) wrote 38,266
tokens to cache on its first request, $0.83 for the session. `count_tokens` marginals on
the capture `~/.claude/requests-log/890f76e2…/0003.json`: 13 upfront tools 12.8k ·
sys_prompt 6.6k · skill listing 5.7k · CLAUDE.md ×2 3.3k · superpowers hook 2.3k ·
Chrome 2.1k · claude.ai connectors 1.9k · agent listing 1.3k · env-context hook 0.8k.
Applied on `work3`, live once merged and installed; edits are to `settings.json` unless
stated.

| # | Decision | Change | Saves |
|---|---|---|---|
| 1 | SendFeedback off | `"feedbackDrafts": "off"` | 1,956 |
| 2 | Workflow kept | — | — |
| 3 | ReportFindings denied; `/code-review` reports as text | `permissions.deny` | 821 |
| 4 | ScheduleWakeup denied; self-paced `/loop` stops, interval `/loop` and Monitor stay | `permissions.deny` | 1,695 |
| 5 | ListAgents kept | — | — |
| 6 | All 14 bundled skills | `skillOverrides`: `name-only` for dataviz, claude-api, workflow-authoring, claude-in-chrome; `user-invocable-only` for the other 10 | ~2,250 |
| 7 | superpowers plugin kept (no per-hook disable in 2.1.269) | — | — |
| 8 | Other plugin skills | no-op: the mode resolver returns `on` for `source === "plugin"` before reading `skillOverrides` (`src/chunk-pmgcy9dx.js:207`), probed live | 0 |
| 9 | The 16 repo skills described "use only if invoked by user or workflow" | `name-only` each | ~240 |
| 10 | Rule for name-only skills, #6 and #9 alike | `sys_prompt/alan-default-next.md`: a skill listed without a description is invoked only when the user or a workflow names it | — |
| 11 | session-analysis pair | shorten `description` in `skills/session-analysis/SKILL.md`; no local override | small |
| 12 | claude.ai connectors off by default | `env.ENABLE_CLAUDEAI_MCP_SERVERS: "false"`; job-search projects set `"true"` in `.claude/settings.json` (env merges per key, project over user; `disableClaudeAiConnectors` is any-source-true) | ~1,900 |
| 13 | Chrome off by default | `env.CLAUDE_CODE_ENABLE_CFC: "false"`; browser projects set `"true"`, or `claude.sh --chrome` | ~2,050 |
| 14 | Prompt suggestions kept | — | — |
| 15 | env-context hook drops `STASH_CAUTION` (cc's worktree block carries it since 2.1.269) | `env_context/render.py`, its pin in `scripts/check-prompt-upstream.py`, `tests/test_env_context.py` | ~150 |
| 16 | sys_prompt and CLAUDE.md | no cut scheduled | — |

Measured 2026-09-30 (`claude.sh -p "say hello"`, claude-fable-5-1, sessions `43d70525`,
`3301ff29`): 38,266 → 24,963 cache-write tokens, 27,285 with `--chrome`. Five tools off
the roster, ten bundled skills gone, 16 repo skills bare, Chrome's guidance block gone
with its tools. The project-scope env blocklist (`src/chunk-by7kenyn.js:50`) names
neither variable, so a project can set either back.
