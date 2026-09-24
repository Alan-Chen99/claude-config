Piece: a section for this repo's README explaining which setting keeps subagents in the foreground and why. Register: doc.

(Reconstructed after the fact from the draft and the repo CLAUDE.md; the ai draft was written from the repo, not from this sheet.)

Facts:
- Goal: subagents default to foreground, or at least foreground is possible. On claude code 2.1.269 foreground subagents do not work by default (measured in a session, not from source).
- Chosen: `CLAUDE_CODE_FORK_SUBAGENT=0`. With it, foreground subagents work. Cost: the `fork` subagent type is gone.
- Mechanism (from source): the gate clears `forceAsync` and puts the `run_in_background` parameter back in the Agent tool schema; a call backgrounds unless the parameter is literally `false`.
- Rejected: `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`. Makes the foreground a harness guarantee and keeps `fork`, but removes the whole background-task facility: `run_in_background` leaves the Bash schema, a command outrunning its timeout is killed (exit 143) instead of backgrounded, the `BACKGROUNDED:` status line cannot fire. Judged the worse tradeoff.
- Enforcement: the system prompt instructs the agent to pass `false` on every Agent call; nothing enforces it. Measured on 2.1.269: 9 of 9 calls complied once the bullet was written as an instruction; 3 of 3 omitted it when the prompt only described the removed hook. Chosen over a hook to avoid maintaining one and to keep background subagents possible when needed.
