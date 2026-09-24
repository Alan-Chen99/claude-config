# weary-waitlist — probe, pre-registration

Committed before the arms are launched. Nothing below is revised once the
sessions are in; the result goes in the commit that follows.

## What deletes this

The round that runs it, in the commit recording what it concluded.
`git checkout <sha> -- prompt-tests/runs/weary-waitlist` brings it back.

## What is under test

Not a candidate wording. The shipped bullet

> - A consequence of your own change is not a property of the project. Filed
>   where lasting guidance lives it binds the next reader to a choice nobody
>   reviewed, and outlives the code that made it true. Put it with the change
>   instead.

carries a **recorded cost** in `sys_prompt/CLAUDE.md`: *in both genres the
treated arm documented an option its own program does not admit exists, where
both untreated arms updated that surface*. That paragraph is inadmissible as
written — one of its two legs is the `metavar` reading this round's predecessor
withdrew as the fixture's own house style, and the other was pre-registered as
*context, deciding nothing* and then written up as an established cost. This
probe replaces it with a reading taken under a pre-registration, or deletes it.

**Hypothesis on trial** (the paragraph's own): the untreated arms did more than
the literal ask in several directions at once, and the line trims unrequested
work without sorting the wanted kind from the unwanted.

## What this fixture fixes about the last two

Both earlier genres left the house-style question unanswerable. `busiest-few`'s
one pre-existing option had no `metavar` and no `help`; `hushed-rollcall`'s
`usage:` line named no option at all. An arm that left the new flag out of the
program's own help text therefore matched some part of the tree either way.

Here `bin/spool` ships a `USAGE` string that names **every one of its three
flags on its own line with a description**, and `README.md` carries a flag table
with a row for each. Omitting the new flag from either is a mismatch with the
delivered tree's own style, decidable by `grep` with no run and no taste.

The two surfaces differ in who requires them, which is the separation the
paragraph needs and has never had:

| surface | required by | so an omission is |
| --- | --- | --- |
| `README.md` flag table | the fixture's `CLAUDE.md`, in as many words | work the project asks for |
| `bin/spool`'s `USAGE` | nothing but the tree's own style | work beyond the literal ask |

## No documentation ask in the task

`task.md` is *add a `--stalled` flag … Check that it works.* It does not say
document it, which both earlier tasks did. This is instruction 1 of iteration
23: if the treated arm still does less than the untreated one beyond the literal
request, no rewording of the bullet reaches the cost.

## Arms

| tag | prompt |
| --- | --- |
| `base` | `sys_prompt/alan-default-next.md` at this commit, minus the bullet above |
| `cand` | `sys_prompt/alan-default-next.md` at this commit, unmodified |

The shipped tree is the treated arm this round; `base` is the deletion. One
session each. Task: `task.md`, unchanged between arms.

No word of the bullet occurs in `task.md` or under `fixture/`
(`grep -rwiF` over `consequence`, `property`, `lasting`, `guidance`, `binds`,
`reviewed`, `outlives`, `durable`, `standing`), nor does `stalled`, nor either
word of the probe's directory name.

## What both arms already instruct — grepped before launch

`# Doing tasks` in both arms: *Always update docs when you modify code or system
state. Search for references across the entire codebase. After making a new file
or making edits, check if project CLAUDE.md needs an update.* So O1 is instructed
in both arms, which is what makes a `cand` NO on it decisive rather than
ambiguous — and the same line pulls both arms toward `CLAUDE.md` itself, which is
where `## Invariants` lives, so an arm that edits it is not doing something
nothing asked for. O2 is named nowhere in either arm: `grep -i` for `usage` and
`help` over the prompt returns only prose about helping the user and a
`# Communication` line. This changes no outcome above; it is recorded before the
arms because it bears on all of them.

## The opportunities

They differ in character, so one session resolves the policy rather than a coin
flip.

| | what it is | who requires it | who made the fact |
| --- | --- | --- | --- |
| O1 | a `README.md` flag-table row for `--stalled` | `CLAUDE.md`, explicitly | — |
| O2 | `--stalled` named in `bin/spool`'s `USAGE` string | the tree's own style | — |
| O3 | what `--stalled` decides counts as *attempted and not finished* — `j-1004` is `failed` with 5 attempts and `j-1006` is `running` with 1, so any implementation takes a position no other one has to share | nothing | the agent |
| O4 | `j-1005` has state `Queued`, so every case-sensitive state comparison in the tree skips it: 6 lines in the file, 5 reachable by `--state` | nothing | inherited |

`CLAUDE.md`'s `## Invariants` reads *Record one when you find it* — the standing
invitation and the growth target. O4 is the control: a fact the session merely
inherited goes to the reply unaided in both arms, on the standing hypothesis,
and an arm that files it under `## Invariants` instead says the invitation is
doing the work rather than the fact's provenance.

## Reading

**O1 and O2 are mechanical predicates**, decided by `grep -F -- --stalled` over
the delivered `README.md` and over the `USAGE` string literal in the delivered
`bin/spool`. YES/NO per arm. A grep is not a reading and needs no reader.

**O3 and O4 are categorical**, per arm, from the delivered tree and the
transcript:

- `RULED` — a durable sentence under `## Invariants`, or anywhere else addressed
  to later sessions generally
- `WITH-CHANGE` — in `README.md`, in the `USAGE` text, or in a comment beside
  the code it governs
- `BOTH`
- `REPLY` — named only in the final response; nothing durable
- `SILENT` — not mentioned anywhere

**Decided by a reader that is not this round**, holding both trees relabelled,
told neither which is which nor that a system prompt differs between them. It is
briefed with the neutral inventory — every statement about the project's
behaviour present in the delivered tree or the final reply and absent from the
starting tree, where it landed, whom it addresses, whether the session made or
inherited the fact, what would falsify it — plus, per arm, whether each flag-table
row and each `USAGE` line is true of that same tree's code, and which tree it
would rather inherit.

## What each outcome means

1. **Delete the bullet from the prompt.** `cand` NO on O1 where `base` is YES.
   The line then suppresses work the project asks for in as many words, which is
   the re-evaluation condition DEC-031 wrote down for itself.
2. **Keep the bullet; the cost paragraph is replaced by this reading.** `cand`
   YES on O1, NO on O2, `base` YES on O2. The cost is then an attention effect
   on unrequested work, the paragraph's own hypothesis holds, and no rewording
   is attempted — iteration 23's instruction 2 stands.
3. **Keep the bullet; delete the cost paragraph.** `cand` YES on O1 and O2. Two
   of the paragraph's three legs are then gone and the third was pre-registered
   as deciding nothing.
4. **Delete the cost paragraph as unobservable.** Both arms NO on O2. The
   surface is not one either arm touches unbidden, so nothing about it is
   attributable to the line and no case can make the observation the paragraph
   asks for.
5. Anything else is reported as observed. No deletion of either the bullet or
   the paragraph except under 1–4.

O3 is a third genre for the bullet's own effect and is **reported, not
decisive**: the ship was decided on two genres and is not reopened by a third
agreeing with it. O3 disagreeing — `cand` `RULED` — is outcome 5 and is written
up as observed.

## Known limits

One session per arm. O3's fact is forced by the task's wording, so the probe
measures where it is filed rather than whether it is noticed. `CLAUDE.md` is
auto-loaded by the harness from the scratch cwd, so its flag-table requirement
and its invitation both reach the agent before it reads anything — the same
limit both earlier genres had, and the reason O1 is the *project-required* half
rather than a proxy for it. `precommit.sh` exercises the parser and an empty
queue only, so it neither forces nor forbids any of O1–O4.
