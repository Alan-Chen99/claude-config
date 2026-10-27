# Session-start token cuts — decisions of 2026-09-30

Evidence: session `890f76e2` ("say hello", cc 2.1.269, claude-fable-5-1) wrote 38,266
tokens to cache on its first request, $0.83 for the session. Edits are to
`settings.json` unless stated.

| # | Decision | Change | Saves |
|---|---|---|---|
| 1 | SendFeedback off | `"feedbackDrafts": "off"` | 1,956 |
| 2 | Workflow kept | — | — |
| 3 | ReportFindings denied; `/code-review` reports as text | `permissions.deny` | 821 |
| 4 | ScheduleWakeup denied; self-paced `/loop` stops, interval `/loop` and Monitor stay | `permissions.deny` | 1,695 |
| 5 | ListAgents kept | — | — |
| 6 | All 14 bundled skills | `skillOverrides`: `name-only` for four, `user-invocable-only` for ten | ~2,250 |
| 7 | superpowers plugin kept (no per-hook disable in 2.1.269) | — | — |
| 8 | Other plugin skills | no-op: a plugin skill resolves `on` before `skillOverrides` is read (`src/chunk-pmgcy9dx.js:207`, probed live) | 0 |
| 9 | 16 repo skills meant to run only when named | `name-only` each | ~240 |
| 10 | Rule for name-only skills, #6 and #9 alike | `sys_prompt/alan-default-next.md`'s "listed without a description" sentence | — |
| 11 | session-analysis pair | shorten `description` in `skills/session-analysis/SKILL.md`; no local override | small |
| 12 | claude.ai connectors off by default | `env.ENABLE_CLAUDEAI_MCP_SERVERS: "false"`; job-search projects set `"true"` in `.claude/settings.json` (env merges per key, project over user, and the project-scope blocklist `src/chunk-by7kenyn.js:50` names neither variable; `disableClaudeAiConnectors` is any-source-true) | ~1,900 |
| 13 | Chrome off by default | `env.CLAUDE_CODE_ENABLE_CFC: "false"`; browser projects set `"true"`, or `claude.sh --chrome` | ~2,050 |
| 14 | Prompt suggestions kept | — | — |
| 15 | env-context hook drops `STASH_CAUTION` (cc's worktree block carries it since 2.1.269) | `env_context/render.py`, its upstream pin and test | ~150 |
| 16 | sys_prompt and the two loaded CLAUDE.md files | Kept; no cut scheduled | — |

Measured 2026-09-30 (`claude.sh -p "say hello"`, claude-fable-5-1, sessions `43d70525`,
`3301ff29`): 38,266 → 24,963 cache-write tokens, 27,285 with `--chrome`. Gone: five
tools, ten bundled skills, Chrome's guidance block with its tools; 16 repo skills bare.
