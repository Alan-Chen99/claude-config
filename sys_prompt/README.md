# sys_prompt/

Why `alan-default-next.md` says what it says: a section per thing the prompt does, quoting it in
the heading, kept so a later edit can tell a live rule from cargo; then the ledger of wordings
measured and not shipped. How to write either is `CLAUDE.md`.

## Why the prompt says what it says

### `model: haiku` on Explore spawns

Claude Code 2.1.198 (2026-07-01) changed the built-in Explore agent's model from `haiku` to
`inherit`, as a reliability fix rather than a quality one: issue #45357 reported that a large MCP
tool surface overflowed Haiku's prompt limit and killed every spawn. That failure needs a heavy
MCP install; a session without one keeps Haiku's headroom, and Explore is scoped to locating code
rather than reviewing it. `Prefer` carries the escape hatch, so the prompt spells none out: pass
`sonnet` or `opus` when a search is genuinely hard. Haiku also drops the session's inherited
`effort` setting, which the API rejects for that model. Per-call rather than an `Explore` agent
shadowing the built-in, because the shadow would have to re-declare everything the built-in sets;
since 2.1.271 that is possible — `omitClaudeMd` is now agent frontmatter, where it used to be
readable only on built-in definitions — but the per-call form needs no upkeep.
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

The subagent half repairs a dangling reference rather than betting on a rate: the block's own
example cites an item "reported by subagent qr-3" while nothing ever asked a subagent for one.
Of what this repo installs, only the `SubagentStart` hook reaches every subagent
(`conventions/agent-responses.md` says why), so the ask belongs to the hook and the prompt keeps
only the half no hook can do — folding what returns into the parent's own block.
Unlike the arrangement `docs/subagent-backgrounding.md` records backing out of, this hook
overrides no decision the model made and spends none of the parent's attention, and every
definition in `agents/` carries a notes slot so the ask does not contradict the ones that
constrain their output. What is measured is delivery, not compliance: the one end-to-end run gave
a `haiku` `Explore` agent a `wc -l` question, which received the ask in full and returned no
block — within a best-effort block's own terms, and the whole of the evidence, so a non-trivial
task on a non-`haiku` model is the measurement still owed. Retire it with the rest of the block.

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
block and, off the same gate, cc's `gitStatus` reminder; the gate's source and everything else it
removes are the `includeGitInstructions` row of `.claude/skills/update-claude-code/SKILL.md`.
`attribution.commit` and `.pr` set to `""` remove the attribution reminder by a documented key;
the first key removes it too, but that is observed rather than documented, so both are set.

| Bash tool `# Git` line | Now |
| --- | --- |
| Interactive flags (`-i`) are not supported in this environment | Dropped: `# Using your tools` already says nothing gets a tty, and `GIT_SEQUENCE_EDITOR=… git rebase -i` works without one. |
| Use the `gh` CLI for GitHub operations | Dropped; nothing replaces it. |
| Commit or push only when the user asks | `Commit your changes.` Push stays under `# Executing actions with care`: outward-facing, so confirm first. |
| If on the default branch, branch first | Dropped. With the line gone the probes never saw the agent consider a branch. |
| End commit messages with the attribution lines from the reminder | `Claude-Session: <session id>`. The id resolves to the transcript — `claude --resume <id>` finds it in any project on the machine — where a JSONL path would not: it moves with `CLAUDE_CONFIG_DIR` and dies with a container rebuild. |

The author is set by `scripts/claude.sh` (`GIT_AUTHOR_*`), so the prompt is silent about it, and
about subagents: the setting is session-wide, so a subagent that commits has no policy but its
parent's prompt. The snapshot is not lost — `agent-tools env-context` renders its own `# Git status
at session start` (`environment.git_snapshot`) and re-fires on resume, `/clear` and compact where
cc's was sent once. The clone sentence is the old `# Coding` line with `/tmp` replaced by the
scratchpad; no run exercises it.

With no section and the tool block present the agent does not commit — *"you didn't ask for a
commit"* — so the section is what produces the commit at all. Four clauses of a longer draft were
then each removed in turn and none changed the behaviour, so none is in the shipped section:
`without being asked`, `on the current branch`, `leave pre-existing uncommitted changes as they
are`, and `, the id from the environment block`. That rests on a toy repository with no remote; one
with an `origin/main` may pull toward a branch.

Retire or re-test when a release renames `includeGitInstructions` or stops gating the Bash block
by it, which puts the tool note back beside this section to contradict it; the update skill's
row says how to check, and `prompt-tests/general/commit-own-changes` whether the agent still
commits. The trailer rule reads the hook's `Session ID:` line, unique to the hook because cc's
own block only embeds the id in the scratchpad path; retire that clause if the line goes, since
`CLAUDE_CODE_SESSION_ID` would still carry the id but no text would say so.

### Subagents: `run_in_background: false` on every Agent call

The model decides per call and nothing checks it; dropping the hook that enforced it for a prompt
rule was the user's direction, not a measurement's. `docs/subagent-backgrounding.md` carries the
harness side: the fork gate the rule needs off, why only a literal `false` keeps a call in the
foreground, the hook the rule replaced, and the alternative settings.

- **Concurrency is not a reason to background.** Several Agent calls in one assistant message run
  concurrently in the foreground, so the strongest legitimate pull toward backgrounding does not
  hold, in exactly the case that needs several agents at once.
- **The tool description recommends the opposite.** Named and overridden, that is a resolved
  conflict; unnamed, the model settles it per call.
- **`Default` carries the escape hatch**, so the prompt spells out no exception.

Dropped and not replaced: "never report an agent as still running and never wait for a
notification that the launching call already answered" — both were true only while nothing could
background. The override clause rests on no trial that weighed the tool description against the
prompt, so removing it and re-running `prompt-tests/general/subagent-foreground-default` is what
would tell it from text the first clause already covers. Retire this if `settings.json` moves to
`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`, which forces the foreground with no help from the model.

### Backgrounding a wrapped command: `run_in_background: true` by default, `--background` by exception

The prompt names one default — `run_in_background: true` on an ordinary `agent-tools run` — and
gates `agent-tools run --background` behind one trigger: the job must survive the call being
killed. This is a preference the user stated about this bullet; no measurement forced it, so it
can be revisited by asking. What supports it: a detached run gives up the task id and the
harness's completion notification and delivers only `final(<code>)` on the status channel, which
arrives on the next tool result rather than waking the agent — so the default path is the one that
reports, and the flag is what you pay for surviving a kill. Both sides are in the prompt already,
which is why no reason for the ordering is; before the edit `--background` was described at twice
the length with no trigger and no cost stated in contrast, so length and final position were doing
the recommending. `docs/agent-tools-status-reference.md` is the prompt's exhaustive half and was
reconciled in the same change, since an agent that reads it gets whichever default it states; its
"The kill boundary" measures the `TaskStop` half of the trigger on both sides. Retire or revisit
this if `--background` gains a completion notification of its own.

### `[continue]` waives review, not confirmation

It grants nothing and requires nothing: acting, and asking something smaller, were both available
already, and which one fits is situational.

Two things are deliberate. No later review is promised — unreviewed is the safer default, and a
promise of one buys reliance on a catch. And it asks rather than tells, in vocabulary that avoids
`# Executing actions with care`'s "explicitly told to proceed without asking", which an imperative
gloss named `[proceed]` walked into. A clause permitting the unread plan to be amended was measured
and dropped: the agent already does that.

Retire the question form when an arm answers it and stops where the owner expected the work, on
`prompt-tests/general/umber-trellis`; the same arms check that the marker is not read as the
carve-out's licence, and that an unread plan's status reaches the next reader's file.

### `listed without a description`

Sixteen repo skills carry the description `use only if invoked by user or workflow`, and
`skillOverrides` in `settings.json` lists them and four bundled skills as `name-only`
(`plans/2026-09-30-session-start-token-cuts.md`, #6, #9, #10), so the description that carried the
rule no longer reaches the model and this sentence states it once for the set. Retire it when cc's
`name-only` rendering states the rule itself, or when the overrides go.

## Ledger: wordings measured and not shipped

A row is a wording no longer under consideration, kept so a later round does not re-run it
believing it new. Its probe is restorable; its run is in the commit that measured it.

| Wording | Why it is not in the prompt | Probe |
| --- | --- | --- |
| `Omit by default` (and the reach half before it) | On a compression task an arm carrying it and one without were indistinguishable, each making an unrequested false claim. What it bought was attention to readership, and attention argues in whichever direction the task favours. Hypothesis: a document acquires a claim while a sentence is being written, not at a moment where adding could be declined. Bring it back if a transcript shows an agent declining a specific addition as costing more than it is worth, the reasoning tracing to a line rather than to the task. | in the prompt until round 13 |
| The second bullet's *binds the next reader to a choice nobody reviewed* | One claim in two wordings with the bullet above it, and nothing said which governed. Both arms then left the soliciting `CLAUDE.md` byte-identical, so the surviving bullet reaches its placement without the copy. Limit: only the uncut arm's reasoning raised the heading at all. Restore the copy if an arm carrying the cut block extends a soliciting document that an arm carrying the uncut one leaves alone, on `prompt-tests/general/hushed-rollcall`. | in the prompt until round 33 |
| A bullet asking for claim-handling | A premise gating an act the reader performs is recorded as a check with nothing asking for it; one inside a sentence explaining how a step works is asserted flat, by a session that had named that same doubt in its own `uncertainties`. Hypothesis: a doubt is routed to where the reader acts, and a descriptive sentence offers nowhere to put it, so it is dropped rather than declined. Retire this deletion when an arm carrying such a line qualifies a premise inside an explanatory sentence where an arm without it asserts it flat, on `prompt-tests/general/maintainer-briefing`. | — |
| *A note telling the next reader to avoid something is a fix you did not make* | Saturated where the fix or the check is part of the task: the arms took it either way. Not saturated where the note contradicts a rule the change has just falsified — there one arm rewrote the sentence and the other left a file asserting and denying one rule. | `git checkout d530b4ed -- prompt-tests/runs/slate-harbor`, `… bronze-kettle` |
| *Finding out costs less than the rule you would write instead* | Never written: every leg already ran the check unprompted, established the finding was pre-existing, named the fix and put the choice in the reply, with no standing rule in any tree. | `git checkout 96ffd5b7 -- prompt-tests/runs/amber-thicket` |
| *A rule's scope is a claim. Wording one wider than you checked asserts the cases you did not look at — narrow it to those you did, or check the rest* | The arm carrying it shipped the failure the line names, asserting a coupling one render refutes, where the bare arm stated it correctly. Hypothesis: the unchecked half of a claim is invisible while the sentence is being composed, so a line naming it changes nothing — what catches it is looking at the second case. This is the live failure: every leg of the probe above turned one instance into a project-wide rule, and the added scope, not the instance, is where the false statements were. Ship a wording here when an arm carrying it states no claim its own tree refutes where a bare arm does. | `git checkout 4cb01c30 -- prompt-tests/runs/pewter-dial` |
