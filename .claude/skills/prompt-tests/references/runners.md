# Runners

Invocations are in `SKILL.md`; this is what each runner sets, and where it
fails silently.

## Claude Code

`sys_prompt/alan-default-next.md` is written for Claude Code, and this runs it
there: `agent-tools claude -p`, so the session gets this checkout's hooks,
settings, and output style alongside the prompt. Read the script for what it
sets and why; each of its guards exits non-zero naming what to fix.

The one mechanic worth knowing outside it is `--thinking-display summarized`:
without it every thinking block in the transcript is an empty string while the
run still reports a thinking-token count, so a hand-rolled invocation that drops
the flag yields a log indistinguishable from an agent that did not reason.

**Confirm the arm on a resumed leg.** Claude Code applies the **last**
`--system-prompt-file`, which is how the arm file wins over the one
`scripts/claude.sh` passes — but only on a session's first request, since a
resume replays the recorded prompt. `prompt-test-cc-leg2.sh` passes
`--system-prompt-snapshot off` for that. When the MITM proxy is listening on
`127.0.0.1:9160`, the system block actually sent is at
`~/.claude/requests-log/<session>/0001.json`.

Not isolated: the user's `~/.claude/CLAUDE.md` reaches the agent as a `claudeMd`
system-reminder. It describes the machine and is identical across arms.

## opencode

Answers a different question — whether an effect survives a change of runner and
model family. Reach for it when a Claude Code result looks model-specific. Tool
names, hooks, and the agent-view fork behaviour are Claude Code's, so nothing the
prompt says about them is exercised here.

`PROMPT_TEST_MODEL` (default `openrouter/anthropic/claude-opus-5`, so a Claude
Code prompt is exercised by a Claude model) and `PROMPT_TEST_OUT_DIR` override.
The script refuses a prompt file starting with frontmatter, which `{file:...}`
would inject verbatim.

An agent file that *has* frontmatter — `opencode/agents/alan-default-ids.md` —
therefore has to be driven directly, with `model` and `variant` set in the config
block (`openai/gpt-5.5/xhigh` for `alan-default`). Full recipe:
`skills/opencode-subcommand`.

Three of its lines carry a failure that is silent when you get them wrong, and
one of the three is specific to this repo:

- **`model` and `variant` in the config block**, because `{file:...}` does not
  apply the agent file's frontmatter. Verify the rendered header with
  `agent-tools opencode-pretty <session-id> --agent`.
- **`PATH` and `CLAUDE_CONFIG_ROOT`.** `alan-default-ids` calls `agent-tools
  opencode.gate`, whose text is baked into the binary at build time, and
  `~/.local/bin/agent-tools` is the installed checkout's — so a worktree edit to
  the gate never reaches it and the change appears tested when it is not.
  Rebuild, put the worktree binary first on `PATH`, and read the gate text back
  out of it before trusting the run.
- **`"plugin": []`.** Both runner scripts pass it; a hand-rolled run must. No
  case here wants plugins loaded.

Two log caveats for this runner. The `--format json` stream is written
incrementally, so a log read mid-run can be missing the final text part —
`opencode export <session-id>` is the source of truth. And reasoning summaries
are not always emitted, so a grader told to read every thinking block may
correctly find none; check `info.tokens.reasoning` before recording coverage.
