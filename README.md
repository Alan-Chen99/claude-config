# claude-config

[![CI](https://github.com/Alan-Chen99/claude-config/actions/workflows/ci.yml/badge.svg)](https://github.com/Alan-Chen99/claude-config/actions/workflows/ci.yml)

My Claude Code and opencode configuration, and the tooling built around it.
It began as a fork of [solatis/claude-config](https://github.com/solatis/claude-config)
and grew a Rust harness (`agent-tools`), a replacement system prompt with its
reasoning kept beside it rather than inside it, a prompt-evaluation corpus, and
a set of measured investigations into what the harness actually does.

## Status

This is a personal configuration, published to show the ideas rather than to be
installed. `install.sh` symlinks the tree into `~/.claude/` and assumes one host
layout — read it before running it anywhere. Nothing here is versioned or
packaged for anyone else, and Claude Code moves quickly: every measurement
below carries the date it was taken and, where it depends on one, the Claude
Code version.

## Ideas

### Measure the harness before shaping the model

[`docs/system-prompt-snapshot/`](docs/system-prompt-snapshot/README.md) holds
the complete API request bodies Claude Code sends — every system block, every
message, every tool definition — captured from live traffic through this
repository's own MITM proxy ([`scripts/intercept/`](scripts/intercept/README.md)),
one directory per model id, for claude-cli 2.1.269 (captured 2026-09-11).
`request.json` is the artifact of record; `prompt.md` and one file per tool
under `tools/` are derived from it so that a release upgrade can be reviewed as
`git diff`. The finding that reorganised the directory: the prompt is chosen per
model id, not per version, and
[no two of the five captured models receive the same one](docs/system-prompt-snapshot/what-the-model-gets.md)
— opus-4-7 and sonnet-5 get the long-form body (8,702 and 8,745 system tokens),
opus-5, fable-5 and opus-4-8 the compressed `# Harness` body (3,252, 3,556 and
2,266). The 17 built-in skills' bodies, which no ordinary capture records, are
captured separately ([`builtin-skills/`](docs/system-prompt-snapshot/builtin-skills/README.md),
512,397 characters). The proxy logs bodies only, never headers; it had to be
taught pass-through streaming, because mitmproxy's default buffering withholds
response headers past Claude Code's first-byte watchdog
([`notes/intercept-proxy-response-buffering.md`](notes/intercept-proxy-response-buffering.md),
measured 2026-09-13). [`docs/background-sessions.md`](docs/background-sessions.md)
records what a session silently loses when it moves to the background: the
fork's argv is built from scratch, and neither `--system-prompt` nor
`--system-prompt-file` is in it (cc 2.1.269).

### A replacement system prompt whose reasoning lives outside it

[`sys_prompt/alan-default-next.md`](sys_prompt/alan-default-next.md) replaces
Claude Code's system prompt through `--system-prompt-file`. The rule in
[`sys_prompt/CLAUDE.md`](sys_prompt/CLAUDE.md): the prompt states the rule and
the file beside it carries the reasoning — version numbers, dates, measurements
and the argument that justified a line all move out — and the editing loop ends
in a falsifiable test: name the behaviour that changes without the line, or drop
it. The flag replaces only one of two channels; Anthropic-authored text still
arrives through `messages[]`, so a release is a rebase, not a diff — adopt,
adapt, or diverge on purpose, and write down which. Two scripts keep the file
honest: [`scripts/check-prompt-upstream.py`](scripts/check-prompt-upstream.py)
requires each passage borrowed from upstream to occur in the decompiled source
the recorded number of times, and exits non-zero rather than passing vacuously
when the tree is missing; [`scripts/check-prompt-coupling.sh`](scripts/check-prompt-coupling.sh)
guards the other direction — Rust strings the prompt teaches the agent to
recognise carry a `// PROMPT-COUPLED` marker, and marker count must equal
needle count before any needle is grepped. Budgeting uses
[`agent-tools count-tokens`](src/claude_config/count_tokens.py), whose two
backends deliberately do not agree: the vendored Qwen3.8 tokenizer (sha256-checked
on every run) reports 19% below Opus 4.7's count on indented code and 61% below
on Chinese, so no scale factor reconciles them and `--api` is the one used for a
context budget (recorded in the
[design of 2026-09-07](docs/superpowers/specs/2026-09-07-count-tokens-local-default-design.md)).
Measured 2026-09-13: a `/compact` turn runs under this prompt too — its system
block byte-identical to the file after stripping — so the summary the next
context window is built from obeys the same rules.

### Prompt changes are measured, not asserted

[`prompt-tests/`](prompt-tests/CLAUDE.md) is a runner-neutral corpus of cases —
`task.md`, a grader-only `reference-solution.md`, fixtures — run against Claude
Code by [`scripts/prompt-test-cc.sh`](scripts/prompt-test-cc.sh) or against
opencode by [`scripts/prompt-test-run.sh`](scripts/prompt-test-run.sh). The
recorded result is the trajectory, not the answer: a `session-analysis`
evidence artifact under [`prompt-tests/runs/`](prompt-tests/runs/README.md),
compared artifact-against-artifact between arms; `pass`/`fail` is never stamped
on a run. Tested agents run from a fresh directory holding only fixture files,
because harnesses auto-load nearby `CLAUDE.md` — and graders are contaminated
by the same channel. One case shows the shape:
[`subagent-foreground-default`](prompt-tests/general/subagent-foreground-default/reference-solution.md)
is graded mechanically — a per-record table of the `Agent` tool-use inputs,
read with `jq` — because omission of `run_in_background` is the failure mode
and a backgrounded call looks unremarkable in a transcript. With the old prompt bullet, 0 of 3 calls carried
the parameter and all three backgrounded; with the rewritten one, 9 of 9 across
three trials passed `false` and none did (2026-09-16, cc 2.1.269).
[`skills/prompt-engineer-v2/experiments.md`](skills/prompt-engineer-v2/experiments.md)
states the measurement rules as negatives: no enforcement the agent would
derive alone, none for a failure the agent cannot perceive, no targeting a pass
percentage. [`notes/`](notes/) holds the long-form investigations, one behaviour
each: [`compliance-check-failure-mode.md`](notes/compliance-check-failure-mode.md)
is 47 rounds on why opencode agents fail to follow user direction on specific
task classes, with a citation rule (every claim names its round) and a token budget
on the main file; [`subagent-backgrounding-overrides-run-in-background.md`](notes/subagent-backgrounding-overrides-run-in-background.md)
located the `run_in_background` regression between cc 2.1.143 and 2.1.235 by
scanning 26,953 request captures across 350 sessions (2026-08-28).

### The agent sees its own processes out of band

[`agent-tools run`](docs/agent-tools-status-reference.md) wraps a shell
command: it tees both streams to a capture directory and forwards the bytes and
the exit code, so it can stand in for the bare command — the ways a wrapped run
still differs from a bare one are listed rather than papered over. Each child's
status changes reach the agent through the `PostToolUse`, `PostToolUseFailure`
and `UserPromptSubmit` hooks, and `agent-tools ps` is the pull path after a
compaction. The governing invariant
([spec](docs/superpowers/specs/2026-08-26-agent-tools-run-design.md)): no
information *caused by* a status change reaches the agent before the agent
learns that status; that is what makes backgrounding unobservable. Nothing
polls and nothing is cached: the wrapper records durable facts (`meta.json`, wrapper pid
and start ticks, capture size and mtime) and the status is derived at delivery,
so a recycled pid cannot make a dead child read as running. A `flock`-guarded
ledger records what the agent was last told and commits only after the
report's write succeeds — a failed write costs a repeat, never a loss.
`--background` detaches by fork and `setsid`, and the reparenting is the
operative property, because the Bash timeout kill walks the descendant tree
(measured 2026-08-29: `setsid` survived, `nohup` and a bare `&` did not;
[spec](docs/superpowers/specs/2026-08-29-agent-tools-run-background-ps-design.md))
and so does `TaskStop` (measured on cc 2.1.269 in the
[status reference](docs/agent-tools-status-reference.md)). Passthrough is
tested against a real binary, since every property it promises is a property
of processes ([spec](docs/superpowers/specs/2026-08-26-agent-tools-run-design.md);
internals in [`agent-tools/CLAUDE.md`](agent-tools/CLAUDE.md)), and the stress
findings are kept as written:
[`notes/agent-tools-run-stress-findings.md`](notes/agent-tools-run-stress-findings.md)
records, for instance, `yes | head -1` needing a kill at 5 s with a 2.1 GB
capture before the drain cap existed, and a publish window in which 61% of
wrapper starts briefly exposed a directory without its `meta.json`, closed by
an atomic rename (2026-08-25 to 2026-08-27). Root resolution is an assertion,
never an override: `CLAUDE_CONFIG_ROOT` must name the compile-time root by
device and inode, so a session on one checkout refuses another checkout's
binary. [`skills/long-bash/`](skills/long-bash/SKILL.md) teaches the agent the
protocol.

### Session logs as data

[`cc-pretty`](src/claude_config/cc_pretty/main.py) renders Claude Code JSONL
transcripts as an index into the raw log rather than a replacement for it:
every block carries an `@L<n>[i]` reference, and the legend prints the
`sed`/`jq` recipe that recovers the raw string behind any of them.
`--skeleton` emits one line per block so a reader can plan extraction batches
before reading anything. It accepts a session or subagent id as well as a path
([design](docs/superpowers/specs/2026-09-17-cc-pretty-id-or-path-design.md):
2,864 transcripts on this machine, all resolvable by an 8-character prefix
without collision, 2026-09-17). [`opencode-pretty`](src/claude_config/opencode_pretty/convert.py)
flattens opencode's part-based export into the same records and reuses the
pipeline. [`cc-render-coverage`](src/claude_config/cc_pretty/coverage.py)
checks that the renderers show everything the source carries, with three
kinds of finding: a file that failed to load, a hardcoded cap that ignores the
flag, and content that is simply absent. Above them, [`skills/session-analysis/`](skills/session-analysis/SKILL.md)
and its [agent](agents/session-analysis.md) define a skeleton-first reading
protocol and an evidence artifact that bans interpretation — no classification
words, and a regex over reasoning blocks is not a read of them; the subagent
returns a path, not the payload. Measured 2026-08-19/20 over six arms
([design](docs/superpowers/specs/2026-08-20-session-analysis-two-mode-revision-design.md)):
in the arm that measured it, producing the artifact added 25–35% over an
answer-only run rather than the conjectured 2×, and self-reported process notes
were inaccurate in 6 of 6 arms.
[`diagnose-workflow`](skills/diagnose-workflow/SKILL.md) extracts sub-agent
dispatch structure as ground truth where a parent's self-report disagrees.

### Human in the loop over Telegram

One local process holds the bot token, owns the single `getUpdates` drain,
forwards sends from any number of sessions over a Unix socket, and appends both
directions to one JSONL log
([design](docs/superpowers/specs/2026-09-12-telegram-hitl-design.md),
[`src/claude_config/telegram_hitl/`](src/claude_config/telegram_hitl/)). The
single drain is forced by a measurement (2026-09-12): a second `getUpdates`
consumer is not refused — the *first* one gets `409 Conflict` — so exclusion is
enforced locally with `flock` before anything touches the network, and the lock
descriptor is never closed. A socket rather than a port, because a port number
names a different socket in every network namespace; the state directory sits
on a path bind-mounted identically into the host and every container (verified
as one inode from two containers, 2026-09-13). An update is appended and fsynced
before the next poll carries the advanced offset, which is what tells Telegram
to forget it. There is no blocking wait endpoint — waiting happens against the
file, where a proxy restart is invisible — and the proxy never reacts to a
message, because an acknowledgement would mask the one failure that matters: a
message logged and picked up by nobody. [`systemd/telegram-hitl.service`](systemd/telegram-hitl.service)
runs it, [`skills/telegram-hitl/`](skills/telegram-hitl/SKILL.md) carries the
working rules and the Bot API traps, and six test modules drive it against a
fake Bot API on loopback — the skill's Python recipes are executed out of the
markdown by [the tests](tests/test_telegram_hitl_skill.py).

### Environment context with drift detection

[`agent-tools env-context`](src/claude_config/env_context/) is a SessionStart
hook that supplements Claude Code's own environment block with what it does
not carry — the checkout a worktree belongs to, the shell the Bash tool actually
runs, the session id — under the heading `# Environment (supplement)`, so two
identically headed sections cannot read as a contradiction, followed by its own
`# Git status at session start` section. Where Claude Code
prints `unknown`, this says what it found and what it means (measured
2026-09-13, cc 2.1.269: `Shell: unknown` beside this hook's `/bin/bash`).
[`docs/env-context-manifest.json`](docs/env-context-manifest.json) pins the
literal set of Claude Code's own block; the hook reads the installed binary's
string table, diffs the set and, for the short labels that also occur elsewhere
in the binary, compares occurrence *counts*, and warns inside the block — not
only on stderr, which the agent never reads. `--update` refuses to re-pin a count of zero, which could
never fail again ([design](docs/superpowers/specs/2026-09-02-env-context-design.md);
[`scripts/check-env-context.sh`](scripts/check-env-context.sh) shows the
difference after an upgrade). The related finding about where customisation
reaches the model at all: a backgrounded session's fork is launched without
`--system-prompt-file` but still reads `settings.json`, so an output style is
the one customisation that survives the handoff
([`output-styles/README.md`](output-styles/README.md)), and
[`scripts/claude.sh`](scripts/claude.sh) closes the handoff path with
`CLAUDE_CODE_DISABLE_AGENT_VIEW=1`, binds the proxy environment only after a
TCP connect to the listener succeeds, and resolves its prompt with `readlink -f`
so that a worktree's copy loads that worktree's prompt.

### Design first, record kept

Non-trivial changes start as a dated spec under
[`docs/superpowers/specs/`](docs/superpowers/specs/) and, when built, a plan
under [`docs/superpowers/plans/`](docs/superpowers/plans/) — 18 and 13 of them
on 2026-09-23. A spec records measurement, not intent: the Telegram design
states that every constraint in it was measured against the live Bot API on a
named date, and marks the unverified as unverified. Specs, plans and notes are
write-once evidence; the post-upgrade runbook
([`.claude/skills/update-claude-code/`](.claude/skills/update-claude-code/SKILL.md))
forbids re-pinning them to a newer Claude Code, states its principle as "a
check that cannot fail is not a check", tabulates what each of its checks is
blind to, and makes re-deriving what a falsified check was a premise for a step
of its own. [`conventions/`](conventions/CLAUDE.md)
holds the rules agents are graded against: intent markers that skip a quality
check only when they carry `what; why`, with a malformed marker itself a
finding ([`intent-markers.md`](conventions/intent-markers.md)); a mandatory
self-report section that must exist even when empty, where a finding that fits
several categories goes under the hardest to admit
([`agent-responses.md`](conventions/agent-responses.md)). The prompt's tone
markers (`[record]`, `[idea]`, `[may-rewind]`) constrain inference rather than
mood, and its "writing for other agents" rule treats compaction summaries,
subagent prompts, specs and docs as one category, read cold by a reader who
will act on them as a premise. [`skills/git-surgery/`](skills/git-surgery/SKILL.md)
rewrites history through pygit2 without touching the worktree, index or `HEAD`,
writing only under `refs/git-surgery/` (`result` by default), and cascades SHA
references held in tracked files and commit messages — the one case that cannot
be repaired after the fact, a squash whose message would have to name its own
SHAs, is documented together with the pre-rewrite it needs.
[`skills/notes/`](skills/notes/SKILL.md) stands in for built-in auto-memory by
writing into the `CLAUDE.md` and `README.md` files Claude Code already loads,
and refuses to persist anything derivable from the tree.

### opencode as a second harness

[`opencode/agents/alan-default-ids.md`](opencode/agents/alan-default-ids.md) is
the production opencode prompt, a labelled-ID derivative of codex's
`base_instructions`; [`min.md`](opencode/agents/min.md) beside it is a
deliberately thin correctness floor, so that single-rule ablations stay
interpretable. [`docs/opencode-system-prompt/`](docs/opencode-system-prompt/alan-default-commentary.md)
carries an annotated mirror of each, one comment block per rule, recording
what the rule was written to do and which measured failure produced it. The prompt's self-review gate is a
shell command, `agent-tools opencode.gate`, rather than prompt text, so the
reasoning prompts arrive in a separate tool result; the binary's root assertion
covers it, so a prompt test run from the wrong checkout fails loudly.
[`skills/opencode-subcommand/`](skills/opencode-subcommand/SKILL.md) is the
recipe for driving `opencode run` programmatically and names the contamination
channels that make a probe measure the wrong thing — an agent file's
frontmatter becoming system-prompt text, the wrapper's own command line visible
in `/proc/*/cmdline`, `AGENTS.md` injection; removing only the frontmatter once
turned 0-tool-call cells into 19- and 34-tool-call ones
([round 20](notes/compliance-check-failure-mode/round-20.md)).
[`scripts/prompt-test-run.sh`](scripts/prompt-test-run.sh) uses opencode as a
neutral harness for the other harness's prompt: its default subject is
`sys_prompt/alan-default-next.md` on a Claude model through OpenRouter.

## Repository map

| Path | What |
| --- | --- |
| [`CLAUDE.md`](CLAUDE.md) | The index: every directory, with when to read what; the detail sits in each directory's own `CLAUDE.md` |
| [`agent-tools/`](agent-tools/) | Rust binary: the `run`/`ps` process wrapper and hooks, `cc-pretty`, `count-tokens`, `env-context`, launchers |
| [`sys_prompt/`](sys_prompt/) | Replacement system prompts loaded by `scripts/claude.sh`, and the reasoning behind each line |
| [`output-styles/`](output-styles/) | Output styles — the customisation surface that survives a background handoff |
| [`prompt-tests/`](prompt-tests/) | Runner-neutral prompt evaluation cases and recorded runs |
| [`notes/`](notes/) | Investigation write-ups: measured evidence and root cause, one behaviour each |
| [`docs/`](docs/) | Captured system prompts, harness anatomy, design specs and plans |
| [`skills/`](skills/), [`agents/`](agents/), [`conventions/`](conventions/) | Skills, sub-agent definitions, documentation and code conventions — upstream's, extended |
| [`src/claude_config/`](src/claude_config/) | Python: log renderers, the Telegram proxy, the env-context hook, token counting |
| [`scripts/`](scripts/) | The `claude.sh` launcher and its provider-backed siblings `kimi.sh` and `zai.sh`, the MITM intercept proxy, prompt-test runners, drift checks |
| [`opencode/`](opencode/) | opencode configuration and agent prompts |
| [`plans/`](plans/) | Plan storage, historical |
| [`tests/`](tests/) | The Python suite (pytest + hypothesis); Rust tests live under `agent-tools/tests/` |

## Upstream

Forked from [solatis/claude-config](https://github.com/solatis/claude-config)
at `6e72bc29` (2026-02-09). Inherited from there, and still the shape of the
planning workflow: the `planner`, `deepthink`, `refactor`, `problem-analysis`,
`decision-critic`, `codebase-analysis`, `doc-sync`, `prompt-engineer` and
`incoherence` skills; the `developer`, `architect`, `technical-writer`,
`quality-reviewer` and `debugger` agents; `conventions/`; and the
`skills/scripts` orchestration framework. Upstream's README explains that
workflow and its reasoning; this fork's copy of it, as it stood at the fork
point, is `git show 6e72bc29:README.md`.

## Install

```bash
git clone https://github.com/Alan-Chen99/claude-config ~/claude-config
~/claude-config/install.sh
```

Directory-level symlinks for `agents`, `conventions`, `output-styles` and
`skills` into `~/.claude/`, `~/.config/opencode` → `opencode/`, file symlinks
for `settings.json` and `statusline.sh`, an `agent-tools` build linked with
the `scripts/claude.sh`, `scripts/kimi.sh` and `scripts/zai.sh` launchers into
`~/.local/bin`, and the Python venv. Run it from the
canonical checkout only: a worktree that installs its own build repoints
`~/.local/bin` at the worktree and breaks every other session when the
worktree is deleted.

## Tests

```bash
uv run pytest                     # Python: tests/ and skills/scripts/tests
(cd agent-tools && cargo test)    # Rust
```

## License

MIT. Copyright (c) 2025 Leon Mergen for the upstream work; copyright (c) 2026
Xinyang Chen for everything since the fork.
