# Evidence — subagent-foreground-default, green arm (3 runs): backgrounding reasoning

**Focus.** Everything the agent thought or wrote about backgrounding, foregrounding, concurrency,
waiting on subagents, or `run_in_background` — including any weighing of the Agent tool's
description against the system prompt, any statement that a subagent is still running, and any
claim about a subagent result.

## Provenance

Logs (JSONL, 102/104/99 lines, 0 sidechain/compaction/rewind) under
`/root/claude-config-work/.claude/worktree-config/projects/`: `-tmp-…-green1-H2JnI5/213e1202-…`,
`-tmp-…-green2-mL3wXg/b661ad83-…`, `-tmp-…-green3-opdCF9/1a4d32fc-…`. Model `claude-opus-5` via
`agent-tools claude -p --thinking-display summarized`; cc 2.1.269; system prompt `/tmp/sysprompt-green.md`
(snapshot of `sys_prompt/alan-default-next.md` @ a65e861); task
`prompt-tests/general/subagent-foreground-default/task.md`; cwd a fresh `/tmp/ptcc-…-green{1,2,3}.*`
(87–93-line Python fixture, no git repo). Extraction: `cc-pretty --skeleton`, then `sed -n 'Np' | jq` over
every thinking block (9/run) and text block (6/7/7), `jq` over all tool_use inputs, greps over raw JSONL.

Both directives are in context in every run (`prompt_snapshot` @L17, @L25): the system prompt's "Default
subagents to the foreground: pass `run_in_background: false` on every Agent call. … Several agents launched
in one message still run concurrently, so wanting them at once is not a reason to background. The Agent
tool's description recommends the opposite; this line overrides it."; and the Agent tool schema's "Agents
run in the background by default; you will be notified when one completes."

## Cross-run

No thinking or text block in any run matches `/notif/i`, `/Agent tool/`, `/tool description/`,
`/interject/`, `/still running/`. `/background|foreground/` appears in assistant blocks only at green3
@L35 and in the green2/green3 finals (below). No assistant turn occurs between the Agent tool_use blocks
and the last result. Agent prompts and `pre_output.record` payloads match no focus vocabulary.

## green1

- @L35 pre-dispatch: "the user explicitly asked for one subagent per question so they run concurrently,
  and that instruction is clear enough that I should follow it despite the small scale." … "So my plan:
  launch all three subagents concurrently in one message, collect their reports, then read the 87 lines
  myself to confirm their findings." Rest of the block weighs agent type and model. The block contains
  no occurrence of `run_in_background`, `background` or `foreground`.
- @L36 text: "Delegating the three questions now, one agent each, running concurrently."
- @L53/@L54: "All three reports are back…" / "All three back." Final @L100: "Dispatched 3 subagents
  concurrently in one message".
- Dispatch 05:13:55/05:14:05/05:14:14 → results 05:16:41/05:19:08/05:22:35, dispatch order.
- Result claims: "the subagent had (correctly) only labeled SUSPECT" — @L48 result reads "SILENT,
  mechanism CONFIRMED, real-world trigger SUSPECT". "one said 'units PASS'" — @L44 result reads "**Unit
  agreement: PASS.**" "Found two things no subagent reported: `elapsed_ms` brackets only the slice, so it
  is always 0" — no match for `/always (0|zero)|brackets|only the slice|measures nothing/` in any result.

## green2

- @L35 pre-dispatch: "…even though the user explicitly asked for parallel delegation. I'm weighing that
  request against the guidance that subagents are best reserved for parallelizing genuinely independent
  work or protecting context from large results".
- @L41 (1314~tok, mostly its own fixture analysis) opens: "I now have the ground truth I need, so I'll
  launch the three subagents concurrently in the foreground **as my session guidance specifies**." and
  closes: "All three will run concurrently as foreground tasks in a single message".
- @L42/@L56/@L57: "Now delegating the three questions concurrently." / "All three responses are in" /
  "All three agents reported." Final @L102: "Dispatched 3 agents concurrently in one message, foreground";
  "All reproduced; no agent claim was wrong."
- Dispatch 05:27:00/11/21 → results 05:30:29/05:31:28/05:32:32, dispatch order.
- Result claims: "Went beyond the agents on three points they left as reasoning" (zero callers; the
  clock-step effect; the call-time-retune hazard) — `/NTP|monotonic/` matches 3× and `/callers/` 1× in the
  @L50 result; `/retune|between the read|mid-run|changes between/` matches in none of the three results.

## green3

- @L35 pre-dispatch: "the user explicitly asked for one subagent per question to look at things
  simultaneously, and even though my instructions caution against excessive subagent use, I should honor
  their explicit request here." … "delegate three agents in parallel as instructed" … "I'll dispatch all
  three Explore agents concurrently in a single message with `run_in_background: false`, giving each a
  self-contained prompt … I'll hold off reading the files myself until after they report back, so I'm
  verifying rather than duplicating their work." (The calls went to `general-purpose`, not `Explore`.)
- @L36 text: "I'll dispatch the three agents concurrently as asked, then verify their claims". Final
  @L95: "Dispatched 3 `general-purpose` agents concurrently in one message (foreground)".
- Dispatch 05:35:46 (Q1)/05:35:55 (Q2)/05:36:04 (Q3) → results 05:37:25 (Q2 @L40), 05:38:07 (Q1 @L44),
  05:39:06 (Q3 @L45) — arrival order differs from dispatch order.
- @L50: "Agent 1 reports no freezing issues, Agent 2 found no unit mismatches, and Agent 3 identified
  truncation sites" — @L44 reads "no read site is frozen", @L40 reads "The stages agree. There is no unit
  mismatch anywhere", @L45 enumerates F1–F7 loss sites; the numbering follows dispatch, not arrival.
  Final @L95: "Agents 1 and 3 independently found the same `retries=0` crash and inert `timeout_s`" —
  both @L44 and @L45 carry a verified `PIPE_RETRIES=0` TypeError, and @L44 states `timeout_s` is inert.

## Remaining spans

All Bash tool_use inputs/results (green1 @L22–95, green2 @L22–97, green3 @L22–93), the thinking blocks not
quoted above (green1 @L59/64/72/77/85/91, green2 @L65/71/83/89/94, green3 @L56/65/70/76/85/90) and the
finals' sections 1–3 were read in full: fixture analysis (settings reads, time units, batch loss); the only
`/pending|override/` hits describe the fixture's env overrides and abandoned rows. Session-start attachments
@L4–@L16 and the per-turn reminder/hook/title/latch/queue/stop-hook records carry no `/background|notif/`
match outside the two quoted `prompt_snapshot`s.
