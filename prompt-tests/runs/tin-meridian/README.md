# tin-meridian — pre-registration, iteration 33, second probe

Deleted by the round that runs it; `git checkout <this sha> -- prompt-tests/runs/tin-meridian`
brings it back in one command.

## What is on trial, and why a second probe

The same two arms as `amber-ferry`, unchanged files:

    arm c0  HEAD, no docs bullet   /tmp/wf33arms/b0.md   6391 API tokens
    arm c1  c0 + the bound         /tmp/wf33arms/b1.md   6422

> A change owes documentation only where it made a document false; what it could
> newly explain, it does not owe.

The first probe measured the benefit: both arms repaired every falsified sentence,
and the treated arm wrote a quarter of the unfalsified prose while running *more*
verification than the bare arm — so the volume effect is not the effort confound
that blocked iteration 32. Its reasoning names the rule in its own words: *matching
the rule that docs only need updating when a change makes them false.*

It also showed one cost, and the cost is what this probe is for. The user's standing
gate is that **negative effects must be understood via adversarial testing** before a
line is added, and one observed cost is not an understood one. The first probe's R4
failure — the treated tree's documented recovery procedure no longer runs — cannot be
attributed: that arm chose an on-disk format that broke old files and the bare arm
chose one that did not, so only one arm was ever under the obligation. The arms
diverged there on `# Coding`'s backwards-compatibility line, which both carry.

**The hypothesis this probe tests is the mechanism that failure would have.** The
bullet's test is *falsity*. A document can stop working without any sentence in it
becoming false: a procedure whose steps are each still accurate stops reaching its
stated end. A rule that licenses silence about everything except falsity would leave
such a procedure broken. This fixture puts both arms under that obligation with no
design freedom to dodge it.

## The fixture

`docs/runbook.md` carries a four-step restore procedure:

    1. Stop the writer.
    2. Copy the snapshot file back into the snapshot directory.
    3. Run `warden verify` and confirm it reports `ok`.
    4. Start the writer.

The task moves each snapshot's hash out of `index.json` and into a `<name>.sha256`
sidecar, and makes `verify` read the sidecar. After that change every sentence of
the procedure is still accurate and the procedure no longer reaches `ok`: step 2
copies one file where two are now needed. The task names the sidecar, so both arms
owe the same obligation.

Three statements are falsified outright, so the repair reading has content:
`README.md`'s *A snapshot directory holds one file per snapshot*; `CLAUDE.md`'s *A
snapshot directory holds nothing but snapshot files; `warden list` treats every file
it finds there as a snapshot*; and `docs/runbook.md`'s *`warden verify` fails only
when a snapshot's bytes have changed since it was written*.

Depth is fixed the same way as in the first probe: the `warden list` behaviour the
natural implementation trips over — every file in the directory read as a snapshot,
so a sidecar lists as a second copy of its own snapshot — is stated in the
auto-loaded `CLAUDE.md` as a convention, not left to be discovered.

## Readings

- **Q1 the procedure.** Follow `docs/runbook.md`'s restore steps literally against
  the delivered tree. Does step 3 report `ok`? If not, does any delivered document
  say what else the operator must do?
- **Q2 falsified statements.** The three above, plus any other sentence the delivered
  change makes false: repaired / deleted / left standing.
- **Q3 unfalsified additions.** Prose added that the change did not make necessary,
  in lines, with per-file accounting.
- **Q4 work done.** Tool calls; checks run beyond the shipped suite; whether the
  delivered `warden list` still lists each snapshot once; defects.

## Outcomes, written before launch

- **N1 the harm is real.** c0's tree makes the restore procedure reach `ok` — the
  step amended, or the sidecar requirement stated where the operator will read it —
  and c1's does not. The bullet's falsity test is too narrow, the wording is not
  shipped as written, and this round records what a repaired wording must say.
- **N2 no harm.** Both trees make the procedure runnable. The bullet costs the
  procedure nothing, the first probe's R4 failure stands attributed to the format
  choice rather than to the rule, and the line ships.
- **N3 saturated the other way.** Neither tree makes it runnable. The failure is the
  genre's and not the bullet's — a true-but-unrunnable procedure is missed with or
  without the line — and the line ships on the first probe, with this recorded as the
  failure no wording at this position reaches.
- **N4 reversed.** c1 amends the procedure and c0 does not. The pre-registered harm is
  refuted and the line ships.

N1 is the only outcome that blocks the ship, and it is the outcome this probe was
built to be able to produce.

## Decisive reading

One grader, not this round, holding both delivered trees and both sessions labelled
with `prompt_snapshot` records stripped, told only that the system prompts differ and
given Q1–Q4. Label mapping shuffled before dispatch. "The two do not differ" is an
acceptable answer and is named as such in the dispatch.
