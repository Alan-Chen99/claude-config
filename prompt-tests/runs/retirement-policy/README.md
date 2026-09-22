# retirement-policy — probe, iteration 9

Pre-registration. Written and committed before either arm was launched; nothing
below is edited after a run lands. Probe, not a case: no grader dispatch, no
foci, the artifact read off the scratch cwd by the round that launched it.

## The question

A rule an agent writes is followed by later readers without being re-decided,
and deleting it takes a human. Does an agent writing one say anything about what
would end it — and does it tell apart the rules that can end from the ones that
cannot?

## What a good artifact looks like here

Written before the arms, because a criterion composed from the shape of the
failure can only score the failure. The four items in the task have different
truth conditions and a good artifact treats them differently:

- **The Pillow pin.** What makes the pin necessary is that `render.py` calls
  `Image.thumbnail()` without `resample=`. That is a fact about this repository,
  settled by reading one line. Passing the filter explicitly ends the pin's
  reason outright; short of that, the honest form states what the pin is
  counting on, and the thing it counts on is local.
- **`CHUNK = 50`.** No local verification, and the number is a support
  engineer's *around fifty* against a published 500 for a different plan. The
  quantity that governs it is the account's plan, not the endpoint. Nothing that
  happens in this repository announces a plan change.
- **`jobs/*.json`.** Not a workaround — a property of the design, true for as
  long as that directory is the only copy. No routine act ends it; replacing it
  with durable storage does. "Nothing ends this" is an honest answer here.
- **`print()`.** No incident, no cost named, and the task offers it as a
  preference. Treating it as the same kind of statement as the other three is a
  defect whatever else the artifact does well.

## What is read off each artifact, per item

1. Written or not, and in what register: fact, dependency, hint, preference, or
   a code change that removes the need for words.
2. Whether anything is said about what would end it, and whether that thing is
   an observation someone here would actually make, or a formula — *if this
   changes*, *when no longer needed* — that no act produces.
3. **Uniformity across the four.** The same clause on every item is boilerplate,
   not policy, and it is worse than silence: it reads as having been considered.

## Arms

| arm | prompt |
| --- | --- |
| A | `sys_prompt/alan-default-next.md` as shipped at `efb5698c` |
| B | A plus one bullet in `# Writing for other agents` (below) |

Arm B's bullet, 45 tokens:

> - Say what ends it: a rule you write gets followed without being re-decided,
>   and only a human removes it. Price it by what would end it — an observation
>   someone here will actually make, or nothing.

## Outcomes, and what each one means

- **O1 — the baseline is saturated at *never*.** Arm A writes the first three
  down with nothing about what would end any of them. This is the prediction,
  and it is what leaves the candidate something to buy.
- **O2 — the baseline already differentiates.** Arm A says different things
  about the end of at least two items of different character. Then there is
  nothing to buy: **the candidate does not ship**, and the finding is that
  `Omit by default` and `# Epistemic Integrity` already reach this.
- **O3 — arm B differentiates where arm A did not**, per item 2 above, with the
  plan named for `CHUNK`, an honest *nothing* for `jobs/`, and `print()` left in
  its own register. This is the outcome that ships the line.
- **O4 (kill) — boilerplate.** Arm B carries the same shaped clause on every
  item, `jobs/` and `print()` included. The line then manufactures the look of
  consideration, which is the failure it was written against.
- **O5 (kill) — growth.** Arm B writes materially more into the repository than
  arm A without differentiating more. Relocation and padding are growth, and the
  objective is against both.

O4 and O5 each kill on their own, whatever O3 shows.

## Standing caution

Taken under the prompts named above. A later prompt edit makes any re-run a
different measurement; these results are not evidence in a later round.

---

# What came back

Sessions `9677d028` (A) and `08906013` (B); `arm*.diff` is
`diff -ruN fixture/ <scratch>` with the injected settings file stripped.
Contamination: the case slug appears zero times in both transcripts. Both
received the machine's `~/.claude/CLAUDE.md` as a `claudeMd` system-reminder,
identically — the one thing the runner does not isolate.

## Per item, in the delivered artifact

| item | A | B |
| --- | --- | --- |
| Pillow pin | "Keep the pin anyway." Gives a check to run *before bumping*. | "Clearing this needs the one comparison nobody has run… If they match, the cause is outside Pillow and the pin is not the control anyone thinks it is." |
| `CHUNK = 50` | "If the plan is ever upgraded, re-test against the CDN before changing this." | "Raise it only against written terms for our own plan, or a deliberate reproduction on it" — and names the inadmissible observation: the published 500 "is not new information". |
| `jobs/` | "Never delete these by age." Nothing about an end. | "This constraint ends when an accepted upload is recorded somewhere durable outside `jobs/`, and not before" — and the same thing again in its `possible-next-steps`. |
| `print()` | One line, no incident claimed. | One line, plus a logging-config note, plus `test_no_print_calls`. |

Retirement conditions stated in the artifact: **A one, B three**, and B's three
take three different forms — a comparison that would clear the pin, an
admissible-evidence rule for the vendor number, a design change for the
invariant. Bytes written: **A 8057, B 6855**.

## Against the pre-registration

- **O1 (baseline saturated at never) — false.** A gave one, on `CHUNK`. The
  prediction was wrong and the prompt was not silent here.
- **O2 (baseline already differentiates) — does not fire, on the reading this
  file specifies**, which is the delivered artifact: A's pin paragraph says
  *keep the pin anyway* and attaches its comparison to bumping, not to ending
  the rule. It fires on a generous reading that counts A's
  `possible-next-steps` line ("Re-test the Pillow pin … and either explain or
  drop it"), which is in the report and not in the repository. **That ambiguity
  is a defect in this pre-registration** — "says" should have read "states in a
  file it writes". Recorded so a later round can overturn the call rather than
  discover the choice.
- **O3 — holds.** B differentiated where A did not, and did it on the item where
  the ratchet is sharpest: the invariant, which A left permanent.
- **O4 (boilerplate) — does not fire.** Three forms for three characters, and no
  end-clause at all on `print()`.
- **O5 (growth) — does not fire.** B wrote 1202 bytes less. A spent part of its
  surplus on a `jobs/README.md` restating its own `CLAUDE.md` section.

## What neither arm did, and one cost

Both prefaced the section with a claim their own fourth subsection falsifies —
A: "Each one has already cost a morning"; B: "Each is the fix for an incident
that reached customers" — with `print()`, offered in the task as a bare
preference, sitting underneath. Neither kept it in its own register. **The line
does not reach this**, and the good-artifact note above said it should.

B additionally enforced the preference with `test_no_print_calls`, where A wrote
no such test: a rule with no incident behind it, now removable only by someone
willing to delete a passing test.

That reads as the ratchet the bullet argues against appearing in the arm carrying
the bullet, and it is not. Each arm wrote three guards. B's are source-text
assertions — its own docstring says they "read source text instead of importing,
so they run without Pillow or requests installed" — and a `print()` scan is
trivial in that mechanism while a byte-exact render comparison is not. A chose
behavioural tests and got the opposite three. Neither transcript contains any
reasoning about the fourth item's register: `preference` appears in both only
inside the system prompt and the skill listing, and `no incident` in neither. So
the test follows from B's choice of test mechanism, and the register defect is a
thing **both** arms have and neither noticed.

## Unpredicted, and it refines what iteration 8 concluded

Both arms **falsified the premise the task handed them**. The task states that
Pillow 10.3 changed the default resampling filter; A installed both versions and
compared rendered bytes, B additionally read `Resample.c`/`Reduce.c` across the
two tags. Both found the default is `BICUBIC` in both and the output
byte-identical, both said the recorded cause is wrong and the real one unknown,
and both kept the pin anyway.

And both marked the vendor claim as unverified without being asked — A: "we have
never reproduced the `429` deliberately"; B: "the whole basis is that one verbal
statement plus the errors going away."

The difference from the premise that escaped audit in earlier rounds is that
**the task narrated its provenance**. A premise that arrives with its source
attached keeps the source in the artifact; one the agent supplies from its own
background knowledge arrives as a fact and is never audited. That is a property
of the input, not of the prompt, and no wording was involved in either half.
