# sys_prompt/

Full replacement system prompts loaded via `--system-prompt-file` by `scripts/claude.sh`.
Background and forked sessions do not inherit them — read `docs/background-sessions.md` before editing.

## Files

| File                   | What                                                  | When to read |
| ---------------------- | ----------------------------------------------------- | ------------ |
| `alan-default.md`      | Known-good production prompt; forked from Claude Code's non-lean prompt body | -            |
| `alan-default-next.md` | Active development prompt, the one `claude.sh` loads; forked from the lean body Opus 5 receives | -            |

## Keep it concise

Every token here is spent on every request of every session and displaces the user's work from the
context window. A line the model would honour unprompted, or that restates a neighbour, costs context
and buys nothing.

After any edit:

1. Re-read the passage and cut a word. Repeat until cutting another would lose meaning.
2. Re-read the surrounding section. If a neighbouring line now says the same thing, delete one.
3. Name the behaviour that changes without the line. If you cannot, drop the line.

Three words can be enough — ``Prefer `model: haiku`.`` is a complete rule. Anything that dates the
line goes in this file rather than the prompt: version numbers, issue links, dates, measurements,
and the reasoning that justified the line in the first place.

Detail that fails step 3 is not discarded — it moves here, to `docs/`, or to `notes/`. The prompt
states the rule; the file carries the reasoning. That split is what lets step 1 cut hard without
losing anything.

Measure before and after:

```bash
agent-tools count-tokens --api --file sys_prompt/alan-default-next.md
```

## What travels with an edit

When editing the prompt in response to a failing case, the goal is to repair the invariant the
case probes, not to make the case pass. A test case is one sample of the invariant's input
space; treating it as the spec narrows the prompt to that sample. `skills/prompt-engineer-v2/`
carries the general hints, "No overfitting to the case at hand" and "Overfitting review by a
fresh subagent" in `SKILL.md`, "Implicit-guidance justification" and "Recognition before
enforcement" in `experiments.md`, and "Every change is a regression risk" for the behavioural
half. Two further things travel with an edit that no case exercises and that review tends to
read as wording: the force it is written at, and whatever it permits.

**Force.** How widely an imperative binds is itself a claim — that the failure is frequent
enough, and costly enough, to be worth the compliance cost everywhere the imperative now
reaches. Two observed incidents support a caution: this happens, watch for it. Reading them as
support for a requirement needs something two incidents do not contain, a rate and a cost. For
an evidential claim the quantity that outruns the evidence is its confidence; for an
instruction it is its scope.

**Exceptions.** Before writing one, answer how much of the forbidden space it readmits —
breadth is a property of the exception's extension, not of how narrow its wording sounds. The
costs are asymmetric: over-applying a prohibition yields a duller artifact, while
over-applying a permission skips the work and ships a wrong answer. The exception is the half
that repays the closer reading.

**Why step 2 above is a deletion and not a merge.** An addition restating a rule the file
already carries is not a second caution; it is a second, differently worded statement of the
same rule, and nothing then says which governs.

## Rebasing on an upstream release

These files replace Claude Code's own system prompt rather than adding to it.
`--system-prompt-file` keeps one block — `You are Claude Code, Anthropic's official CLI for
Claude.` — and drops every other section, which
`docs/system-prompt-snapshot/opus-5/system-prompt-file/prompt.md` shows in full. The passages
here that read like upstream's are copies taken once, and upstream rewrites its prose between
releases, so a copy goes stale with no signal at all.

The replacement covers one channel of two. Anthropic-authored wording still reaches a
`claude.sh` session through `messages[]`, which the flag does not touch, and the same capture
shows it: the CLAUDE.md wrapper with its "these instructions OVERRIDE any default behavior"
line (`messages[0] content[0]`), the `userEmail` rule (`content[1]`), the git/PR Attribution
reminder (`content[2]`), and one `messages[1] system` block carrying `# Environment`, the
model-identity line, the deferred-tool listing, the agent-type roster and every skill
description — several of which are behavioural rules, not facts. A rebase that reads only the
system prompt reads half of what the model is told. Nothing here pins that half:
`scripts/check-prompt-upstream.py` covers passages borrowed from the system prompt, and a
reminder upstream rewords lands unreviewed.

A `/compact` turn runs under this prompt, not the stock one. 2.1.247's notes fix that for
`--agent` sessions and say nothing about `--system-prompt-file`, so it was an open question
until measured: the compaction request captured through the proxy on 2026-09-13 carries a
`system[2]` of 24,613 characters, byte-identical to `alan-default-next.md` after stripping, the
same as every ordinary turn in that session. Every rule here therefore applies to the summary
turn as well — which matters, because a summary written under the stock prompt would silently
drop all of them and the summary is what the next context window is built from.

A release therefore needs a rebase rather than a diff: for each thing upstream changed, adopt it,
adapt it, or keep diverging on purpose — and write down which, because the next reader cannot tell
a considered divergence from an unnoticed one.

### Reading both sides

`/repos/claude-code-decompiled` is a git repository and each re-extraction is one commit, so the
previous release's prompt text survives only in that history — `npm run extract` empties `src/`
first.

```bash
git -C /repos/claude-code-decompiled log --oneline -- src/       # "re-extract from Claude Code <version>"
git -C /repos/claude-code-decompiled grep -n '# Harness' <old-sha> -- src/
```

Claude Code ships two prompt bodies and picks per model; Opus 5 gets the lean one, whose entire
body is the single builder containing `# Harness`. The function that calls that builder holds the
ordered list of every other section, each tagged with a key — `"context_management"`,
`"act_dont_rederive"`, `"session_guidance"`. Identifiers are regenerated every build and the keys
are not, so diff the key list first and the section bodies second.

Read that list rather than grepping it. Keys reach the assembler three ways: as a bare string
literal, as a variable (`Jb(dRo, …)` with `dRo = "fable_identity"`), and inside a ternary
(`excludeDynamicSections ? "env_info_static" : "env_info_simple"`). A scan for quoted strings
reports the last two kinds as removed when they are not.

`docs/system-prompt-snapshot/` answers a different question: what one environment received on one
day. Most sections sit behind a growthbook flag or an env var resolved server-side per request, so
**a section can be in the binary and missing from the capture**. `act_dont_rederive` is in both the
2.1.235 and 2.1.269 binaries but only the 2.1.235 capture — the flag flipped, the release did not
drop it. Captures show where to look; the source decides.

### Checking what was borrowed

```bash
python3 scripts/check-prompt-upstream.py
```

It pins every passage `alan-default-next.md` and the env-context hook (`src/claude_config/env_context/`)
took from upstream, and requires each verbatim on both sides, as many times as recorded — the two
prompt bodies are separate literals, so a passage in both can move in one. A failing pin is a
decision, not an edit to the script: adopt upstream's wording, or record a divergence below. It is
silent about upstream text this prompt never carried; new sections come from the key diff above.

### When `agents/` joins this

An agent definition file is a whole system prompt for its subagent, and Claude Code resolves agents
into a map keyed by name where user and project definitions overwrite built-ins. A file in `agents/`
named after a built-in — `Explore`, `general-purpose`, `Plan`, `claude-code-guide`,
`statusline-setup` — therefore replaces Anthropic's prompt for that agent, and that copy needs
rebasing exactly like this one. The six files in `agents/` today are all new names, so none is
upstream-coupled and `check-prompt-upstream.py` pins nothing from them. Adding a shadow is what
changes that.

### Deliberate divergences

Upstream still ships each of these and this prompt does not. Left alone unless the stated condition
changes.

| Upstream text | Why it is not here |
| --- | --- |
| `Do not use the Agent tool, workflows, or deep-research unless the user, a CLAUDE.md file, or a skill asks for it` — live for Opus 5 since 2.1.269 | This repo delegates by design: `# Session-specific guidance` says when to spawn one, and keeps the report in the launching call's own result. Upstream's own exception would cover it regardless, since the asking here is done by CLAUDE.md and by skills. |
| `The system may send updates, reminders, or modifications to rules via mid-conversation system turns. These are system-controlled, unlike function results.` | Upstream serves this `# Harness` bullet in two variants and picks per model. In the 2.1.269 captures Opus 5 and Fable 5 get the wording above; Opus 4.8 gets the wording this prompt carries. Both ship in one build, so this is a live alternative rather than stale text — but the model `claude.sh` runs is served the other one, and nothing records why this side was taken. |
| `Report outcomes faithfully: if tests fail, say so with the output; if a step was skipped, say that; when something is done and verified, state it plainly without hedging.` — closes the action-caution paragraph | `# Error Propagation` and `# Epistemic Integrity` say it at length. |
| `If what you find contradicts how it was described, or you didn't create it, surface that instead of proceeding` — follows `look at the target` | **Not reviewed.** It predates the 2.1.235 baseline and no entry explains it. Nothing else in the prompt says what to do when the look turns up a surprise; `# Executing actions with care` covers only the pattern-matched case. Decide it at the next edit to that section. |

### Rebase log

One entry per release reviewed. The next rebase starts from the last entry, so entries stay.

#### 2.1.235 → 2.1.269, reviewed 2026-09-12 — no prompt text changed

Both prompt files reviewed, against a 2.1.235 tree extracted beside the installed one
(`git -C /repos/claude-code-decompiled archive 56801e78 src`). Section keys were diffed, then every
section present in both builds had its text compared, not only the sections these files borrow —
a key list shows what a release added and removed, never what it rewrote in place.

All thirteen pins in `scripts/check-prompt-upstream.py` resolve against both trees. Of the sections
this prompt does not borrow, `bg-session`, `focus_mode`, `brief` and `subagent_steer_delegation`
differ only in renamed identifiers and in the quote style the decompiler emits, so compare the
decoded string rather than the source line.

| Upstream change | Done |
| --- | --- |
| `language`, `output_style` and `scratchpad` dropped as system-prompt sections | Nothing; none was carried here. `output_style` was handled in 60edda3. The scratchpad is now a bullet inside the environment attachment, which is what leaves `agent-tools env-context` duplicating it. |
| the environment block left the system prompt for a `messages[]` attachment, leaving three bullets behind | Nothing; never carried here. |
| `fable_identity` gained a Fable 5.1 variant | Nothing; this prompt is loaded for Opus 5. |
| new `opus5_reduced_delegation` section, replacing two 2.1.235 lines that rode the `heron_brook` fallback and loosening them to admit CLAUDE.md and skills | Deliberate divergence, above. |
| new `willow_tern` section, `# Writing for the user`: a ten-rule contract for the final message | **Not adopted.** It is off by default for Opus 5, so it is a preview rather than shipped guidance, and it contradicts `## Response template`, which requires headers on every response where the new text bans them under about 500 words. Revisit if it ships on by default. |
| new `brook_heron` section, whose text arrives from client data or growthbook keyed by model | Nothing to rebase — served, not shipped. Recorded so that unfamiliar text in a future capture is recognised instead of hunted for in the binary. |
| everything `alan-default-next.md` borrows: the five `# Harness` bullets, the action-caution paragraph, `# Context management`, three `# Session-specific guidance` bullets | Byte-identical across the two builds. Now pinned by `scripts/check-prompt-upstream.py` instead of re-read by hand. |
| the environment block, which the env-context hook re-emits: its facts left the system prompt for the attachment, it gained a scratchpad bullet, and the model and knowledge-cutoff lines left it | Nothing, and that is a deferred decision rather than a finished one — a `--system-prompt-file` session now receives Claude Code's own copy as well, so most of what the hook renders is a second copy. `env_context/__main__.py` holds the finding. Its two borrowed sentences are unchanged and now pinned. |
| the legacy prompt body, which `alan-default.md` is the copy of | Nothing. The four removals above hit that branch too, and its six prose sections are unchanged between the 2.1.235 and 2.1.269 sonnet captures. Unpinned: nothing loads this file unless a prompt-test runner is given it explicitly. |

## Why the prompt says what it says

Reasoning cut from the prompt under step 3 above, kept so a future edit can tell a live rule from
cargo. Each entry names what would retire it.

### `Prefer model: haiku` on Explore spawns

Claude Code 2.1.198 (2026-07-01) changed the built-in Explore agent's model from `haiku` to
`inherit`, so an Explore spawn now runs the session's model unless the call passes one. The change
was a reliability fix, not a quality one: issue #45357 reported that a large MCP tool surface
overflowed Haiku's prompt limit and killed every spawn. That failure needs a heavy MCP install; a
session without one keeps Haiku's headroom, and Explore is scoped to locating code rather than
reviewing or analysing it.

`Prefer` carries the escape hatch, so the prompt does not spell one out: pass `sonnet` or `opus`
when a search is genuinely hard — tracing minified identifiers through decompiled chunks, say,
rather than finding a file. Haiku also drops the session's inherited `effort` setting, which the
API rejects for that model, and falls back from adaptive to plain extended thinking.

Passing the parameter per call, rather than shadowing the built-in with a user-defined `Explore`
agent: `omitClaudeMd` is set only on built-in agent definitions and is never read from frontmatter,
so a shadow re-attaches the whole CLAUDE.md hierarchy to every spawn.

`CLAUDE_CODE_SUBAGENT_MODEL_FORCE` (2.1.257, unset here) would override every per-spawn `model`,
turning this line into an instruction the harness discards; `CLAUDE_CODE_SUBAGENT_MODEL` would not,
since 2.1.251 made it a default that an explicit `model` beats.

Retire this if the built-in default returns to `haiku`, or if Explore spawns start failing on prompt
size — which would mean the MCP surface has grown into the case #45357 describes.

### `# Writing for other agents`

**`Omit by default` prices by reach, not by existence.** The earlier wording priced a line by having
been written at all, and maintenance and mis-reading cost the same wherever a line sits —
per-session cost does not. Measured 2026-09-22 on `prompt-tests/general/what-retires-this-line`:
with the old wording the whole write-up went into an auto-loaded `CLAUDE.md` and no other file was
created; with the block deleted the detail went to a separate file and a pointer stayed behind. The
reach wording takes the pointer placement without pushing out content that genuinely binds every
session.

Unresolved, and the likeliest thing to retire it: total bytes written went **up**. The objective this
was edited under asks that documentation not grow unbounded, and relocation is growth.

That question is now narrower than it was. It was open for *both* kinds of writing; 2026-09-22 on
`prompt-tests/general/doc-succession` closed the maintenance half. Editing an existing document, the
old wording, the new wording and no block at all all shrank the file, and none of the three annotated
a dead section as obsolete rather than deleting it. So the growth is not an unwillingness to remove;
it belongs to the creation case, where the reach wording moves detail out of the loaded file and
writes more of it.

What four runs on that case do agree on is a boundary, and it is the **subject**, not the licence.
Everything about the subject a task named was rewritten — including by the run whose task asked only
for a line to be added, which deleted twenty and said so. Almost nothing about any other subject was:
of the fixture's two regions that are actionable defects, one arm of three fixed one and reported it
as out of scope, and the rest went untouched, two of them by runs that said out loud they had found
them. Read the weaker claim, not the clean one — the fixture's other two untouched regions were
correctly left alone, one because it agrees with the script and one because nothing available refutes
it. If documentation here accumulates, the likeliest place is still regions no task names, and
neither bullet reaches them.

**`Claim less` no longer endorses a hedge.** It closed with *Often you are better off with a hint,
warning or a [record] marker*; deleted 2026-09-22.
`notes/workers-bullet-hint-in-fact-position.md` argues the hedge is not the cheap alternative it
reads as — a warning is still a claim, being wrong about it produces no failure pointing back at it,
and it costs every later reader a check that returns nothing, with no event that retires the line.
Measured on `prompt-tests/general/unconfirmed-cause`: with the clause and without it the agent
reached the same verdicts on all four items, ran the same verifications, and produced the same
arithmetic; a blind grader holding both sessions found no difference a maintainer would care about,
and on *hedging where checking was available*, "neither". `# Epistemic Integrity`'s No Unexplained
Residue Rule already forbids what the clause would license, and unconditionally where the clause
said *often*. A third arm that priced the hedge explicitly wrote 30% more text and rewrote
`render.py` mid-investigation where both other arms left the code alone, so stating the price
measured worse than saying nothing.

That retirement condition was tested on 2026-09-22 and it was the wrong condition. It said: retire
the deletion if an agent is found writing an unverifiable thing as a flat fact where
`# Epistemic Integrity` does not reach. On `prompt-tests/general/doc-succession`, where the writer
edits a document for a reader about a vendor client it cannot reach, that happened in all three arms
— each wrote some form of "the client negotiates TLS 1.3 by default", which nothing in the task or
the repository establishes. But the arm carrying the deleted clause restored wrote one too, and none
of the three hedged the one thing it genuinely could not check: an unscheduled, explicitly uncertain
guess, which every arm kept out of the document and reported to the user instead.

So the condition named an observation where it needed a comparison. An unverifiable flat fact
appearing does not speak for the clause; the clause preventing one does, and here it prevented
nothing. Restated: retire the deletion when an arm carrying the clause writes materially less of this
than an arm without it.

**Nothing was added here about asserting what you cannot check, and three wordings have now failed
to change that.** The behaviour is specific and it is not a shortage of care. On
`prompt-tests/general/snapshot-truncation` (2026-09-22), a fixture carrying five claims at
increasing distance from reachable evidence, every arm *verified* the claims it formed in the
session — each wrote a fake endpoint and drove the real code through it rather than reasoning
about what it would do — and every arm then rested load-bearing reasoning on what an unreachable
object store does with an incomplete multipart upload, unmarked, in the artifact and in the report
alike. What escapes audit is the premise the agent **brought with it**: background knowledge about
an external system does not arrive feeling like a claim, so nothing fires on it, while what the
agent derived in-session does. An earlier one-premise fixture, since deleted as superseded, showed
the same class across four arms.

The three wordings: *attributed, verified, or not at all*; *with what it rests on, or with what the
reader should conclude if it does not hold*; and, aimed at the node above rather than at a form,
*the ones you will not notice making are the ones you brought with you*. None produced an effect
separable from what the shipped prompt already does. The third arm's report named the vendor premise
as unverifiable and shipped a file saying none of it — the failure the line was written to defeat,
in the arm carrying the line. `grep -in "unverif\|cannot check\|not establish"` returns nothing in
either runbook artifact and three hits in an untreated arm writing for a different reader.

So the open question is no longer *what should the rule say*. Retire this paragraph when something
other than a sentence in this block is shown to reach the behaviour — and note what a rule here
would have to survive: all three arms discharged the premise well, by giving the reader a test to
run instead of a caveat to read, which is better than the marking the third wording asked for. A
line that buys markings at the cost of that trade is a regression even where the artifact looks
more careful.

**`Say what ends it` buys an exit for rules that would otherwise be permanent.** A rule an agent
writes is followed by later readers without being re-decided, and deleting it takes a human — the
objective's sharpest clause. Measured 2026-09-22 on `prompt-tests/general/retirement-policy`, a
fixture carrying four items that differ in whether they can end at all: a pin whose stated cause is
checkable here, a vendor number governed by the account's plan, a design invariant, and a bare
preference. Baseline artifact: one end-condition of four. Treated: three, in three different forms
matched to the three characters, including *this constraint ends when an accepted upload is recorded
somewhere durable outside `jobs/`* for the invariant, where the baseline wrote only *never delete
these by age*. The treated arm wrote 1202 bytes fewer, so this is not the reach bullet's open
question repeating.

Two things it did not buy, both recorded in the run: neither arm kept the bare preference out of the
register it used for the three incidents, so the line does not reach the *should this be a rule at
all* half; and the treated arm alone turned that preference into a passing test. That second one is not the
line's doing: both arms wrote three guards, the treated arm's are source-text assertions in which a
`print()` scan is trivial and a byte-exact render comparison is not, and neither transcript reasons
about the fourth item's register at all. The register defect belongs to both arms.

Retire this bullet when an arm carrying it states no more end-conditions in its artifact than an arm
without it, on a fixture whose items differ in whether they can end — or, sooner, when an arm
carrying it attaches an end-condition to a rule that has none, which is the boilerplate the run was
built to catch and did not find.

### `# Git`

The section is the only git policy a `claude.sh` session receives, because `settings.json` turns
the other one off. `includeGitInstructions: false` removes the Bash tool description's `# Git`
block — measured through the proxy on 2026-09-13, cc 2.1.269: the description loses exactly that
block and nothing else — and with it cc's `gitStatus` reminder, because both hang off one gate
(`q7()`, `chunk-dbb93264.js:69382`; the settings reference says the same). `attribution.commit`
and `.pr` set to `""` remove the attribution reminder by a documented key; the first key removes
it too, but that is observed, not documented, so both are set.

What the block said, and where each line went:

| Bash tool `# Git` line | Now |
| --- | --- |
| Interactive flags (`-i`) are not supported in this environment | Dropped. `# Using your tools` already says nothing gets a tty, and `GIT_SEQUENCE_EDITOR=… git rebase -i` works without one, so the line overclaimed. |
| Use the `gh` CLI for GitHub operations | Dropped; nothing replaces it. |
| Commit or push only when the user asks | `Commit your changes.` Push stays under `# Executing actions with care`: outward-facing, so confirm first. |
| If on the default branch, branch first | Dropped. With the line gone the probe below never saw the agent consider a branch. |
| End commit messages with the attribution lines from the reminder | `Claude-Session: <session id>`. The id resolves to the transcript — `claude --resume <id>` finds it in any project on the machine — where a JSONL path would not: it moves with `CLAUDE_CONFIG_DIR` (prompt tests write under `.claude/worktree-config/`) and dies with a container rebuild. cc uses the same trailer token for its cloud session link. |

The author is set by `scripts/claude.sh` (`GIT_AUTHOR_*`, `Claude <81847+claude@users.noreply.github.com>`);
the prompt is silent about it on purpose. The section says nothing about subagents either: the
setting is session-wide, so a subagent that commits has no policy but its parent's prompt.

The snapshot is not lost. `agent-tools env-context` renders its own `# Git status at session
start` (`environment.git_snapshot`, cc's flags and 2000-character cap), and it re-fires on resume,
`/clear` and compact, where cc's was sent once. It leaves out cc's `Git user` line — the config
name cc prints is not who the commits are by — and the main-branch line, a PR aid.

The clone sentence is the old `# Coding` line with `/tmp` replaced by the scratchpad, which did
not exist when that line was written. No run exercises it.

**What the probes cut.** `prompt-tests/general/commit-own-changes`: a one-file task in a
repository on `main` with an unrelated file already modified, nothing about git in the task.
Baseline, no section and the tool block present: no commit — "you didn't ask for a commit". The
first draft of the section was longer; it ran once whole and once per clause removed, one run
each on `claude-opus-5`:

| Draft clause | With it removed | Kept |
| --- | --- | --- |
| `without being asked` | committed | no |
| `on the current branch` | committed on `main`, no branch created, none considered | no |
| `leave pre-existing uncommitted changes as they are` | staged its own file only; every run, the baseline included, reasoned "not mine, leave it" unprompted | no |
| `, the id from the environment block` | trailer carried the right id | no |

What that rests on: one run per variant, a toy repository with one commit and no remote. A
repository with an `origin/main` may pull toward a branch. Artifacts under
`docs/prompt-trials/commit-own-changes/`.

Measured: 7679 → 7693 API tokens (`claude-opus-4-7`), the clone line's rewrite included.

Retire or re-test when: a release renames `includeGitInstructions` or stops gating the Bash block
by it — the tool note returns beside this section and contradicts it. No capture will show that:
`capture.py` passes `--setting-sources project,local` and `settings.json` installs as user
settings, so `tools/Bash.md` carries the block either way. Read a live session's own Bash
description instead; the case shows whether the agent still commits. The hook was trimmed on 2026-09-13 and the
`Session ID:` line the trailer rule reads survived it — being unique to the hook is what kept it,
since cc's own block never states the id, only embedding it in the scratchpad path
(`…/<cwd-slug>/<session id>/scratchpad`). Retire this clause if that line ever goes; Bash
subprocesses would still carry the id as `CLAUDE_CODE_SESSION_ID`, but no text would say so. When a run shows the agent branching, asking before a
commit, or sweeping foreign changes in — those are what the cut clauses would have said.

### Subagents: `run_in_background: false` on every Agent call

Until 2026-09-16 this was a harness guarantee rather than a rule: a `PreToolUse` hook on `Agent`
rewrote the parameter to `false` on every call, and the bullet stated the foreground as a fact
about the session. The user asked for a prompt rule instead, so the model now decides per call
and nothing checks it.

`CLAUDE_CODE_FORK_SUBAGENT=0` in `settings.json` is the precondition, not a second enforcement.
With the fork gate on, `run_in_background` is omitted from the Agent tool's input schema outright
(`rc() || Z8()`, `src/chunk-dbb93264.js:171779`) and the rule would be unfollowable.

Each clause was measured or read out of the source, not assumed:

- **`false`, not omission.** Claude Code backgrounds unless the parameter is literally `false`
  (`q4o`'s last term `!s && r !== !1`, `src/chunk-dbb93264.js:103955`). The clause exists because
  omission is the failure mode and it is invisible — a call without the parameter reads like any
  other call. Measured 2026-09-16 with the hook removed and the old bullet still in place: 3 of 3
  Agent calls omitted the parameter and all three backgrounded. That run's own agent noticed —
  "All three ran in the background and returned via task notifications instead. The guidance does
  not match this session's behavior."
- **Concurrency is not a reason to background.** Several Agent calls in one assistant message run
  concurrently in the foreground, so the strongest legitimate pull toward backgrounding does not
  hold. Without the clause the model has a good reason to background in exactly the case that
  needs several agents at once.
- **The tool description recommends the opposite.** The Agent tool description and the
  `run_in_background` property's own `.describe()` both say to background by default and offer
  "so the user can hand you other work" as the reason. Named and overridden, that is a resolved
  conflict; unnamed, it is an unresolved one the model settles per call.
- **`Default` carries the escape hatch**, as in ``Prefer `model: haiku` `` above, so the prompt
  spells out no exception.

Dropped from the old bullet and not replaced: "never report an agent as still running and never
wait for a notification that the launching call already answered". Both were true only while
nothing could background. A backgrounded agent now genuinely is still running and a notification
genuinely follows.

`prompt-tests/general/subagent-foreground-default` is the check, and the only thing standing
between this rule and silent decay. Measured the same day, same task, hook gone in both arms: with the old bullet, 3 of 3 Agent
calls omitted the parameter and all three backgrounded; with this bullet, 9 of 9 across three
trials passed `false`, none backgrounded, and every report returned as the launching call's own
tool result. The trajectories were deleted on 2026-09-19; these counts are the surviving record.

**Unverified, decide at the next edit to this bullet:** no green trial's reasoning weighed the
Agent tool's description against the prompt, and one of the three named neither the parameter nor
the foreground at all while still passing `false`. So the override clause has no measured
behaviour behind it — it may be what keeps the conflict from being weighed, or it may be text the
first clause already covers. Removing it and re-running the case is what would tell them apart.

Retire this if `settings.json` moves to `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`, which forces the
foreground with no help from the model and makes every clause here dead text.

### Backgrounding a wrapped command: `run_in_background: true` by default, `--background` by exception

The prompt names one default — `run_in_background: true` on an ordinary `agent-tools run` —
and gates `agent-tools run --background` behind one trigger: the job must survive the call
being killed, by a `TaskStop` or at a timeout the command is not promoted out of.

This is a preference the user stated on 2026-09-14, about this bullet: the default should not
be `--background`. No measurement forced it, so it can be revisited by asking. What supports
it: a detached run gives up the task id and the harness's completion notification and delivers
only `final(<code>)` on the status channel, which arrives on the next tool result or user turn
rather than waking the agent — so the default path is the one that reports, and the flag is
what you pay for surviving a kill. Both sides of the trade are in the prompt already, which is
why no reason for the ordering is.

Before the edit the bullet named `run_in_background: true` first and then described
`--background` at twice the length with no trigger and no cost stated in contrast. Length and
final position were doing the recommending; that is what changed, not the facts.

`docs/agent-tools-status-reference.md` was reconciled in the same change — its "Delivery" and
"kill boundary" sections each named `--background` as the form to reach for whenever a job
outlives its call, which contradicts the prompt's gate. That doc is the prompt's exhaustive
half, so an agent that reads it gets whichever default it states.

`skills/telegram-hitl/SKILL.md` was brought under the same gate: its hours-long waiter now
runs as a harness background task, because a detached one delivers no completion notification
and the answer would sit unread until something else gave the session a turn. Its proxy keeps
`--background` and now says why — a harness background task is session-scoped and the proxy
has to outlive the session that starts it.

The `TaskStop` half of the trigger is measured on both sides, in
`docs/agent-tools-status-reference.md`, "The kill boundary": `--background` survives it, a
harness background task is killed by it (`final(143)`).

Retire or revisit this if `--background` gains a completion notification of its own, which
would leave the flag with no cost to trade against.
