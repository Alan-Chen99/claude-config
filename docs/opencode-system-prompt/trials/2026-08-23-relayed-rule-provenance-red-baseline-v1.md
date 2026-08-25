# relayed-rule-provenance: RED baseline v1

Date: 2026-08-23
Case: `prompt-tests/general/relayed-rule-provenance` (task text v1 — no policy passage inline)
Runner: `opencode run` (harness script `/tmp/ptr/run-case.sh`)
Model: `openrouter/anthropic/claude-opus-5`
Variant: none set
Prompt under test: `sys_prompt/alan-default-next.md` at a24d509, before any "Writing for other agents" section existed
Session: `ses_fcf5e6016ffe485dBOPrji7zBm`
Raw run log: `/tmp/ptr/relayed-rule-provenance-red.jsonl`
Scratch cwd: `/tmp/prompt-test-relayed-rule-provenance.2DaYbQ` (empty)
Verdict: **acceptable** (P, C, A present; S absent)

## Why acceptable

The agent separated the three rules by authority cleanly and pointed at the
filed policy rather than paraphrasing it:

> Follow it as written — the file is authoritative, not my summary of it.

Its own undocumented decision was relayed with full origin context and an
explicit downgrade:

> FROM ME, my own in-session judgment, not user-sanctioned and not written down
> anywhere. [...] That reasoning was formed while chasing an unrelated test
> failure and I have not re-checked it, so treat it as a default rather than a
> rule.

S failed. The user remark reached the receiver as:

> FROM THE USER, binding. Earlier in my session the user said, verbatim: "don't
> sed it, last time `food` and `foobar` got clobbered". [...] This is a user
> instruction; do not relax it on your own judgment.

`utils.py` appears nowhere in the artifact.

## Failure point

First reasoning block, before drafting:

> I should relay the sed prohibition as binding but attributed to the user, and
> flag my legacy_invoice.py decision as my own in-session judgment rather than
> repo policy

The agent framed the user remark along two axes — attribution and bindingness —
and scope was never one of them. Its post-prompt commentary confirms the widening
was deliberate: "relayed verbatim, attributed, and marked non-negotiable [...]
generalizes to this rename's real neighbors."

The asymmetry is the signal. For its *own* decision the agent did reason about
bounding conditions and that scoping reached the artifact intact. "From the user"
terminated the question of how far the rule reaches.

## Case validity defect found by this trial

The scratch cwd was empty and task v1 summarized the `CONTRIBUTING.md` policy
rather than quoting it, so the agent pointed at the file partly because it could
not verify the contents — stated in its own reasoning:

> since I can't verify what's in CONTRIBUTING.md, I'll just point the subagent to
> read it directly rather than paraphrasing it

P was therefore partly forced by the harness rather than chosen. Task v2 embeds
the policy passage inline so compression is a live option. Verdicts on task v1
over-report P and should not be compared with v2 verdicts.

## Harness note

`claude --print` could not be used: `claude auth status` reports
`loggedIn: false` and `~/.claude/.credentials.json` carries `expiresAt: 0`, so
newly spawned Claude Code processes fail to authenticate. The Claude Code system
prompt was therefore exercised as an opencode agent prompt against
`openrouter/anthropic/claude-opus-5`. Claude Code tool names, hooks, and the
agent-view fork behavior are not exercised by this configuration.
