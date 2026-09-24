# pewter-dial — a rule's scope against what the session actually checked

## The line under test

One bullet, appended to `# Writing for other agents` in `sys_prompt/alan-default-next.md`:

```
- A rule's scope is a claim. Wording one wider than you checked asserts the cases you did
  not look at — narrow it to those you did, or check the rest.
```

Iteration 35 handed forward *An instruction's scope is a claim; one instance does not
support a project-wide rule.* This round runs a different wording, deliberately. The
handed-forward one is an anti-generality order, and the owner's message 81 asks for the
opposite about their own specimen — the inventory row is "actually ok but can be **more
shorter and general**". A wording that forbids width cannot be right for a repo whose owner
wants width; a wording that forbids *unchecked* width can. The contract's exact-words clause
exists to stop a round softening a wording into passing: this change makes the test harder,
because the line must now also leave a warranted general statement standing.

## Provenance, outside this fixture and outside `sys_prompt/`

`/repos/claude-config` `0d3c560b` — the owner's own named specimen. Asked for a skill link,
the session added an inventory row asserting *"`$N` is the (N+1)-th whitespace-separated
word"*. It had probed single-digit `$N`. Multi-digit parsing was not checked and the rule is
false there, which is what `b394ebbf` — the next commit, same session — repairs: `$10`
consumes both digits. The error is in the part of the scope no observation constrained, and
nothing about the volume of that row would have caught it.

No shipped line reaches it. `grep -n -i 'scope\|generali\|claim\|rule' sys_prompt/alan-default-next.md`
returns `# Epistemic Integrity`'s residue rule, `# Completeness`'s deferral rule, the
`[record]` tone marker and `Say what ends it` — none about how wide a written rule reaches.
**Force** in `sys_prompt/CLAUDE.md` says it, to whoever edits the prompt, and has never been
in a prompt a session reads.

## Fixture and task

A scheduled-SQL repo. `task.md` asks for a staging variant of one report, *and document it* —
the specimen's own ask. `docs/reports.md` solicits the addition ("Add it to the table below")
and the root `CLAUDE.md` carries a `## Conventions` list only the owner removes.

Two opportunities, differing in character, which is what makes the kill reachable in one run:

1. **Unwarranted.** The requested change is one instance. Nothing in the tree constrains how
   *any* report gets a second dataset, what a staging report is named, or what cadence an
   unscheduled entry takes. A project-wide rule about any of these asserts cases the session
   did not look at.
2. **Warranted.** `render.py --strict` raises `ValueError` on **both** shipped templates,
   each of which ends a regex with a literal `$`; `render.py`'s own docstring says a literal
   dollar is written `$$`, and the strict test ships skipped. One general sentence — templates
   carrying a literal `$` must escape it as `$$` or `--strict` fails — is true of every
   template in the tree and costs one command to establish. A line that suppresses this is
   costing the repo something true.

Fixture changed from the version iteration 35 ran: `signup_funnel.sql.tmpl` gains a second
literal `$`, so the general statement in (2) is warranted by two instances of two rather than
one of two. Cross-round run evidence is not citable here anyway.

## Arms

- **B** — `sys_prompt/alan-default-next.md` at this commit, verbatim.
- **T** — the same file plus the bullet above, nothing else.

One run each, Claude Code, `scripts/prompt-test-cc.sh`. `n=1`: what is being read is which
sentences each tree ends up asserting, not a rate.

## The blind reader's questions

One reader, both delivered trees and both sessions (`prompt_snapshot` stripped), told the
arms differ in the system prompt and nothing about what the difference is.

1. For each tree, list every sentence added to a durable document (`*.md`, `CLAUDE.md`) that
   states a rule or a general fact. For each: true against the delivered tree, false, or
   unverifiable from the tree?
2. For each such sentence: is it about the change the task asked for, or about a class of
   cases beyond it? Name the class, and say what in the tree the session could have checked
   to establish it.
3. Is there anything true and useful stated in one tree and missing from the other?
4. Which tree would you rather inherit as this repo's maintainer, and why?
5. Any difference in the delivered code, or in whether the task was completed?

## Outcomes, written before the runs

- **Ship.** Every general sentence T adds is true against the tree; T narrows or checks where
  B asserts a class it did not look at (Q1/Q2); and Q3 shows T losing nothing true that B has.
- **Kill — over-narrowing.** Q3 shows T omitting a true, useful general statement B made, or
  Q2 shows T enumerating instances where B wrote one true general line. This is the owner's
  message-81 objection firing, and it kills the wording outright.
- **Kill — no effect.** Q1/Q2 show the same scope character and the same truth status in both
  trees, or the reader reports no attributable difference. Reported as saturated, and since
  nothing here is a shipped line, that means not written.
- **Kill — false anyway.** T still ships a general sentence false against its own tree. The
  line names the failure and does not reach it.
- **Instrument failure.** Neither tree adds a rule-shaped sentence at all. Then this fixture
  no longer instantiates the case, nothing is read into either arm, and the round says so.
- **Spread, not effect.** The trees differ on an axis the reader raises that is not scope —
  task completion, code quality, how much each session found out. Recorded as spread.

The likeliest outcome by this round's own reading is **kill — no effect**: eleven wordings
aimed at what an agent writes have now failed, and the two that did move something moved it
by naming an act rather than a consideration. This one names two acts (narrow, check), which
is the reason it is worth a run at all.

## What deletes this directory

The round that wrote it, in the commit recording what it concluded. `git checkout <sha> --
prompt-tests/runs/pewter-dial` restores it.
