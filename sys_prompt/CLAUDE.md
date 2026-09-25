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

### A session on this machine is not evidence about this file until its snapshot says so

`scripts/claude.sh` loads the **installed** checkout's copy, and `/repos/claude-config`
is still on the pre-round-11 fork: its `# Writing for other agents` is `Omit by default`
and `Claim less`, and `# Doing tasks` still carries the docs order. The development
branch has never been merged, so every edit recorded in this file reaches the
prompt-test runners and nothing else. Read out of the `prompt_snapshot` attachments in
`e828eab7`'s own JSONL on 2026-09-24.

The specimen the owner named therefore had `Omit by default` in front of it while it
wrote four durable additions, and had neither `Say what ends it` nor the
self-consequence bullet. It is one more null for the deleted wording and says nothing
about the live one. Grep a session's own snapshot for the line before citing it.

Retire this when `git merge-base --is-ancestor` puts the branch inside the installed
checkout.


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

**`Omit by default` is deleted, and its reach half before it: on the compression case an arm
carrying it and one without it were indistinguishable, each making an unrequested false claim.**
What the wording bought was attention to readership, and attention argues in whichever direction
the task favours. Hypothesis: the failure it names is not an act the agent performs — a document
acquires a claim while a sentence is being written, not at a moment where adding could be
declined. Bring it back when a transcript shows an agent declining a specific addition as costing
more than it is worth, the reasoning tracing to a line rather than the task.
`prompt-tests/general/halve-the-runbook` stays whatever this says, on the user's direction: the
user set that fixture's shape.

**Growth has a moment: a document soliciting additions, met by a fact the session has just
established.** Measured across two genres: each treated arm left the soliciting document untouched
and put the fact where the project already required the option described, naming the line's own test
while declining the edit. The trade is reader-perceived quality against a rule only a human removes —
blind readers have twice preferred the arm that grew. Two accounts of why the fact moved were
withdrawn; every fixture behind them required the option documented, so no round has said what the
genres differ in. A third genre, repairing documents a change has falsified, shows neither the declining nor a
soliciting edit in either arm; what separated the arms there was volume, confounded with how much
each arm found out, and volume has since stopped being the thing worth counting. Retire the bullet
when an arm carrying it extends the soliciting document on `prompt-tests/general/hushed-rollcall`.

**What it costs: a true inherited fact, declined by name.** On a task with no documentation ask, an
arm carrying the bullet cited it — *a consequence of my own change isn't something I should record
as an invariant* — about a property that predated the session, and filed it in a code comment where
the arm without it wrote the standing rule. Hypothesis: the bullet is applied by position, so a
heading soliciting rules reads as the thing denied whatever the fact's provenance. The help-surface
cost recorded here before is deleted: on the one genre whose program enumerates its own flags, both
arms updated it. It is also read as a two-way test, and passing it licenses: an arm weighing a second
durable home for a fact reasoned *the append-only index behavior is a genuine durable design
property, distinct from just being a side effect of my change, so it deserves a place among the
conventions too, even though it's already noted in `docs/layout.md`* — the bullet's own distinction
supplying the warrant for the copy. Retire this when an arm carrying the line records an inherited property under a
soliciting heading as fully as an arm without it, on `prompt-tests/general/weary-waitlist`.

**The two bullets stated one rationale twice, and the copy is cut.** *Followed without being
re-decided* and *binds the next reader to a choice nobody reviewed* are one claim in two wordings,
with nothing saying which governs — step 2 above; the cut went from the second bullet, whose other
leg is the block's only rationale specific to its own subject. Both arms then left the soliciting
`CLAUDE.md` byte-identical, so the surviving bullet reaches its placement without the copy. Limit:
only the uncut arm's reasoning raised the heading at all, so the short wording is untested against
a session that considers it. Restore the copy if an arm carrying the cut block extends a soliciting
document that an arm carrying the uncut one leaves alone, on
`prompt-tests/general/hushed-rollcall`.

**The preamble is kept, on its first isolation.** An arm carrying it sourced a checkable number
where an arm without it stated the same number bare, and they matched on every other reading.
Hypothesis: naming the reader who *will act on it as a premise* separates a value that reader
can check from one it cannot tell from the hearsay beside it. Confounded — the sourcing arms
invoked `prompt-engineer-v2` and the bare one did not. Retire it when an arm without it sources
as much as one with it on `prompt-tests/general/inherited-project`.

**No bullet here asks for claim-handling, and what sorts a premise is the sentence's job rather
than the agent's attention.** A premise gating an act the reader performs is recorded as a check
with no line asking for it. One inside a sentence explaining how a step works is asserted flat —
by a session that had named that same doubt in its own `uncertainties` and reported it as
documented, so *no wording can reach a passing sentence* is withdrawn. Hypothesis: a doubt is
routed to where the reader acts, and a descriptive sentence offers nowhere to put it, so it is
dropped rather than declined. Retire this deletion when an arm carrying such a line qualifies a
premise inside an explanatory sentence where an arm without it asserts it flat, on
`prompt-tests/general/maintainer-briefing`.

**`Say what ends it` reaches the rule whose end is a design change rather than an observation — the
one an agent gives the history of and leaves standing.** Rules that end on an observation get their
exit unaided, in both arms. Hypothesis: an exit is written once the agent can picture the act.
Isolated against a preamble-only arm, so the effect is the bullet's and not the block's. What it
produces is a *document template* carrying an exit as one field, not four sentences — so it reaches a row where no act is picturable and writes a thin exit anyway.
That looked like the predicted harm; a blind reader contradicted it, finding that the arm applying
the template uniformly was also the one that filed a bare preference *as* a preference where the
arm without it stated it flat with no warrant. Retire it when an arm carrying it names no more
exits than one without, on `prompt-tests/general/retirement-policy`.
Against the owner's own specimen it is now tested and not refuted: the whole block was
ablated on a fixture built from that commit's shape, and on both of the fixture's defects the
arms did the same thing, so the block is not what decides a defect found outside the task.
See `# Completeness` below for what does.

**Two wordings that tell the agent to act rather than record were decided and not shipped**
— *A note telling the next reader to avoid something is a fix you did not make* and *finding
out costs less than the rule you would write instead*, both saturated on three fixtures that
made the fix or the check part of the task, so the arms took it either way.
`git checkout d530b4ed -- prompt-tests/runs/slate-harbor`, `... bronze-kettle` and
`git checkout 96ffd5b7 -- prompt-tests/runs/amber-thicket` restore those three probes. What
separates the owner's specimen from all three is that the fix was left undone with the task
finished, and nothing in this block reaches that: see `### # Completeness` below.

**Scope is decided, and no wording ships.** *A rule's scope is a claim. Wording one wider
than you checked asserts the cases you did not look at — narrow it to those you did, or check
the rest* ran against a bare arm, on a task adding one report variant and saying *document it*.
The arm carrying it shipped the failure the line names: two entries sharing one template *so*
differ in the dataset and nothing else, which one render refutes — give them different
`run_date` values and a second line differs — where the bare arm stated that coupling correctly.
The owner's specimen does the same, asserting *"`$N` is the (N+1)-th whitespace-separated
word"* off a single-digit probe. Hypothesis: the unchecked half of a claim is invisible while
the sentence is being composed, so a line naming it changes nothing; what catches it is
rendering the two queries. What
separated the trees was repair — the change falsified `templates/CLAUDE.md`'s opening, the
treated arm rewrote that sentence, the bare arm *added a minimal amendment documenting this
exception* beneath it and left a file asserting and denying one rule. So *a note telling the
next reader to avoid something is a fix you did not make*, read saturated at 34, is not
saturated where the note contradicts a rule the change just falsified. Ship a wording here when
an arm carrying it states no claim its own tree refutes where a bare arm does —
`git checkout 4cb01c30 -- prompt-tests/runs/pewter-dial`.


### `# Completeness`: a defect found on the way

**`A defect found on the way is one of those items: reporting it is not resolving it. Fix it
when the only thing stopping you is that nobody asked; escalate when the call is genuinely
someone else's. Report both.`** A defect the agent trips over is not a *scoped* item, so the
No Deferral Rule above it does not cover one, and its *escalate to the user* clause licenses
stopping at the report. Both arms of an ablation stopped exactly there and said why in their
own reasoning — *"outside my current scope but worth flagging in notes rather than fixing"*,
*"should I fix it or just report it?"*, *"touches every rendered page's output, so rather than
bundling a fix into this change, I should flag it clearly"* — each naming the one-line fix in
the reply and leaving the code alone. The owner's specimen stopped a step earlier still, never
naming its fix at all. So reporting is saturated and is not the lever; the fix is. The owner
settled the trade no measurement here can: *"the 'scope creep' is acceptable, since this
otherwise just never get fixxed"*, and *"suppose it just report to me only. then what i do
with that? and to report to me it still have to do the work of understanding how it works. i
have one sensible option which is for this to get fixed."*

What it buys: the arm carrying it made the one-line fix and pinned it with a test the existing
suite could not have caught, while leaving the fixture's other defect — two filenames the
build cannot both honour — unrenamed and escalated, which is the call the tree does not
settle. What it costs, from the blind reader: that arm reached into shared rendering while
nominally adding a flag, so every page's bytes changed; it filed that under *unexpected
change* rather than as a decision the owner could decline; and it offered a narrower menu on
the escalated defect than the bare arm did. Hypothesis: *fix it* is an act the agent can
picture and *needs no decision but yours* is a test it can apply, where a line about what to
write reaches a choice already made.

**Its harm case is run, and the line is not refuted by it.** A second genre put a construct in
the code that reads as silent data loss — `list({row.id: row for row in rows}.values())` — and
made it load-bearing, the source export repeating one row per page boundary. Both arms opened the
export doc before touching anything, both then left the construct alone, and both said what their
view rested on. So the harm this line was suspected of — changing something deliberate because it
reads as a defect — is not reached where the warrant sits in a document the project already has:
`# Doing tasks` sends every arm to the documentation first. A probe that wants that harm has to
put the warrant somewhere the task gives no reason to look.

**What it costs, measured: what the agent escalates, it also cements.** The same run's other
anomaly was real — `--top 3` prints the three smallest where the README and the flag's own help
say largest. The arm carrying the line caught it from reading the code, escalated it with the
one-word fix named and both resolutions offered, and in the same delivery wrote two tests
asserting smallest-first, so accepting the fix it recommends fails its own suite and nothing in
its reply says so. The arm without the line never saw the defect, so its tests do not fight the
fix. A blind reader holding both preferred the escalating tree on its reply and the other on its
files, in those terms. Hypothesis: escalation settles the question for the rest of the session —
having decided the call is someone else's, the agent treats the current behaviour as correct in
everything else it writes, and a clause about what to report reaches none of that. This is the
owner's *"i have one sensible option which is for this to get fixed"* from a second side, so it
argues for the *fix* half rather than against the line.

Two limits on that run. The **noticing** was one draw each and the blind reader read it as
attention rather than instruction, naming two other places where the same arm was simply more
careful; what is not a draw is that arm quoting the conflict in its own notes — the task's
*existing flags keep working as they do now* against the fix-what-you-find guidance — and
choosing to escalate. So a fixture for this line must carry no sentence that reads as freezing
behaviour, or it measures the escalate branch whatever the arms do. And of 38's two costs, the
narrower menu did **not** reproduce: the carrying arm named the one-word fix and both
resolutions. The *unexpected change* framing did, but neither arm presented any change it
actually made as declinable with a revert named, so that is this genre's baseline and not the
line's cost.

Retire it when an arm carrying it takes a call the tree does not settle — renames a file,
changes a rule's semantics — or when an arm without it fixes a defect the carrying arm leaves
named and undone. `git checkout f75aceb6 -- prompt-tests/runs/partial-regeneration` restores the
probe all three runs were made on, its pre-registrations included, and
`git checkout a247868e -- prompt-tests/runs/spend-window` the probe the harm case ran on.

### The `pre_output.record` reminder, and why only one rule is left in it

`src/claude_config/pre_output/record.py` prints its `RULES` into the tool result of a call
`## Before response` makes mandatory, so every line there is a system-prompt line with a
`NEVER` in front of it. `NEVER reply to user if uncertainties remain. Do more verification and
research` is deleted. `# Epistemic Integrity` already states the rule *with* the branch this
wording drops — investigate **or** escalate — and `## Before response` already makes the
re-record discretionary, so three wordings stood with nothing saying which governs (step 2
above).

What the arms showed: on a case whose items differ in whether a doubt can be discharged at
all, every arm disproved the task's own account of an incident before writing about it, and
every arm replied with residual doubt still listed — the arms carrying the line included, one
tool call after receiving it. So the line neither buys the verification it exists for nor is
obeyed. Where it did act, it added durable text: one arm answered it with five further tool
calls that rewrote a pinned dependency's comment around a reproduction command, and documented
an environment-variable name the session had itself invented. Its cost is paid in what gets
written down, which is what the deletion is for.

Limits: it acted in one of two draws under the same treatment, and that draw's extra work did
scope one claim more narrowly than the session had. The untreated arm is n=1 and its tree
carried three statements a blind reader falsified — all written before that arm ever called
`pre_output.record`, so the line could not have prevented them.

Restore it when an arm without it replies as if a doubt were settled where an arm with it
either resolves the doubt or reports it, on `prompt-tests/general/retirement-policy`.


### `## Required notes`

The owner's intent, stated on the channel 2026-09-24: the bullets exist because
these things "will not otherwise get surfaced, or not as-reliably", and they are
**best effort** — "the important is they are sometimes surfaced", so that a
recurring context waste eventually reaches the user instead of staying hidden.
The requirement is a rate across sessions, not an act in any one of them.

That is what makes the block un-ablatable by the reading this repo runs. An arm
without a bullet that surfaces the same item once says nothing about a rate, and
two rounds were spent measuring one bullet that way. Their arms are still worth
what they showed about the *other* question: both arms of iteration 31 wrote the
same two standing rules into a soliciting `## Agent Policy` and both named them in
the reply, neither under `unexpected change:`, and a blind reader holding both
sessions separated them on nothing load-bearing. So a further bullet naming rules
by name is unwarranted — what routes a rule into the reply is the obligation to
say what the change was, which every arm has.

What `unexpected change:` collected that nothing else did, in the one draw that
showed it: the arm carrying it named a file it had edited and restored and the
cache directories its test runs left behind; the arm without it named neither.
Collateral change, not durable prose.

No case owns this block and none should: its warrant is the owner's use of it, so
price a bullet by what it costs when it fires and not by whether a bare arm
reaches it once. Retire a bullet when the owner says it is not read.


### `# Doing tasks`: the docs order is deleted, and what a docs order can still buy

The line was *Always update docs when you modify code or system state. Search for
references across the entire codebase. After making a new file or making edits,
check if project CLAUDE.md needs an update.*

**Its repair half is saturated in a second genre, and the second genre is the hard
one.** Iteration 28 deleted the line on a tree whose auto-loaded `CLAUDE.md` indexes
every document, and recorded the bet it could not test: a tree that hides its
documents, repaired by an agent that searches narrowly. Iteration 32 built that tree
— conventions and a build command in `CLAUDE.md`, no index, `docs/` reachable only by
looking, a task naming no document — and falsified nine statements across four files
with the two changes it asked for. Three arms, one bullet apart. **Every arm repaired
or deleted every falsified statement, the arm with no docs bullet included**, and a
blind reader holding all three trees found no stale sentence in any of them. The half
of the line the owner wanted — a change leaves a document elsewhere false — is done
without it.

Hypothesis for why: the falsified set is enumerable from the change, and an agent
that has just made the change enumerates it. The untreated arm's reasoning listed the
four documents it had falsified before writing any code. What a standing order adds
to a list the agent is already holding is nothing.

**What separated the arms was the opposite half.** Unfalsified prose — new sections,
new rationale, explanation the change did not make necessary — ran 44 lines in the
untreated arm and 27 in the arm carrying the line above, and four standing
instruction-sentences each. An arm carrying a bullet that states what the obligation
*excludes* — *That repair is the documentation a change owes; what the change could
newly explain is not* — wrote 6 lines and two. Its reasoning shows the mechanism
rather than only the artifact: it enumerated the falsified documents as a list and
routed its three genuine discoveries into its reply, and not one of its narrowing
decisions gave a documentation-scope reason — every one was about implementation
scope or about what the user had asked for.

Not shipped. The candidate's first sentence is the saturated half, and shipping a
saturated sentence to carry an effective one is the duplication step 2 above forbids.
Its second half is confounded at n=1: that arm also declined the code review both
other arms ran, and shipped the one live defect of the three, an uncaught
`OverflowError` on an absurd duration. Nothing in its quoted reasoning connects the
two, which weakens the confound without removing it.

**The exclusion was isolated and it is still not shipped, for a cost that replicates.**
A standalone wording — *A change owes documentation only where it made a document
false; what it could newly explain, it does not owe* — was run against a bare arm on
two fixtures, each with its investigation depth fixed by stating the load-bearing fact
in the auto-loaded file. It cuts unfalsified prose four- and sevenfold, adds no
falsified statement left standing, and the arm carrying it names the rule in its own
reasoning: *matching the rule that docs only need updating when a change makes them
false.* The harm predicted for it was refuted adversarially — on a runbook whose
restore procedure every step of stays accurate while the procedure stops reaching its
stated end, both arms amended the step, so the exclusion is not read as a licence to
ignore a document that broke without going false.

What it costs is the accuracy of the prose it does write. In both probes the arm
carrying it shipped exactly one sentence false against its own delivered code — a cost
claim missing the *write* qualifier that made it true, and a failure mode claimed to
cover a case the code leaves invisible — and the bare arm shipped none in either, while
writing three times as much. The mechanism is the wording's own: what it cuts is the
qualifying clause that scoped a claim. That is the objective's own doc-error axis
pulling against its volume axis, so the volume result does not carry the edit alone.

The owner's answer of 2026-09-24 is the second reason and the more important one. Asked
which of the four durable additions in their own specimen they did not want, they said
the changes there "dont make sense": the additions do not belong where they were put,
do not solve the problem, and introduce new problems that have no solution and no owner.
The alternatives they name are four: find out whether the platform has an off switch
for the behaviour at all; remove the exposure from our own artifact; a note in the skill
header where the invoker reads it; a general gotcha in the root index. None is a volume
question, so a lever on how much a change owes is not the lever that specimen needs.

Asked again on 2026-09-24 which additions were unwanted, they kept the volunteered
inventory row — *actually ok but can be more shorter and general* — and rejected only
the per-skill rule, as *not incorrect but fairly expensive to cleanup, and likely will
only be cleaned if i ordered one*. Their account of the cause is a two-sided
mispricing: the note is written because *it looks like it only helps*, and *a research
is actually MUCH CHEAPER but was considered more expensive here*. The first side is what
`Say what ends it` already prices, and that line was absent from the specimen, so it is
untested against this failure rather than refuted. The second side is priced by nothing
in either fork, and is the open candidate.

Ship a wording here when an arm carrying it writes less unfalsified prose than a bare
arm *and* a reader running the delivered code finds no sentence in its tree false
against that code. Both probes restore in one command —
`git checkout 7fccd245 -- prompt-tests/runs/amber-ferry` for the hidden-docs tree,
`git checkout f04a01d4 -- prompt-tests/runs/tin-meridian` for the runbook whose
procedure breaks without going false.

`output-styles/` keeps the unwidened fork of the deleted sentence and
`sys_prompt/alan-default.md` keeps the whole line; neither was in any arm, and
`settings.json` sets `outputStyle: default`, so nothing loads the first.


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

**What the probes cut.** With no section and the tool block present the agent does not commit —
"you didn't ask for a commit" — so the section is what produces the commit at all. Each clause of a
longer first draft was then removed in turn; none of the four changed the behaviour, so none of
them is in the shipped section:

| Draft clause | With it removed | Kept |
| --- | --- | --- |
| `without being asked` | committed | no |
| `on the current branch` | committed on `main`, no branch created, none considered | no |
| `leave pre-existing uncommitted changes as they are` | staged its own file only; every run, the baseline included, reasoned "not mine, leave it" unprompted | no |
| `, the id from the environment block` | trailer carried the right id | no |

What that rests on: one run per variant, a toy repository with one commit and no remote. A
repository with an `origin/main` may pull toward a branch.

Measured: 7679 → 7693 API tokens (`claude-opus-4-7`), the clone line's rewrite included.

Retire or re-test when: a release renames `includeGitInstructions` or stops gating the Bash block
by it — the tool note returns beside this section and contradicts it. No capture will show that:
`capture.py` passes `--setting-sources project,local` and `settings.json` installs as user
settings, so `tools/Bash.md` carries the block either way. Read a live session's own Bash
description instead; `prompt-tests/general/commit-own-changes` shows whether the agent still
commits. The hook was trimmed on 2026-09-13 and the
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

`CLAUDE_CODE_FORK_SUBAGENT=0` in `settings.json` is the precondition, not a second enforcement:
with the fork gate on, `run_in_background` is omitted from the Agent tool's input schema outright
and the rule would be unfollowable. The gate's source reading, the alternative settings and the
trial counts are in `docs/subagent-backgrounding.md`; this entry justifies the bullet's clauses.

Each clause was measured or read out of the source, not assumed:

- **`false`, not omission.** Claude Code backgrounds unless the parameter is literally `false`
  (`q4o`'s last term `!s && r !== !1`, `src/chunk-dbb93264.js:103955`). The clause exists because
  omission is the failure mode and it is invisible — a call without the parameter reads like any
  other call — which is why the old bullet, stating the foreground as a fact, produced omission in
  every trial while the session read as normal.
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
between this rule and silent decay.

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
