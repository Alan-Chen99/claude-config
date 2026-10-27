# claude-config

[![CI](https://github.com/Alan-Chen99/claude-config/actions/workflows/ci.yml/badge.svg)](https://github.com/Alan-Chen99/claude-config/actions/workflows/ci.yml)

My Claude Code, Codex and opencode configuration, and the tooling built around it.
It began as a fork of [solatis/claude-config](https://github.com/solatis/claude-config)
and grew a Rust harness (`agent-tools`), a replacement system prompt with its
reasoning kept beside it rather than inside it, a prompt-evaluation corpus, and
a set of measured investigations into what the harness actually does.

## Status

A personal configuration, published to show the ideas rather than to be
installed: `install.sh` assumes one host layout, so read it before running it
anywhere, and nothing here is versioned or packaged for anyone else. Claude
Code moves quickly, so every measurement below carries its date and, where it
depends on one, the Claude Code version. [`CLAUDE.md`](CLAUDE.md) indexes every
directory, with when to read what.

## Codex

[`codex/config.toml`](codex/config.toml) is the Codex user config and
[`scripts/codex.sh`](scripts/codex.sh) its launcher; `install.sh` links both
(Install, below). Settings: [official OpenAI configuration reference](https://developers.openai.com/codex/config-reference/).

## Ideas

### Measure the harness before shaping the model

[`docs/system-prompt-snapshot/`](docs/system-prompt-snapshot/README.md) holds
the complete API request bodies Claude Code sends (every system block, message
and tool definition), captured from live traffic through this repository's own
MITM proxy ([`scripts/intercept/`](scripts/intercept/README.md)), one directory
per model id, for claude-cli 2.1.310 (captured 2026-10-25). `request.json` is
the artifact of record; `prompt.md` and one file per tool under `tools/` derive
from it, so a release upgrade reviews as a `git diff`. The prompt is chosen
[per model id, not per version](docs/system-prompt-snapshot/what-the-model-gets.md):
of the seven captured, two get a long-form body and five a compressed
`# Harness` body. The 17
built-in skills' bodies and the files five of them extract, which no ordinary
capture records, are captured separately
([`builtin-skills/`](docs/system-prompt-snapshot/builtin-skills/README.md),
548,533 characters and 141 files on 2.1.310). The proxy logs bodies, never
headers, and streams through, because mitmproxy's default buffering withholds
response headers past Claude Code's first-byte watchdog
([`notes/intercept-proxy-response-buffering.md`](notes/intercept-proxy-response-buffering.md),
2026-09-13).

### A replacement system prompt whose reasoning lives outside it

[`sys_prompt/alan-default-next.md`](sys_prompt/alan-default-next.md) replaces
Claude Code's system prompt through `--system-prompt-file`. Per
[`sys_prompt/CLAUDE.md`](sys_prompt/CLAUDE.md), the prompt states the rule and
[`sys_prompt/README.md`](sys_prompt/README.md) carries the reasoning (versions,
dates, measurements, the argument for a line), and an edit ends in a
falsifiable test: name the behaviour that changes without the line, or drop it.
The flag replaces one of two channels; Anthropic-authored text still arrives
through `messages[]`, so a release is a rebase, not a diff: adopt, adapt, or
diverge on purpose, and write down which. Three scripts keep the file honest.
[`scripts/check-prompt-upstream.py`](scripts/check-prompt-upstream.py) requires
each passage borrowed from upstream to occur in the decompiled source the
recorded number of times, and fails rather than passing vacuously when the tree
is missing. [`scripts/check-prompt-coupling.sh`](scripts/check-prompt-coupling.sh)
guards the other direction: Rust strings the prompt teaches the agent to
recognise carry a `// PROMPT-COUPLED` marker, and marker count must equal
needle count before any needle is grepped.
[`scripts/check-prompt-rationale.sh`](scripts/check-prompt-rationale.sh) makes
the reasoning file cost what the prompt costs: each section must quote in its
heading text the prompt still carries, so deleting a prompt line reports its
rationale deletable and the file cannot outgrow the prompt without anyone
setting a size. Budgets use [`agent-tools count-tokens`](src/claude_config/count_tokens.py),
whose two backends deliberately disagree: the vendored Qwen3.8 tokenizer
(sha256-checked on every run) reports 19% below Opus 4.7's count on indented
code and 61% below on Chinese, so no scale factor reconciles them and `--api`
counts a context budget
([design of 2026-09-07](docs/superpowers/specs/2026-09-07-count-tokens-local-default-design.md)).
A `/compact` turn runs under this prompt too, its system block byte-identical
to the file after stripping (2026-09-13), so the summary the next context
window is built from obeys the same rules.

### Prompt changes are measured, not asserted

[`prompt-tests/`](prompt-tests/CLAUDE.md) is a runner-neutral corpus of cases
(`task.md`, a grader-only `reference-solution.md`, fixtures), run against Claude
Code by [`scripts/prompt-test-cc.sh`](scripts/prompt-test-cc.sh) or opencode by
[`scripts/prompt-test-run.sh`](scripts/prompt-test-run.sh). A run is read for
its trajectory, not its answer: a `session-analysis` evidence artifact,
compared artifact against artifact between arms, never stamped `pass`/`fail`.
No run is kept: [`prompt-tests/runs/`](prompt-tests/runs/README.md) is scratch
the round that wrote a probe deletes, since a later round inherits a claim and
its hypothesis, not another run's artifacts. Tested agents run from a fresh
directory holding only fixture files, because harnesses auto-load nearby
`CLAUDE.md`, which contaminates graders too.
[`background-wait-turn`](prompt-tests/general/background-wait-turn/reference-solution.md)
is read mechanically, as a per-turn table of which turns ended with subagents
still running and which called `pre_output.record`, because a turn that ends
only to wait looks like any other in a transcript. Under `NO EXCEPTIONS` one
run recorded and wrote a status on both wait turns and another on neither; with
the wait-turn exception all three ended on one line and recorded once, at the
end (2026-10-22, cc 2.1.289, one run per arm).
[`skills/prompt-engineer-v2/experiments.md`](skills/prompt-engineer-v2/experiments.md)
states the measurement rules as negatives: no enforcement the agent would
derive alone, none for a failure it cannot perceive, no targeting a pass
percentage. [`notes/`](notes/) holds the long-form investigations, one behaviour
each: [`compliance-check-failure-mode.md`](notes/compliance-check-failure-mode.md)
is 47 rounds on why opencode agents fail to follow user direction on specific
task classes, with a citation rule (every claim names its round) and a token
budget on the main file; [`subagent-backgrounding-overrides-run-in-background.md`](notes/subagent-backgrounding-overrides-run-in-background.md)
located the `run_in_background` regression between cc 2.1.143 and 2.1.235 by
scanning 26,953 request captures across 350 sessions (2026-08-28).

### The agent sees its own processes out of band

[`agent-tools run`](docs/agent-tools-status-reference.md) wraps a shell
command, teeing both streams to a capture directory and forwarding the bytes
and the exit code, so it stands in for the bare command; where a wrapped run
still differs, the reference lists it. Status changes reach the agent through
the `PostToolUse`, `PostToolUseFailure` and `UserPromptSubmit` hooks, and
`agent-tools ps` is the pull path after a compaction. The governing invariant
([spec](docs/superpowers/specs/2026-08-26-agent-tools-run-design.md)): no
information *caused by* a status change reaches the agent before the agent
learns that status, which makes backgrounding unobservable. Nothing polls and
nothing is cached: the wrapper records durable facts (`meta.json`, wrapper pid
and start ticks, capture size and mtime) and status is derived at delivery, so
a recycled pid cannot make a dead child read as running. A `flock`-guarded
ledger of what the agent was last told commits only after the report's write
succeeds: a failed write costs a repeat, never a loss. `--background` detaches
by fork and `setsid`; the reparenting is what counts, because the Bash timeout
kill walks the descendant tree (2026-08-29: `setsid` survived, `nohup` and a
bare `&` did not;
[spec](docs/superpowers/specs/2026-08-29-agent-tools-run-background-ps-design.md))
and so does `TaskStop` (measured on cc 2.1.269 in the status reference). Passthrough is
tested against a real binary, since every property it promises is a property
of processes (internals in [`agent-tools/`](agent-tools/)), and the stress
findings stay as written:
[`notes/agent-tools-run-stress-findings.md`](notes/agent-tools-run-stress-findings.md)
records `yes | head -1` needing a kill at 5 s with a 2.1 GB capture before the
drain cap existed, and a publish window in which 61% of wrapper starts briefly
exposed a directory without its `meta.json`, closed by an atomic rename
(2026-08-25 to 2026-08-27). Root resolution is an assertion, never an override:
`CLAUDE_CONFIG_ROOT` must name the compile-time root by device and inode, so a
session on one checkout refuses another's binary.
[`skills/long-bash/`](skills/long-bash/SKILL.md) teaches the protocol. An agent
no notification re-invokes (a subagent, a `claude -p` session) waits with
`agent-tools wait`, which returns when the job ends, when a message to the
agent is queued, or in time for its prompt cache (four minutes, or 50 for a
subagent with an hour's cache): a message reaches a subagent only between tool
calls, and nothing else cuts a call short
([measured](notes/cc-2.1.289-subagent-waits.md), [again on 2.1.310](notes/cc-2.1.310-subagent-wait-costs.md)).

### Session logs as data

[`cc-pretty`](src/claude_config/cc_pretty/main.py) renders Claude Code JSONL
transcripts as an index into the raw log, not a replacement: every block
carries an `@L<n>[i]` reference, and the legend prints the `sed`/`jq` recipe
that recovers the raw string behind it. `--skeleton` emits one line per block,
so a reader plans extraction batches before reading anything. It takes a
session or subagent id as well as a path
([design](docs/superpowers/specs/2026-09-17-cc-pretty-id-or-path-design.md):
2,864 transcripts on this machine, all resolvable by an 8-character prefix
without collision, 2026-09-17). [`opencode-pretty`](src/claude_config/opencode_pretty/convert.py)
flattens opencode's part-based export into the same records and pipeline.
[`cc-render-coverage`](src/claude_config/cc_pretty/coverage.py) checks that the
renderers show everything the source carries, with three kinds of finding: a
file that failed to load, a hardcoded cap that ignores the flag, and content
simply absent. Above them, [`skills/session-analysis/`](skills/session-analysis/SKILL.md)
and its [agent](agents/session-analysis.md) define a skeleton-first reading
protocol and an evidence artifact that bans interpretation (no classification
words; a regex over reasoning blocks is not a read of them); the subagent
returns a path, not the payload. Over six arms on 2026-08-19/20
([design](docs/superpowers/specs/2026-08-20-session-analysis-two-mode-revision-design.md)),
producing the artifact added 25–35% over an answer-only run in the arm that
measured it, not the conjectured 2×, and self-reported process notes were
inaccurate in 6 of 6 arms. [`diagnose-workflow`](skills/diagnose-workflow/SKILL.md)
extracts sub-agent dispatch structure as ground truth where a parent's
self-report disagrees.

[`agent-tools cc-cost`](src/claude_config/cc_cost/main.py) prices a session or
subagent per agent as cc 2.1.310 does (cache writes at their own TTL's rate,
reads at the model's, a fork's copies of its parent's records owned by the
parent, interrupted streams counted), and applies to every agent's cache the
miss test cc applies to its main thread alone. Over 300 sessions (2026-10-26),
subagents missed 270 times, costing $207 to re-write, and cc's status line
shows none of those misses; the main thread's 52 cost $57. The traced total never exceeds cc's own
`cost-state` total by more than 0.05% in 264 sessions, and the median session
traces 96% of it; the rest is requests cc never transcribes, such as prompt
suggestions and WebFetch's model calls.

### Human in the loop over Telegram

One local process holds the bot token, owns the single `getUpdates` drain,
forwards sends from any number of sessions over a Unix socket, and appends both
directions to one JSONL log
([design](docs/superpowers/specs/2026-09-12-telegram-hitl-design.md),
[`src/claude_config/telegram_hitl/`](src/claude_config/telegram_hitl/)). A
measurement forces the single drain (2026-09-12): a second `getUpdates`
consumer is not refused, the *first* one gets `409 Conflict`, so exclusion is a
local `flock` taken before anything touches the network, on a descriptor never
closed. A socket, not a port, because a port number names a different socket
in every network namespace; the state directory sits on a path bind-mounted
identically into the host and every container (one inode from two containers,
2026-09-13). An update is appended and fsynced before the next poll carries the
advanced offset that tells Telegram to forget it. Waiting happens against the
file, where a proxy restart is invisible, not at a blocking endpoint. The proxy
never reacts to a message: an acknowledgement would mask the one failure that
matters, a message logged and picked up by nobody.
[`systemd/telegram-hitl.service`](systemd/telegram-hitl.service) runs it, and
[`skills/telegram-hitl/`](skills/telegram-hitl/SKILL.md) carries the working
rules, the Bot API traps and the log reader agents arm as a script. Six test
modules drive the proxy against a fake Bot API on loopback, and
[the skill's tests](tests/test_telegram_hitl_skill.py) execute that script. `doc-budget.toml` caps the skill at 1,000 tokens,
enforced by [`tests/test_doc_budget.py`](tests/test_doc_budget.py).

### Environment context with drift detection

[`agent-tools env-context`](src/claude_config/env_context/) is a SessionStart
hook adding what Claude Code's environment block does not carry (the checkout a
worktree belongs to, the shell the Bash tool actually runs, the session id)
under `# Environment (supplement)`, so two identically headed sections cannot
read as a contradiction, then its own `# Git status at session start`. Where
Claude Code prints `unknown`, it says what it found and what that means
(2026-09-13, cc 2.1.269: `Shell: unknown` beside this hook's `/bin/bash`).
[`docs/env-context-manifest.json`](docs/env-context-manifest.json) pins the
literal set of Claude Code's own block: the hook reads the installed binary's
string table, diffs the set, compares occurrence *counts* for the short labels
that also occur elsewhere in the binary, and warns inside the block, not only
on stderr, which the agent never reads. `--update` refuses to re-pin a count of
zero, which could never fail again
([design](docs/superpowers/specs/2026-09-02-env-context-design.md);
[`scripts/check-env-context.sh`](scripts/check-env-context.sh) shows the
difference after an upgrade).

Where customisation reaches the model at all: a backgrounded session's fork
builds its argv from scratch, with neither `--system-prompt` nor
`--system-prompt-file` ([`docs/background-sessions.md`](docs/background-sessions.md),
cc 2.1.269), but still reads `settings.json`, so an output style is the one
customisation that survives the handoff
([`output-styles/README.md`](output-styles/README.md)).
[`scripts/claude.sh`](scripts/claude.sh) closes the handoff path with
`CLAUDE_CODE_DISABLE_AGENT_VIEW=1`, binds the proxy environment only after a
TCP connect to the listener succeeds, and resolves its prompt with
`readlink -f`, so a worktree's copy loads that worktree's prompt.

### Design first, record kept

Non-trivial changes start as a dated spec under
[`docs/superpowers/specs/`](docs/superpowers/specs/) and, when built, a plan
under [`docs/superpowers/plans/`](docs/superpowers/plans/) (18 and 13 of them on
2026-09-23). A spec records measurement, not intent: the Telegram design states
that every constraint in it was measured against the live Bot API on a named
date, and marks the unverified as unverified. Specs, plans and notes are
write-once evidence; the post-upgrade runbook
([`.claude/skills/update-claude-code/`](.claude/skills/update-claude-code/SKILL.md))
forbids re-pinning them to a newer Claude Code, states its principle as "a
check that cannot fail is not a check", tabulates what each of its checks is
blind to, and makes re-deriving what a falsified check was a premise for a step
of its own. [`conventions/`](conventions/CLAUDE.md) holds the rules agents are
graded against: intent markers skip a quality check only when they carry
`what; why`, a malformed marker itself a finding
([`intent-markers.md`](conventions/intent-markers.md)); a mandatory self-report
section exists even when empty, and a finding that fits several categories goes
under the hardest to admit ([`agent-responses.md`](conventions/agent-responses.md)).
The prompt's tone markers (`[record]`, `[idea]`, `[may-rewind]`) constrain
inference rather than mood, and its "writing for other agents" rule treats
compaction summaries, subagent prompts, specs and docs as one category, read
cold by a reader who will act on them as a premise.
[`skills/git-surgery/`](skills/git-surgery/SKILL.md) rewrites history through
pygit2 without touching the worktree, index or `HEAD`, writing only under
`refs/git-surgery/` (`result` by default), and cascades SHA references held in
tracked files and commit messages; the one case that cannot be repaired
afterwards, a squash whose message would name its own SHAs, is documented with
the pre-rewrite it needs. [`skills/notes/`](skills/notes/SKILL.md) stands in for
built-in auto-memory by writing into the `CLAUDE.md` and `README.md` files
Claude Code already loads, and refuses to persist anything derivable from the
tree.

### opencode as a second harness

[`opencode/agents/alan-default-ids.md`](opencode/agents/alan-default-ids.md) is
the production opencode prompt, a labelled-ID derivative of codex's
`base_instructions`; [`min.md`](opencode/agents/min.md) beside it is a
deliberately thin correctness floor that keeps single-rule ablations
interpretable. [`docs/opencode-system-prompt/`](docs/opencode-system-prompt/alan-default-commentary.md)
mirrors each with one comment block per rule: what the rule was written to do
and which measured failure produced it. The prompt's self-review gate is a
shell command, `agent-tools opencode.gate`, not prompt text, so the reasoning
prompts arrive in a separate tool result, and under the binary's root
assertion a prompt test run from the wrong checkout fails loudly.
[`skills/opencode-subcommand/`](skills/opencode-subcommand/SKILL.md) is the
recipe for driving `opencode run` programmatically, naming the contamination
channels that make a probe measure the wrong thing: an agent file's frontmatter
becoming system-prompt text, the wrapper's own command line in
`/proc/*/cmdline`, `AGENTS.md` injection. Removing only the frontmatter once
turned 0-tool-call cells into 19- and 34-tool-call ones
([round 20](notes/compliance-check-failure-mode/round-20.md)).
[`scripts/prompt-test-run.sh`](scripts/prompt-test-run.sh) uses opencode as a
neutral harness for the other harness's prompt: by default
`sys_prompt/alan-default-next.md` on a Claude model through OpenRouter.

## Upstream

Forked from [solatis/claude-config](https://github.com/solatis/claude-config)
at `6e72bc29` (2026-02-09). Inherited from there, and still the shape of the
planning workflow: the `planner`, `deepthink`, `refactor`, `problem-analysis`,
`decision-critic`, `codebase-analysis`, `doc-sync`, `prompt-engineer` and
`incoherence` skills; the `developer`, `architect`, `technical-writer`,
`quality-reviewer` and `debugger` agents; `conventions/`; and the
`skills/scripts` orchestration framework. Upstream's README, which explains
that workflow and its reasoning, is `git show 6e72bc29:README.md` as it stood
at the fork point.

## Install

```bash
git clone https://github.com/Alan-Chen99/claude-config ~/claude-config
~/claude-config/install.sh
```

It symlinks `agents`, `conventions`, `output-styles`, `skills` and
`settings.json` into `~/.claude/`, `opencode/` as `~/.config/opencode`,
`codex/config.toml`, `AGENTS.md` and `skills/config` → `skills/` into
`${CODEX_HOME:-~/.codex}`, and the `systemd/` units into
`~/.config/systemd/user/` (enabled by hand); links an `agent-tools` build and
the launchers into `~/.local/bin`; and provisions the Python venv. An
existing regular Codex file is saved once with `.pre-claude-config` appended;
an existing backup blocks the replacement. Run it from the canonical checkout
only: a worktree that installs its own build repoints `~/.local/bin` at the
worktree and breaks every other session when the worktree is deleted. Test the
script only with a scratch `HOME` and `ALLOW_WORKTREE_INSTALL=1`, never against
the live home.

## Tests

```bash
uv run pytest                     # Python: tests/ and skills/scripts/tests
(cd agent-tools && cargo test)    # Rust
```

## License

MIT. Copyright (c) 2025 Leon Mergen for the upstream work; copyright (c) 2026
Xinyang Chen for everything since the fork.
