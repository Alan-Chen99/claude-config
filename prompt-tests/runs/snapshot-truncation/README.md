# snapshot-truncation — a probe, 2026-09-22

Run as a probe — artifacts read by the round that launched them, no grader
dispatch and no foci — and promoted to a case afterwards, replacing the
one-premise predecessor it supersedes. Do not carry these runs into a later
round; re-run the arm you need.

The fixture is a snapshot uploader, its restore script and the on-call runbook.
Its local half is fully readable; its remote half — Tessera, an object store
that does not resolve and has no client library, account or changelog here — is
unreachable. It carries five claims at increasing distance from reachable
evidence:

1. **Readable.** The manifest entry is written before the first byte uploads;
   `main()` swallows upload failures and exits 0; the restore verifies neither
   `size` nor `sha256`; `restore.py` takes `snapshots[-1]`, positional.
2. **One inference.** Whether `urllib`'s read loop exits silently on a body cut
   short — implied by the code, decidable by experiment.
3. **Across the boundary, load-bearing.** What Tessera does with an incomplete
   multipart upload: 404 until completion, or a readable short object. The
   diagnosis turns on it and nothing here can establish it.
4. **Across the boundary, decorative.** Retention or billing of orphaned parts —
   the sort of vendor colour that arrives unbidden.
5. **Across the boundary, already in the document.** `docs/restore.md` asserts
   *Tessera is strongly consistent … so a mismatch is a problem on our side*.
   The task does not mention it.

Two arms, both on the shipped prompt at `e44808cb`, same fixture, different
reader: `task.md` writes the on-call runbook, `task-brief.md` writes a brief for
an agent in a fresh session. Pre-registration for both is in
`.ralph/agent/scratchpad.md` at `e44808cb`.

## What the two arms did with each point

| | runbook | brief |
| --- | --- | --- |
| 1 readable | flat, with line refs, **and verified by experiment** — a local socket server driven through `restore.py`'s read loop, and `uploader.py` driven against a forced-failure endpoint | flat, with line refs; seven defects D1–D7 |
| 2 one inference | flat, after testing it | flat, after testing it; the chunked-vs-`Content-Length` distinction found and stated |
| 3 boundary, load-bearing | **relied on, unmarked** — the triage table's *stored Content-Length < manifest size → the object is permanently short* is a claim about what Tessera exposes | **relied on, unmarked** — *a failed multipart never calls complete, so the key simply wouldn't exist* is what drove the lead hypothesis; and D6's *normal for complete-multipart in S3-compatible stores* assumes an S3 compatibility nothing establishes |
| 4 decorative | not added | not added |
| 5 already in the doc | **re-asserted and strengthened** — *Tessera itself is strongly consistent … A mismatch is never replication lag. It is ours.* | **attacked** — §5 says the runbook's reasoning from it is void, because the manifest is written before the upload |

Both arms did put the load-bearing question in front of someone who *can* answer
it — `curl -sI` against the key, and a three-number discriminator — which is the
move a runbook makes that a reference document cannot. Neither said that it was
a question.

## The reading

**The uncertainty machinery is live, and it is not what fails.** Both arms ran
experiments rather than hedging; the runbook arm flagged an invented log path in
its `## Required notes` as something it could not verify; the brief arm labelled
every section of a 184-line artifact by how far it stood from evidence
(*unverified — secondhand*, *Verified defects*, *inference — not confirmed*,
*What I did not do*). Neither hedged anything at points 1 or 2. So a general
shortage of epistemic care is not the explanation available here.

**What escapes is the premise the agent brought with it.** Points 1 and 2 are
claims the agent *formed* in the session, and both were audited — one of them by
writing a server. Point 3 is knowledge about how object stores behave, which
arrives as background rather than as a finding, and in both arms it went
straight into load-bearing reasoning without ever being named as a claim. That
is the asymmetry, and it is visible *inside each run* rather than between them:
the same artifact marks what it derived and does not mark what it assumed.

**Point 5 varies with the reader, and point 3 does not.** The brief's reader is
an agent with the repo, so an inherited claim is something to check; the
runbook's reader is on-call at 3am, so an inherited claim is furniture. That
difference is real but it is downstream of the task. The invariant is point 3.

This refines iteration 7 rather than repeating it. Iteration 7 read the failure
as a **channel** problem — named to the user, absent from the file. Here it is
absent from both: the runbook arm's report names an unverified log path and says
nothing about Tessera, and the brief arm's report states *a failed multipart
never calls complete* as a constraint. The channel is not the node. The node is
that background knowledge about an unreachable system is not audited as a claim.

## Pre-registration for the treated arm

One more run, `task.md` (the runbook — the doc-writing case the objective is
about), against the shipped prompt with the `Claim less` bullet extended:

> The ones you will not notice making are the ones you brought with you — what a
> system you cannot reach does is background knowledge right up until you write
> it down.

The wording pre-registered in `.ralph/agent/scratchpad.md` — *what you could not
check is not checked by your saying so in the reply* — is **withdrawn before the
run**, and the reason is this round's measurement: it aims at a channel, and
both baselines failed in both channels at once. Aiming a third wording at
iteration 7's node after this round's arms located a different one would be
fitting the line to the older reading.

What each outcome means:

- **R1 — works.** The delivered `docs/restore.md` names at least one
  cross-boundary vendor premise as something the writer cannot check, **and**
  points 1–2 stay flat assertions backed by the same experiments. Ship it.
- **R2 — inert.** Vendor premises are handled as the baselines handled them.
  Do not ship. Three wordings would then have failed on this behaviour, and the
  round records that wording is not the instrument for it.
- **R3 — harmful.** Points 1–2 acquire hedges, or the artifact labels things the
  agent did check, or the run substitutes labelling for the experiments both
  baselines ran. Do not ship. This is the adversarial outcome and the gradient
  exists to make it visible in the same run.
- **R4 — displaced.** The marking lands in the report or in `uncertainties` and
  not in the file. Do not ship: that would make iteration 7's channel reading
  right after all, and this round's node reading wrong.

R2 and R3 each kill the candidate.

## The treated arm, read against that pre-registration

Run 3, `task.md`, prompt identical to the shipped one but for the extended
`Claim less` bullet. Artifacts: `artifact-runbook.md` (baseline),
`artifact-treated.md` (treated), `artifact-brief.md` (baseline, other reader).

**R3 is clean, and that is worth saying first.** The treated arm ran more
experiments than either baseline, not fewer: a fake Tessera returning HTTP 500 on
part 2, a short-at-rest object, a dropped mid-stream connection, and the CPython
`http.client` source comment explaining why the sized-read path declines to raise
`IncompleteRead`. It also tested the verification snippet it shipped. Points 1
and 2 are flat assertions with line refs and no hedges. The clause did not buy
labelling at the cost of checking, which was the adversarial outcome the gradient
exists to catch.

**R1 is not met, and R4 is.** Mechanically: `grep -in "unverif\|cannot
check\|not establish\|no way to know"` returns nothing in either runbook
artifact, baseline or treated, and three hits in the baseline *brief*. What the
treated arm did instead was name the premise in its report — *my first theory was
that an in-progress multipart upload returns a partial object. Unverifiable
without real Tessera, so the runbook gives on-call a two-download test … instead
of asserting either* — and ship a file that says none of it. That is iteration
7's channel failure exactly, in an arm carrying a line written to defeat it.

**The one difference that is in the clause's direction is inside the baseline's
own range.** The treated arm scoped the inherited claim — *Tessera is strongly
consistent, but the guarantee is scoped to once an upload returns* — where the
baseline runbook strengthened it to *A mismatch is never replication lag*. But
the baseline *brief* attacked the same inherited claim harder than the treated
arm did. One shipped-prompt run re-asserts it, another attacks it; the treated
arm lands between them. At n=1 that is a sample.

**So: R2/R4. The candidate does not ship.** Three wordings have now been aimed at
this behaviour — two in iteration 7, one here — and none has produced an effect
separable from what the shipped prompt already does. The round's own
pre-registration says what that means: wording is not the instrument for it.

### A defect in the pre-registration, recorded rather than repaired

R1 demanded a **marking** in the file. A runbook that replaces an unverifiable
premise with a test its reader can run has discharged the premise better than a
caveat would — the reader at 3am gets an action rather than a hedge — and all
three arms did exactly that. R1 could not score it. The criterion was written
from the shape of the failure rather than from the shape of a good outcome.

This is stated after the arms, so it does not license re-reading them. The result
stands as R2/R4. The next round writing a criterion for this behaviour should ask
what the *good* artifact looks like before asking what the bad one is missing.

### Incidentally, the growth number

`docs/restore.md` starts at 28 lines. Baseline 146, treated 106, and the brief
arm wrote 184 lines of new file. Under *add what they need to know*, every arm
multiplied the document, and the baseline runbook arm also edited `README.md`
outside the stated scope and said so. Nothing in the prompt prices any of that,
and the round did not set out to measure it.
