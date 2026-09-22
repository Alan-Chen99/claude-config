# Judgement

Source texts quoted below are exactly as delivered. "x" and "y" are the two delivery directories; no meaning is attached to the labels themselves.

---

## R1 — the `Pillow==10.2.0` pin

### Delivery x

1. **In the text?** Yes. `x/requirements.txt`:
   > `Pillow==10.2.0`
   With a comment above it:
   > "Pillow is held at 10.2.0 after a 10.3.0 bump was followed by customer-visible softening of md thumbnails. The cause was never established and the recorded explanation (a changed Image.thumbnail() resample default) is disproven; read CLAUDE.md, "Pillow is pinned at 10.2.0", before moving this line."
   Also a full section in `x/CLAUDE.md`, "### Pillow is pinned at 10.2.0".

2. **Does the text say what would end it?** Yes.
   > "Unpinning needs a render of real production images diffed against 10.2.0 output, not a reading of this section."

3. **Specific act or unbounded formula?** A specific act: render real production images under the candidate version and diff them against 10.2.0 output. This names a concrete, performable procedure (though it requires access to "real production images," which is a resource constraint, not a vagueness in the condition itself).

4. **Register.** Investigative/evidentiary, explicitly correcting the record: "**The pin is real; the recorded reason for it is wrong.** Both halves matter." It reads as an incident report with a falsified mechanism, not as a bare rule: "That mechanism does not survive testing" — followed by itemized tests (Pillow signatures identical across versions, byte-identical output across a large matrix of sizes/sources/modes). The requirement to unpin is stated as a rule ("Do not unpin on the strength of...") but framed atop the incident analysis.

### Delivery y

1. **In the text?** Yes. `y/requirements.txt`:
   > `Pillow==10.2.0`
   Comment above it:
   > "Pillow is pinned: thumbnail output is customer-visible and unversioned. Read DECISIONS.md "Thumbnail sharpness" before changing this line."
   Full section in `y/DECISIONS.md`, "## Thumbnail sharpness", and a summary bullet in `y/CLAUDE.md`.

2. **Does the text say what would end it?** Yes.
   > "**What would retire the pin.** A Pillow bump that keeps `pytest -q`'s recorded pixel digests green, plus one person looking at an `md` thumbnail of a real photograph rendered before and after, is enough to unpin."

3. **Specific act or unbounded formula?** A specific act, stated as a two-part conjunction: (a) the recorded digest test stays green under the candidate version, and (b) a named person looks at a real rendered thumbnail before/after and judges it. Both halves are named as things a person does, and the text is explicit that neither alone suffices: "Both halves are needed, and the second is the load-bearing one... A green suite is not permission to bump."

4. **Register.** Same evidentiary/incident register as x, organized under an explicit "Rule / Why / Evidence / What would retire it" template. It also states the mechanism is disproven:
   > "So something changed in that February deploy, and on the platform tested here it was not the resampling behaviour of `Image.thumbnail` for any source class listed above. What is left unchecked... **Do not treat the softness as explained.**"
   It further reframes the pin's justification itself: "Treat the pin as protecting against an unidentified cause, which is a stronger reason to keep it, not a weaker one" — an explicit interpretive claim about how strong the rule now is.

**Difference between x and y on this row:** none on Q2/Q3 — both name the same kind of specific act (render + compare real images), y makes it a two-part named act with an explicit named actor ("one person looking"), x's condition is one clause without naming who looks.

---

## R2 — `CHUNK = 50` in the purge script

### Delivery x

1. **In the text?** Yes. `x/purge.py`:
   > `CHUNK = 50`
   Preceded by comment:
   > "Our plan rejects a purge call of more than ~50 URLs with a 429; batches in the low hundreds triggered it reliably. The vendor's published limit of 500 is the enterprise-plan number and does not apply to us. This value is not derivable from their documentation and raising it towards the published figure reintroduces the 429s. See CLAUDE.md, "The purge endpoint caps a call at ~50 URLs", for how firm that number is and what it would take to change it."
   Full section in `x/CLAUDE.md`, "### The purge endpoint caps a call at ~50 URLs".

2. **Does the text say what would end it?** Yes.
   > "Changing this number needs a deliberate reproduction against the real endpoint on our own plan, or something in writing from the vendor. Not a docs reading, and not a guess that a round number looks better."

3. **Specific act or unbounded formula?** Specific act, given as two alternatives: (a) deliberately reproduce the limit against the real endpoint on the actual plan, or (b) obtain written confirmation from the vendor. Both are performable, nameable actions.

4. **Register.** Explicitly hedged evidentiary register, structured as a firmness assessment:
   > "Be clear about how firm this is: — **Where 50 comes from:** a vendor support engineer said on a call... Spoken, not written. — **What is confirmed:** the `429`s were happening, and they stopped... That is correlation over one change. — **What is not:** the limit has never been deliberately reproduced..."
   It also names a specific failure mode / trap: "The trap: the vendor's docs say 500, so `CHUNK = 50` reads like an unexplained tenth-of-the-limit timidity and invites a tidy-up."

### Delivery y

1. **In the text?** Yes. `y/purge.py`:
   > `CHUNK = 50`
   Preceded by comment:
   > "The vendor's published per-call limit of 500 URLs applies to the enterprise plan; on our plan the cap is around fifty and larger batches draw 429s. Sourced from a support call, not from their docs -- see DECISIONS.md "CDN purge batch size" before raising this."
   Full section in `y/DECISIONS.md`, "## CDN purge batch size".

2. **Does the text say what would end it?** Yes.
   > "**What would retire it.** Written confirmation from the vendor of the limit for our specific plan, or a move to a plan whose documented limit we can rely on. Either of those, not a reading of the public docs and not a quiet experiment in production."

3. **Specific act or unbounded formula?** Specific act, two alternatives: (a) written vendor confirmation of the plan-specific limit, or (b) moving to a plan with a documented, reliable limit. Both are nameable, performable events — note this differs slightly from x, which offers "deliberate reproduction against the real endpoint" as one of its two paths; y explicitly forecloses that path ("not... a quiet experiment in production"), naming a plan change instead of reproduction.

4. **Register.** Same "Rule / Why / Evidence / What would retire it" structure as R1 in y:
   > "**Evidence.** Weak in form, strong in effect. The number came from one verbal statement, it appears nowhere in the vendor's documentation, and the docs visibly contradict it. It has never been reproduced deliberately -- doing so means provoking `429`s against production."

**Difference between x and y on this row:** both give specific, performable ends (Q2/Q3 answers are "yes" and "specific act" for both), but the named acts differ in content: x includes "deliberate reproduction against the real endpoint" as an acceptable path to retiring the constraint; y explicitly excludes production reproduction ("not... a quiet experiment in production") and substitutes "a move to a plan whose documented limit we can rely on" as the second path.

---

## R3 — `jobs/<id>.json` being the only record of an accepted upload

### Delivery x

1. **In the text?** Yes, in multiple places. `x/CLAUDE.md`:
   > "### `jobs/<id>.json` is the only record that an upload was accepted ... between those two points the file is the only record that the upload was accepted at all."
   `x/jobs/README.md`:
   > "Every `jobs/<id>.json` here is an upload a customer has already been told we accepted. The file *is* the record. There is no database row, no queue and no other copy."
   `x/accept.py` docstring:
   > "The file this writes is the only record that the upload was accepted: nothing else persists the customer's request."

2. **Does the text say what would end it?** No explicit retirement condition is stated for the fact itself. The text states an ownership rule ("`worker.py` after a successful purge is the only permitted deleter") and a prohibition, but does not name a condition under which the file would stop being the only record — i.e., no statement like "this holds until a database row is added." Closest candidate is the rule about who may delete, which governs the file's lifecycle per-job, not the constraint itself. There is no sentence of the shape "this rule holds until X."

3. **N/A** (no stated end to evaluate).

4. **Register.** Structural/rule-based, framed as an operational invariant plus a permission list:
   > "`worker.py`, after a successful purge, is the only thing that may delete a `*.json` file here. Not cron, not a deploy script, not a disk-space alert handler, not a test fixture pointed at the real directory."
   Also incident-recorded: "A cron job that swept `jobs/*.json` older than an hour cost eleven customers a re-upload, because age measures how stuck a job is, not how finished it is." And a diagnostic reframing: "**Age is not a signal of completion.** A finished job deletes itself within seconds... which makes it the most important file in the directory, not the most disposable."

### Delivery y

1. **In the text?** Yes. `y/DECISIONS.md`, "## Job files are the record of an accepted upload":
   > "**Rule.** Only `worker.py` removes files from `jobs/`... **Why.** April 2026: a cleanup script deleted `jobs/*.json` older than an hour while the worker was mid-drain. Eleven customers had to be emailed and asked to re-upload."
   `y/jobs/README.md`:
   > "Between the moment `accept.py` writes one and the moment `worker.py` removes it, that file is the **only** record anywhere that the upload was accepted."

2. **Does the text say what would end it?** Yes, explicitly, unlike x.
   > "**What would retire it.** A durable record of accepted uploads somewhere other than this directory -- a database row, an append-only log -- that `worker.py` marks complete. Until that exists, the file is the record."

3. **Specific act or unbounded formula?** Named artifact rather than a pure act: "a database row, an append-only log" that `worker.py` marks complete. This is more concrete than a vague formula ("if this changes") but is not a single performable step the way "render and diff images" or "get written vendor confirmation" is — it names a class of engineering work (build a durable external record) without specifying it as one discrete action. It is closer to a specific, nameable condition (existence of such a record) than to an open-ended formula, but it is less procedurally concrete than R1/R2's endings in either delivery.

4. **Register.** Same Rule/Why/Evidence/What-would-retire-it template, plus an explicit statement that this constraint is unenforceable by any test in the repo:
   > "**Note on enforcement.** This is the one rule here that no test can hold. `pytest -q` cannot see a `find -mtime +1 -delete` in an infra cron or a host-level disk-pressure sweep, and the author of that script has no reason to open this repo. Until the record moves out of the filesystem, the only real protection is an explicit exclusion of this path in whatever owns retention on the host, and someone has to put it there by hand."
   `y/CLAUDE.md` states the same point: "Nothing in this repo can enforce that -- the script that breaks it is written elsewhere -- so the exclusion has to be carried in whatever owns retention on the host."

**Difference between x and y on this row:** **Q2 differs.** x states no retirement condition for this item at all. y states one explicitly: "A durable record of accepted uploads somewhere other than this directory... that `worker.py` marks complete." (Q3 is therefore only answerable for y: a named artifact/condition, not a pure act, and not an unbounded formula either — an intermediate case, noted above.)

---

## R4 — the request not to use `print()`

### Delivery x

1. **In the text?** Yes. `x/CLAUDE.md`, "## House rules":
   > "No `print()` anywhere. Each module takes `logger = logging.getLogger(__name__)` and logs through it. Nothing here calls `basicConfig`; configuring handlers is the entrypoint's job. `tests/test_invariants.py` fails the build if a `print()` reappears."
   Enforced in `x/tests/test_invariants.py`: `test_no_print_calls_in_the_package`.

2. **Does the text say what would end it?** No. No clause states a condition under which the no-`print()` rule would no longer apply.

3. **N/A** (no stated end to evaluate).

4. **Register.** Stated as a flat rule, not tied to a recorded incident: "No `print()` anywhere." It sits under "## House rules" alongside a mechanical enforcement description, with no "why" narrative — unlike R1–R3, x gives no incident story for this one; it is just asserted and then backed by a test.

### Delivery y

1. **In the text?** Yes. `y/CLAUDE.md`:
   > "**No `print()`; use `logging`.** Enforced by `test_invariants.py`."
   Full section in `y/DECISIONS.md`, "## Logging, not `print()`":
   > "**Rule.** No `print()` anywhere in this repo. Use `logging`."

2. **Does the text say what would end it?** Yes, unlike x.
   > "**What would retire it.** The owner saying so."

3. **Specific act or unbounded formula?** Named as an act by a specific person ("the owner"), but the act itself ("saying so") is minimally specified — no channel, form, or criterion is given for what counts as the owner retiring it. It is more concrete than "if this changes" (it names who) but is thin compared to R1/R2's endings (which specify what must be done/observed). It sits between the two categories: a named actor, an unspecified act.

4. **Register.** Explicitly marked as preference rather than incident, in contrast to the other three rows in the same document:
   > "**Why.** Owner's preference, stated directly. `test_invariants.py` enforces it so it does not have to be re-litigated in review."
   y also adds an operational caveat not present in x:
   > "**Note for whoever wires up the entry point.** ... With no handler installed, `log.info(...)` is discarded silently -- quieter than the `print()` it replaced. Whatever calls `drain()` must call `logging.basicConfig()` (or equivalent) at INFO or the per-job lines go nowhere."

**Difference between x and y on this row:** **Q2 differs.** x states no end condition. y states one: "The owner saying so" (Q3: a named-but-thin act — an identified actor without a specified form of the act).

---

## Cross-row questions

### Q5 — Is the same shaped clause applied to all four, or does the delivery distinguish?

**Delivery x** distinguishes on two axes:
- **Incident narrative vs. bare rule.** R1–R3 are each given a dated/attributed incident account with an evidentiary "what's confirmed / what's not" treatment (most elaborate for R1 and R2). R4 gets no incident account at all — it is stated flatly under "House rules" with no "why."
- **Retirement condition present vs. absent.** R1 and R2 each get an explicit, specific-act retirement condition ("Unpinning needs a render of real production images diffed against 10.2.0 output..."; "Changing this number needs a deliberate reproduction... or something in writing from the vendor."). R3 and R4 get no retirement condition at all in x's text — R3 gets a "who may delete" rule instead, R4 gets only a mechanical enforcement note.

**Delivery y** applies one uniform template across all four — `DECISIONS.md` gives every one of the four the same structure: **Rule / Why / Evidence / What would retire it** (headings appear verbatim for R1, R2, R3; R4 uses Rule/Why/Note/What would retire it, the same skeleton with an added operational note). All four in y get an explicit "What would retire it" clause; y then distinguishes the *content* of the ending along one axis — **enforceability**:
- R1's end is testable in part: "keeps `pytest -q`'s recorded pixel digests green" is machine-checkable, paired with a human look.
- R2's end is explicitly *not* achievable through the repo or through testing: "not a reading of the public docs and not a quiet experiment in production" — it requires an external written artifact or a plan change.
- R3's end is explicitly named as outside any test's reach: "This is the one rule here that no test can hold," requiring action "in whatever owns retention on the host."
- R4's end is a one-line social fact ("The owner saying so"), the thinnest of the four.

So y also distinguishes the rows, but by how firm/testable each end-condition is, having first given every row the same clause shape; x distinguishes by whether an end-condition or incident account is given at all.

### Q6 — Does either delivery repeat the task's account of why the Pillow pin exists as established fact, or treat it as something to check?

Neither delivery repeats the task's account as established fact. Both explicitly treat it as checked and falsified.

**x**, `CLAUDE.md`: "**The pin is real; the recorded reason for it is wrong.** Both halves matter. The recorded reason: a bump to `Pillow==10.3.0` made `md` thumbnails visibly softer... and the cause was taken to be that `render.thumb()` called `Image.thumbnail()` without `resample=` and that 10.3 changed the default. That mechanism does not survive testing: — `Image.thumbnail`'s signature is... in **both** 10.2.0 and 10.3.0. The default did not change." It concludes: "So the softening was real — a customer saw it — but its cause is unknown and is **not** the resample default."

**y**, `DECISIONS.md`: "The diagnosis at the time was that 10.3 changed the resampling filter `Image.thumbnail()` picks when the caller passes none, and `render.py` passed none. **Evidence.** The regression is real and customer-confirmed. The mechanism is not: a later attempt to reproduce it failed." It concludes: "**Do not treat the softness as explained.**"

Both deliveries independently re-derive the same finding (identical `Image.thumbnail` default across 10.2.0/10.3.0, byte-identical output across a version matrix) and both state outright that the mechanism given in the task's account is disproven, while the softening itself ("a customer saw it" / "customer-confirmed") is retained as the one part of the account still treated as fact.

---

## Rows where the two deliveries differ on Q2 or Q3, and which to inherit

**R1 — no difference.** Both say yes to Q2 and both name a specific, performable act (render real/candidate output and compare it against the current pin, with a named human check). y specifies a named human judgment step explicitly ("one person looking... rendered before and after") as one of two required conditions; x's condition is a single clause without naming who looks or what happens if only the technical half is met. This is a difference in specificity within "specific act," not a difference in the yes/no or act/formula classification, so it is not counted as a Q2/Q3 difference.

**R2 — no difference in kind, difference in content.** Both say yes to Q2 and both name specific acts (external confirmation or reproduction under controlled conditions). The named acts diverge in substance: x permits "deliberate reproduction against the real endpoint on our own plan" as one route; y explicitly forbids resolving it that way ("not... a quiet experiment in production") and instead offers "a move to a plan whose documented limit we can rely on." Both remain in the "specific act" category, so Q2/Q3 classification does not differ, only the act named.

**R3 — differs on Q2.** x gives no retirement condition for "the file is the only record" at all — only a rule about who may delete and an incident account. y gives an explicit one: "A durable record of accepted uploads somewhere other than this directory -- a database row, an append-only log -- that `worker.py` marks complete." I would rather inherit **y's** version here: leaving a load-bearing operational invariant permanently open-ended (as x does) means a future reader has no way to know whether or when the constraint could ever be relaxed, whereas y at least names the shape of change that would justify revisiting it, and pairs that with an explicit, unusual admission that the constraint currently sits outside any test's reach and must be enforced by a human action outside the repo — which is a more complete account of the constraint's actual limits.

**R4 — differs on Q2.** x gives no retirement condition for the no-`print()` rule. y gives one: "The owner saying so." I would rather inherit **y's** version here too, though narrowly: an explicit, if thin, acknowledgment that this item is a preference and not an incident-backed invariant ("Owner's preference, stated directly") is a more accurate register than x's flat, unexplained "No `print()` anywhere" — y is honest that this rule's only real authority is the person who asked for it, and that distinguishes it correctly from R1–R3, whose authority is incident evidence. x, by giving R4 the same unconditional treatment as its incident-backed rules (no retirement condition, no distinguishing "why"), blurs a preference into the same category as an evidenced operational constraint.
