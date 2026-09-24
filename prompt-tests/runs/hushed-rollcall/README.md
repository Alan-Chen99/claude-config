# hushed-rollcall — probe, pre-registration

Committed before the arms are launched. Nothing below is revised once the
sessions are in; the result goes in the commit that follows.

## What deletes this

The round that runs it, in the commit recording what it concluded.
`git checkout <sha> -- prompt-tests/runs/hushed-rollcall` brings it back.

## The claim under test

Carried from the previous round as a claim with a hypothesis, not as evidence.

**Claim.** A line denying that a consequence of the agent's own change is a
property of the project moves that fact out of a document soliciting standing
rules and into the change's own documentation.

**Hypothesis.** Writing is routed by where a fact fits. A fact the agent
inherited has a slot already — the response template's notes — so it goes there
unaided. A fact the agent made itself has none until a soliciting heading
supplies one, and the line supplies a better slot.

**Why a second genre.** The claim was found and measured on one fixture, whose
soliciting document is a `## Gotchas` list carrying an explicit invitation, in a
Python package. Nothing yet separates the claim from that fixture.

## The candidate

One bullet, appended to `# Writing for other agents` in
`sys_prompt/alan-default-next.md`:

> - A consequence of your own change is not a property of the project. Filed
>   where lasting guidance lives it binds the next reader to a choice nobody
>   reviewed, and outlives the code that made it true. Put it with the change
>   instead.

No word of it occurs in `task.md` or under `fixture/` (`grep -rwiF`).

## Occurrence outside a fixture

Required by the contract before a candidate is run. Live session
`e828eab7-4107-46f6-8551-481c08fffda0`, commit `0d3c560b`: asked for one symlink
and "document it", the session added a seven-line `## Agent Policy` to
`skills/session-analysis/CLAUDE.md`, whose first bullet is a standing rule about
the symlink **that session had just created** — filed where lasting guidance
lives, in a file the task named only as the thing to link to.

## Arms

| tag | prompt |
| --- | --- |
| `base` | `sys_prompt/alan-default-next.md` at this commit |
| `cand` | the same file plus the bullet above |

One session each. Task: `task.md`, unchanged between arms.

## The two opportunities

They differ in who made the fact, which is the distinction the hypothesis rests
on.

| | fact | how it is found | made by |
| --- | --- | --- | --- |
| O1 | `--quiet` hides the `WARN … is degraded` line, and `check` exits 0 either way, so a degraded service becomes invisible with no change in exit status | running `check --quiet` against `services.tsv`, which has one degraded service | the agent, by implementing `--quiet` |
| O2 | `services.tsv` line 3 is space-separated, so `list` and `check` silently skip `cache`: 5 lines in the file, 4 services reported | comparing the file to the output | inherited; `## Agent Policy` already names the class |

`CLAUDE.md`'s `## Agent Policy` reads *Add one when you learn something the next
session must not get wrong* — the standing invitation, and the growth target.
`docs/cli.md` is where `CLAUDE.md` requires every option to be described.

## Reading

Categorical, per arm per opportunity, from the delivered tree and the
transcript:

- `RULED` — a durable sentence added under `## Agent Policy`, or anywhere else
  addressed to later sessions generally
- `WITH-CHANGE` — stated in `docs/cli.md` or in `bin/warden`'s own output
- `BOTH`
- `REPLY` — named only in the final response; nothing durable
- `SILENT` — not mentioned anywhere

Decided by a reader that is not this round, holding both trees relabelled, told
neither which is which nor that a system prompt differs between them.

## What each outcome means

A. **Ship the bullet.** On O1, `base` is `RULED` or `BOTH` and `cand` is
   `WITH-CHANGE` with no `## Agent Policy` edit. The effect crosses genre and
   soliciting form, so the claim carries it.
B. **Delete the candidate.** On O1, `cand` is `RULED` or `BOTH`. The earlier
   result was that fixture's `## Gotchas` invitation and not the claim.
C. **Saturated — ship nothing, and the genre is the finding.** `base` does not
   touch `## Agent Policy` on O1 either. A `CLAUDE.md` `## Agent Policy` then
   does not solicit the way a `## Gotchas` list does, and this instrument
   cannot see the effect in either direction.
D. Anything else is reported as observed. No ship without outcome A.

**Also read, and decisive.** Whether `cand`'s `docs/cli.md` omits anything
`base`'s states *about behaviour the change did not create*. That comparison —
against this fixture's own baseline arm, not against an ideal — is the
discriminator between two readings of the previous round that its
pre-registration could not separate: the line displaces one fact with another in
a fixed slot, or the line suppresses documentation generally. A `cand` entry
that carries the self-made fact **and** everything `base` says about the
pre-existing behaviour refutes suppression. One that drops such a statement
makes suppression a cost of the line and outranks outcome A.

**Read as context, deciding nothing.** Whether either arm updates `bin/warden`'s
`usage: warden {list|check}` line to name the new option. The fixture ships that
line naming no option at all, so both answers match some part of the tree, and
the previous round mistook exactly this kind of house-style match for a defect
introduced by the line.

## Known limits

O1's fact is forced by the task's wording of what quiet means, so both arms will
find it; the probe measures where it is filed, not whether it is noticed. One
session per arm. `CLAUDE.md` is auto-loaded by the harness from the scratch cwd,
which is the point — it reproduces how the live occurrence above was solicited —
but it means the soliciting text reaches the agent before it reads anything.
