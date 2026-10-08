# A safety classifier stopped a response mid-turn; the log keeps no trace of what it stopped

Measured 2026-10-08, Claude Code **2.1.289**, opus-5-5, session `13b1bdb9`
(`/root/.claude/projects/-root-claude-config-work/13b1bdb9-*.jsonl`, @L1684–@L1709).

Two Bash tool results returned at @L1691; the session's next assistant response
was stopped by a safety classifier. What the JSONL holds:

- **No partial record.** The stopped response never reached the log — no
  assistant line exists between @L1691 and the notice @L1693. What was being
  written is unrecoverable, so the trigger can only be inferred from what the
  session says it was about to do, never read back.
- **cc's own record** (@L1692): `type: "system"`, `subtype: "informational"`,
  `level: "notice"`, `isMeta: false`, content *"Opus 5.5's safeguards stopped
  the response above · continuing once with that noted"*, timestamped the same
  millisecond as the notice.
- **The notice** (@L1693, user role, model-visible): *"Your response above was
  stopped by a safety classifier — this is not a tool or API error. The rest of
  it was withheld, and tool calls in it that had not finished did not run. Do
  not produce that content again, even reworded."*
- **One automatic continuation**: the informational record itself says
  *"continuing once"*, and the next assistant turn (@L1694) answers the notice.

## Reading it in cc-pretty

The default render and `--skeleton` hide @L1692: `is_model_visible`
(`src/claude_config/cc_pretty/main.py`) admits only `local_command` and `api_*`
system records, and the model saw the user-role notice, not cc's informational
line. `--show-all` rows it (`system:informational · 20~tok`). A reader of the
default skeleton finds the stop through @L1693's preview alone, which names the
cause just as plainly.

## This instance

The session had finished API-key recitation probes of the server-injected
browser-safety section (`docs/system-prompt-snapshot/server-injected/`) and was
composing a claude.ai-login arm: a replay request on the subscription OAuth
credential with the probe's system prompt in place of Claude Code's own, the
billing header and identity line kept so the OAuth gate passes
(`notes/cc-replay-oauth-system-prompt-gate.md`). Whether the classifier objected
to that construction or to reproducing the safety text in prose is not
determinable from the log. The session read the stop as its user's "stop and
tell me" condition, abandoned the OAuth arm and wrote nothing — which is why
the capture directory was committed by a later session. A stop condition
phrased about "the model refusing" fired here on the operator's own session
instead; the two are different signals and both warrant reporting.

## Hypothesis: the gate-bypass construction, not the reproduction

Recorded by the follow-up session (`a1d05327`) that verified the runs and
committed `server-injected/`. The trigger is not observable, so this is
weighting, not a finding.

- **For:** timing singles out the response's new element. Fragment-level
  reproduction of the section had already passed through this session for
  turns (@L1615–@L1691 — tool outputs, thinking, the assistant's own prose,
  the committed blog page), so quoting alone had been cleared in practice;
  what first appears in the stopped response is the OAuth arm's construction
  (and the notice says it carried unfinished tool calls).
- **For:** the constructed request keeps the real client's billing header and
  identity line so `/api/oauth/validate` passes while carrying a foreign
  system prompt — a non-Claude-Code request masquerading as Claude Code to an
  access control. The session's earlier OAuth replays, which drew no stop,
  were faithful replays of genuine captured requests (the trailing-cut gate
  probe included, `notes/cc-replay-oauth-system-prompt-gate.md`);
  whole-prompt replacement under preserved identity markers is different in
  kind. If the classifier keys on a pattern, the pattern is the conjunction:
  extract the internal safety text *by* evading the client-identity check.
- **Against / open:** a quantity threshold on reproduction is not excluded;
  the withheld bytes never reached the log, and @L1694 is the agent
  reconstructing its own intent, not a record of what was stopped.
- **Discriminating test, not run:** two arms on an Anthropic-powered
  session — reproduce the section in prose vs. describe/construct the
  gate-bypassing replay. Arm 2 stopping where arm 1 does not would confirm.
