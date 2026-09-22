## Foreground subagents

We want the subagents to default to foreground, or at least allow foreground subagents. As of claude code 2.1.269, foreground subagents do not work by by default (measured, not from source).

Implemented workaround: using `CLAUDE_CODE_FORK_SUBAGENT=0`. With this foreground subagent "just works". Accepted tradeoffs: `fork`-typed subagents are not possible anymore.

Rejected alternative: `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`. That breaks background bash commands, which we considered a worse tradeoff.

Note: system prompt currently instructs the agent to pass `false` to the `run_in_background` parameter, to avoid maintaining a hook and to still allow background subagents in cases that needs it.
