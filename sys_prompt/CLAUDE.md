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

**A session on this machine is not evidence about this file until its snapshot says so.**
`scripts/claude.sh` loads the **installed** checkout, `/repos/claude-config`, and that is still
the pre-round-11 fork: `Omit by default` and `Claim less` where this branch has
`# Writing for other agents`, and the docs order still in `# Doing tasks`. The branch has never
been merged, so every edit recorded below reaches the prompt-test runners and nothing else — the
owner's own specimen, `e828eab7`, ran the old fork. Grep a session's `prompt_snapshot` for the line before
citing the session. Retire this when `git merge-base --is-ancestor` puts the branch inside the
installed checkout.

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

Reasoning cut from the prompt under step 3 above, kept so a future edit can tell a live rule
from cargo.

**One paragraph per line the prompt stack carries** — the claim, the hypothesis behind it, and
the retirement condition: an observation that would end the line, and the case where it gets
made. A round that measures a line **replaces** that line's paragraph; it does not add a
second. A wording measured and not shipped is one row of the ledger at the end. What an arm
said, how much it wrote, which fixture it ran on and on what date stay in the commit that
measured them — a run is evidence for the round that ran it, so quoting one here spends context
on what the next round may not rely on.

That is the whole bound on this file: one paragraph per line, one row per dead wording, nothing
that is neither. Held to, it makes the file as long as the prompt has lines and no longer, with no
size set by hand. What it is worth: opening any file in this directory with the **Read** tool
attaches this whole file as a system-reminder — `prompt-tests/CLAUDE.md` states that mechanism and
how to re-check it — so every paragraph here is spent on every session that comes to edit the
prompt. `.claude/skills/prompt-tests/SKILL.md` bounds the case
corpus by the same construction — one grep against the retirement conditions below.
A round that finds it needs a second paragraph for one line has found the bound wrong: say so and
replace it, rather than appending under it.

### `Prefer model: haiku` on Explore spawns

Claude Code 2.1.198 (2026-07-01) changed the built-in Explore agent's model from `haiku` to
`inherit`, as a reliability fix rather than a quality one: issue #45357 reported that a large MCP
tool surface overflowed Haiku's prompt limit and killed every spawn. That failure needs a heavy
MCP install; a session without one keeps Haiku's headroom, and Explore is scoped to locating code
rather than reviewing it. `Prefer` carries the escape hatch, so the prompt spells none out: pass
`sonnet` or `opus` when a search is genuinely hard. Haiku also drops the session's inherited
`effort` setting, which the API rejects for that model. Per-call rather than a user-defined
`Explore` agent shadowing the built-in: `omitClaudeMd` is set only on built-in definitions and is
never read from frontmatter, so a shadow re-attaches the whole CLAUDE.md hierarchy to every spawn.
`CLAUDE_CODE_SUBAGENT_MODEL_FORCE` (2.1.257, unset here) would override every per-spawn `model`
and turn this line into text the harness discards; `CLAUDE_CODE_SUBAGENT_MODEL` would not, since
2.1.251 made it a default an explicit `model` beats. Retire this if the built-in default returns
to `haiku`, or if Explore spawns start failing on prompt size.

### `# Writing for other agents`

**The preamble** — *read cold, by a reader who cannot ask what you meant … will act on it as a
premise*. Hypothesis: naming that reader separates a value the reader can check from one it
cannot tell from the hearsay beside it; an arm carrying it sourced a checkable number where a
bare arm stated the same number flat. Confounded — the sourcing arms invoked
`prompt-engineer-v2` and the bare one did not. Retire it when an arm without it sources as much
as one with it on `prompt-tests/general/inherited-project`.

**`Say what ends it`** reaches the rule whose end is a design change rather than an observation
— the one an agent gives the history of and leaves standing. Rules that end on an observation
get their exit in either arm. Hypothesis: an exit is written once the agent can picture the act.
What it produces is a *document template* carrying an exit as one field, so it reaches rows
where no act is picturable and writes a thin exit anyway; that looked like the predicted harm
until a blind reader weighed it against the same arm filing a bare preference *as* a preference
where the bare arm stated it with no warrant, and preferred it. Retire it when an arm carrying
it names no more exits than one without, on `prompt-tests/general/retirement-policy`.

**`A consequence of your own change is not a property of the project`.** Growth has a moment: a
document soliciting additions, met by a fact the session has just established. Across two genres
the carrying arm left the soliciting document untouched and put the fact where the project
already required the option described. The trade is reader-perceived quality against a rule only
a human removes, and blind readers have twice preferred the arm that grew. What it costs is a
true inherited fact declined by name — a property that predated the session, filed in a code
comment where the bare arm wrote the standing rule. Hypothesis: the bullet is applied by
position, so a heading soliciting rules reads as the thing denied whatever the fact's provenance.
It also reads as a two-way test, one arm taking its distinction as the warrant for a second
durable copy of a fact already documented. Retire the bullet when an arm carrying it extends the
soliciting document on `prompt-tests/general/hushed-rollcall`; retire the cost when an arm
carrying it records an inherited property under a soliciting heading as fully as an arm without
it, on `prompt-tests/general/weary-waitlist`.

**The block as a whole is not what decides a defect found outside the task.** Ablated against a
fixture built from the owner's own specimen, the arms did the same thing on both of that
fixture's defects; `# Completeness` below is what reaches them. `prompt-tests/general/halve-the-runbook`
stays whatever this section says, on the user's direction: the user set that fixture's shape.

### `# Completeness`: a defect found on the way

**`A defect found on the way is one of those items: reporting it is not resolving it. Fix it
when the only thing stopping you is that nobody asked; escalate when the call is genuinely
someone else's. Report both.`** A defect the agent trips over is not a *scoped* item, so the No
Deferral Rule above it does not cover one, and its *escalate to the user* clause licensed
stopping at the report: both arms of an ablation named the one-line fix in the reply and left
the code alone, and the owner's specimen stopped a step earlier still, never naming its fix.
Reporting is saturated and is not the lever; the fix is. The owner settled the trade no
measurement here can — *"the 'scope creep' is acceptable, since this otherwise just never get
fixxed"*, and *"suppose it just report to me only. then what i do with that? … i have one
sensible option which is for this to get fixed"* — and priced the *Report both* clause
separately: *"noticing but not telling me is i think simply incorrect behavior in this case"*,
while how an unrequested fix is presented is *"an efficiency thing which agent can decide at
runtime, and i think you dont really need to prescribe"*. Hypothesis: *fix it* is an act the
agent can picture and *needs no decision but yours* is a test it can apply, where a line about
what to write reaches a choice already made.

Its harm case is run and it is not refuted: where the thing that reads as a defect is deliberate
and a document in the project says so, both arms read the document first and left the construct
alone, because `# Doing tasks` sends every arm to the documentation. A probe wanting that harm
must put the warrant where the task gives no reason to look. What the same run cost, measured:
**what the agent escalates, it also cements** — the carrying arm escalated a real defect with the
one-word fix named, then wrote tests asserting the defective behaviour, so accepting the fix it
recommends fails its own suite and nothing in its reply says so. Hypothesis: escalation settles
the question for the rest of the session, and a clause about what to report reaches none of the
writing that follows. That argues for the *fix* half rather than against the line. A fixture for
this line must carry no sentence that reads as freezing current behaviour, or it measures the
escalate branch whatever the arms do.

Retire it when an arm carrying it takes a call the tree does not settle — renames a file, changes
a rule's semantics — or when an arm without it fixes a defect the carrying arm leaves named and
undone. `git checkout f75aceb6 -- prompt-tests/runs/partial-regeneration` and
`git checkout a247868e -- prompt-tests/runs/spend-window` restore the two probes.

### `pre_output.record`'s `RULES`

`src/claude_config/pre_output/record.py` prints them into the tool result of a call
`## Before response` makes mandatory, so each is a system-prompt line with a `NEVER` in front of
it. One is left. `NEVER reply to user if uncertainties remain. Do more verification and research`
is deleted: `# Epistemic Integrity` already states that rule *with* the branch this wording drops
— investigate **or** escalate — so three wordings stood with nothing saying which governs. It
bought neither the verification it exists for nor obedience; where it did act it added durable
text, one arm answering it by documenting an environment-variable name the session had itself
invented. Restore it when an arm without it replies as if a doubt were settled where an arm with
it either resolves the doubt or reports it, on `prompt-tests/general/retirement-policy`.

### `## Required notes`

The owner's intent, stated on the channel: the bullets exist because these things "will not
otherwise get surfaced, or not as-reliably", and they are **best effort** — "the important is
they are sometimes surfaced". The requirement is a rate across sessions, not an act in any one of
them, which is what makes the block un-ablatable by the reading this repo runs: an arm without a
bullet that surfaces the same item once says nothing about a rate, and two rounds were spent
measuring one bullet that way. What those rounds do settle is the *other* question — both arms
wrote the same standing rules into a soliciting `## Agent Policy` and both named them in the
reply, so a further bullet naming rules by name is unwarranted; what routes a rule into the reply
is the obligation to say what the change was, which every arm has. What `unexpected change:`
collected that nothing else did was collateral change — a file edited and restored, the cache
directories a test run left behind — not durable prose. No case owns this block and none should:
price a bullet by what it costs when it fires. Retire a bullet when the owner says it is not read.

### `# Doing tasks` carries no docs order

The deleted line was *Always update docs when you modify code or system state. Search for
references across the entire codebase. After making a new file or making edits, check if project
CLAUDE.md needs an update.* **Its repair half is saturated, including on the tree it was a bet
about** — conventions in `CLAUDE.md` with no index, `docs/` reachable only by looking, a task
naming no document, two changes falsifying nine statements across four files. Every arm repaired
or deleted every falsified statement, the arm with no docs bullet included. Hypothesis: the
falsified set is enumerable from the change, and an agent that has just made the change
enumerates it — one untreated arm listed the four documents it had falsified before writing any
code. What a standing order adds to a list the agent is already holding is nothing.

What separates arms is the opposite half, unfalsified prose, and the wording that cuts it is not
shipped: *A change owes documentation only where it made a document false; what it could newly
explain, it does not owe* cuts that prose several-fold and survives the adversarial case (a
runbook whose every step stays accurate while the procedure stops reaching its stated end — both
arms amended it), but in both probes the arm carrying it shipped one sentence false against its
own delivered code where the bare arm shipped none. The mechanism is the wording's own: what it
cuts first is the qualifying clause that scoped the claim. That is this objective's doc-error
axis pulling against its volume axis. The owner's account of their own specimen is the second and
larger reason — the additions there "dont make sense": they do not belong where they were put, do
not solve the problem, and introduce new problems with no owner; the alternatives they name are
an off switch, removing the exposure, a note in the skill header, a general gotcha in the root
index, and none is a volume question. Their account of why such a note gets written at all is a
two-sided mispricing — *it looks like it only helps*, and *a research is actually MUCH CHEAPER but
was considered more expensive here* — whose damage is an aggregate: *if every session says
"adding this will save a little bit of time", thats how you get unbounded doc growth that ends up
costing a lot more tokens*. Each addition is locally justified by a small expected saving, so a
lever aimed at any single judgement does not reach the sum. Ship a wording here when an arm carrying it writes less
unfalsified prose than a bare arm *and* a reader running the delivered code finds no sentence in
its tree false against that code. `git checkout 7fccd245 -- prompt-tests/runs/amber-ferry` and
`git checkout f04a01d4 -- prompt-tests/runs/tin-meridian` restore the two probes.

`output-styles/` keeps an unwidened fork of the deleted sentence and `sys_prompt/alan-default.md`
keeps the whole line; neither was in any arm, and `settings.json` sets `outputStyle: default`, so
nothing loads the first.

### `# Git`

The section is the only git policy a `claude.sh` session receives, because `settings.json` turns
the other one off. `includeGitInstructions: false` removes the Bash tool description's `# Git`
block and, off the same gate, cc's `gitStatus` reminder (`q7()`, `chunk-dbb93264.js:69382`).
`attribution.commit` and `.pr` set to `""` remove the attribution reminder by a documented key;
the first key removes it too, but that is observed rather than documented, so both are set.

| Bash tool `# Git` line | Now |
| --- | --- |
| Interactive flags (`-i`) are not supported in this environment | Dropped: `# Using your tools` already says nothing gets a tty, and `GIT_SEQUENCE_EDITOR=… git rebase -i` works without one. |
| Use the `gh` CLI for GitHub operations | Dropped; nothing replaces it. |
| Commit or push only when the user asks | `Commit your changes.` Push stays under `# Executing actions with care`: outward-facing, so confirm first. |
| If on the default branch, branch first | Dropped. With the line gone the probes never saw the agent consider a branch. |
| End commit messages with the attribution lines from the reminder | `Claude-Session: <session id>`. The id resolves to the transcript — `claude --resume <id>` finds it in any project on the machine — where a JSONL path would not: it moves with `CLAUDE_CONFIG_DIR` and dies with a container rebuild. |

The author is set by `scripts/claude.sh` (`GIT_AUTHOR_*`), so the prompt is silent about it. It is
silent about subagents too: the setting is session-wide, so a subagent that commits has no policy
but its parent's prompt. The snapshot is not lost — `agent-tools env-context` renders its own
`# Git status at session start` (`environment.git_snapshot`), and re-fires on resume, `/clear` and compact where cc's was sent
once. The clone sentence is the old `# Coding` line with `/tmp` replaced by the scratchpad; no run
exercises it.

With no section and the tool block present the agent does not commit — *"you didn't ask for a
commit"* — so the section is what produces the commit at all. Four clauses of a longer draft were
then each removed in turn and none changed the behaviour, so none is in the shipped section:
`without being asked`, `on the current branch`, `leave pre-existing uncommitted changes as they
are`, and `, the id from the environment block`. That rests on a toy repository with no remote; one
with an `origin/main` may pull toward a branch.

Retire or re-test when a release renames `includeGitInstructions` or stops gating the Bash block
by it, which puts the tool note back beside this section to contradict it. No capture will show
that: `capture.py` passes `--setting-sources project,local` and `settings.json` installs as user
settings, so `tools/Bash.md` carries the block either way. Read a live session's own Bash
description instead; `prompt-tests/general/commit-own-changes` shows whether the agent still
commits. The trailer rule reads the hook's `Session ID:` line, which is unique to the hook —
cc's own block never states the id, only embedding it in the scratchpad path; retire that clause
if the line goes, since `CLAUDE_CODE_SESSION_ID` would still carry the id but no text would say so.

### Subagents: `run_in_background: false` on every Agent call

Until 2026-09-16 a `PreToolUse` hook rewrote the parameter on every call and the bullet stated the
foreground as a fact about the session. The user asked for a prompt rule instead, so the model now
decides per call and nothing checks it. `CLAUDE_CODE_FORK_SUBAGENT=0` in `settings.json` is the
precondition, not a second enforcement: with the fork gate on, `run_in_background` is omitted from
the Agent tool's input schema outright and the rule would be unfollowable. The gate's source
reading and the alternative settings are in `docs/subagent-backgrounding.md`.

- **`false`, not omission.** Claude Code backgrounds unless the parameter is literally `false`
  (`q4o`'s last term `!s && r !== !1`, `src/chunk-dbb93264.js:103955`). Omission is the failure
  mode and it is invisible — which is why the old bullet, stating the foreground as a fact,
  produced omission in every trial while the session read as normal.
- **Concurrency is not a reason to background.** Several Agent calls in one assistant message run
  concurrently in the foreground, so the strongest legitimate pull toward backgrounding does not
  hold, in exactly the case that needs several agents at once.
- **The tool description recommends the opposite**, in both the description and the
  `run_in_background` property's own `.describe()`. Named and overridden, that is a resolved
  conflict; unnamed, the model settles it per call.
- **`Default` carries the escape hatch**, so the prompt spells out no exception.

Dropped and not replaced: "never report an agent as still running and never wait for a
notification that the launching call already answered". Both were true only while nothing could
background. `prompt-tests/general/subagent-foreground-default` is the check and the only thing
standing between this rule and silent decay. **Unverified, decide at the next edit:** no passing
trial's reasoning weighed the tool description against the prompt, so the override clause has no
measured behaviour behind it — removing it and re-running the case is what would tell it from text
the first clause already covers. Retire this if `settings.json` moves to
`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`, which forces the foreground with no help from the model.

### Backgrounding a wrapped command: `run_in_background: true` by default, `--background` by exception

The prompt names one default — `run_in_background: true` on an ordinary `agent-tools run` — and
gates `agent-tools run --background` behind one trigger: the job must survive the call being
killed. This is a preference the user stated on 2026-09-14 about this bullet; no measurement
forced it, so it can be revisited by asking. What supports it: a detached run gives up the task id
and the harness's completion notification and delivers only `final(<code>)` on the status channel,
which arrives on the next tool result rather than waking the agent — so the default path is the
one that reports, and the flag is what you pay for surviving a kill. Both sides are in the prompt
already, which is why no reason for the ordering is. Before the edit the bullet described
`--background` at twice the length with no trigger and no cost stated in contrast; length and
final position were doing the recommending, and that is what changed, not the facts.
`docs/agent-tools-status-reference.md` was reconciled in the same change — it named `--background`
as the form to reach for whenever a job outlives its call, and it is the prompt's exhaustive half,
so an agent that reads it gets whichever default it states. `skills/telegram-hitl/SKILL.md` came
under the same gate; its proxy keeps `--background` and now says why. The `TaskStop` half of the
trigger is measured on both sides in that doc, "The kill boundary". Retire or revisit this if
`--background` gains a completion notification of its own.

### Ledger: wordings measured and not shipped

A row is a wording no longer under consideration, kept only so a later round does not re-run it
believing it new. Its probe is restorable; its run is in the commit that measured it.

| Wording | Why it is not in the prompt | Probe |
| --- | --- | --- |
| `Omit by default` (and the reach half before it) | On a compression task an arm carrying it and one without were indistinguishable, each making an unrequested false claim. What it bought was attention to readership, and attention argues in whichever direction the task favours. Hypothesis: a document acquires a claim while a sentence is being written, not at a moment where adding could be declined. Bring it back if a transcript shows an agent declining a specific addition as costing more than it is worth, the reasoning tracing to a line rather than to the task. | in the prompt until round 13 |
| The second bullet's *binds the next reader to a choice nobody reviewed* | One claim in two wordings with the bullet above it, and nothing said which governed. Both arms then left the soliciting `CLAUDE.md` byte-identical, so the surviving bullet reaches its placement without the copy. Limit: only the uncut arm's reasoning raised the heading at all. Restore the copy if an arm carrying the cut block extends a soliciting document that an arm carrying the uncut one leaves alone, on `prompt-tests/general/hushed-rollcall`. | in the prompt until round 33 |
| A bullet asking for claim-handling | A premise gating an act the reader performs is recorded as a check with nothing asking for it; one inside a sentence explaining how a step works is asserted flat, by a session that had named that same doubt in its own `uncertainties`. Hypothesis: a doubt is routed to where the reader acts, and a descriptive sentence offers nowhere to put it, so it is dropped rather than declined. Retire this deletion when an arm carrying such a line qualifies a premise inside an explanatory sentence where an arm without it asserts it flat, on `prompt-tests/general/maintainer-briefing`. | — |
| *A note telling the next reader to avoid something is a fix you did not make* | Saturated where the fix or the check is part of the task: the arms took it either way. Not saturated where the note contradicts a rule the change has just falsified — there one arm rewrote the sentence and the other left a file asserting and denying one rule. | `git checkout d530b4ed -- prompt-tests/runs/slate-harbor`, `… bronze-kettle` |
| *Finding out costs less than the rule you would write instead* | Never written: every leg already ran the check unprompted, established the finding was pre-existing, named the fix and put the choice in the reply, with no standing rule in any tree. | `git checkout 96ffd5b7 -- prompt-tests/runs/amber-thicket` |
| *A rule's scope is a claim. Wording one wider than you checked asserts the cases you did not look at — narrow it to those you did, or check the rest* | The arm carrying it shipped the failure the line names, asserting a coupling one render refutes, where the bare arm stated it correctly. Hypothesis: the unchecked half of a claim is invisible while the sentence is being composed, so a line naming it changes nothing — what catches it is looking at the second case. This is the live failure: every leg of the probe above turned one instance into a project-wide rule, and the added scope, not the instance, is where the false statements were. Ship a wording here when an arm carrying it states no claim its own tree refutes where a bare arm does. | `git checkout 4cb01c30 -- prompt-tests/runs/pewter-dial` |
