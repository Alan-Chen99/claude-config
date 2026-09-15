# Measuring a prompt change

Read this when an edit is going to be measured — running cases, reading
transcripts, deciding what a result means. The principles in `SKILL.md` apply to
the edit itself; these apply to the loop around it.

**Observability.** Grade what the transcript shows, not what the final message
claims about itself; if the harness records reasoning as well as output, read
both. In Claude Code the transcripts are JSONL logs carrying thinking and text
blocks, and `/cc-history` queries them.

**Implicit-guidance justification.** When an edit adds enforcement guidance
longer than the invariant it enforces, the guidance must be justified by a prior
experiment showing the agent cannot derive it alone. Experiment shape: take the
prior prompt, add ONLY the invariant text as a labeled section plus a gate
asking whether the invariant holds for the output draft. Run on the failing case
and read the transcript. Targeted enforcement is justified only for what the
agent did NOT surface on its own; pre-specifying categories the agent would have
derived is wasted length and an overfitting vector.

**Recognition before enforcement.** A permanent enforcement edit is designed
against what the agent can perceive about the failure, not against the failure as
the editor sees it. Before locking in the fix, run a throwaway diagnostic version
— typically a one-sentence directive at the enforcement point ("after producing
your draft, identify whether [invariant] holds; if not, name what is missing") —
and read the transcripts. Three outcomes drive different fixes: (1) recognition
succeeds and behavior changes — the diagnostic itself, possibly shortened, is the
fix; (2) recognition succeeds but behavior does not — pair recognition with an
action trigger (re-enter the gate, do not send); (3) recognition fails — the
agent cannot perceive the failure; do not add enforcement, instead reframe the
invariant in vocabulary the agent uses, or add an external verifier. Enforcement
on top of unrecognized failure produces compliance theater. Pairs with
implicit-guidance justification: that rule answers "do not add what the agent
already derives"; this one answers "do not add what the agent cannot perceive".

**Pass percentage is not the target.** Outcomes cluster: a structurally-fixed
invariant tends to pass most fair trials, a structurally-broken one to fail most.
That prior justifies fewer trials per conclusion, and it also makes raw pass
percentage a weak target. Look for the decision point that produced the outcome,
and distinguish (a) arbitrary decision points where either path should still
produce valid output from (b) direct failure points where a specific action or
omission made the output invalid. (a) drifts with unrelated prompt changes, model
variance and real-task distribution; if every test run takes one arbitrary path
while a plausible real run takes another, add a case that exercises the other
path rather than treating the percentage as stable. Example: every run invoking a
gate exactly once is not itself a failure, but if a plausible failure mode appears
only after a second gate iteration, add a case that produces multiple iterations
before claiming coverage.

**Conclusions must predict and be falsifiable.** "Agent behaved this way under
this prompt" is one observation about one prompt. A useful conclusion names a
line of reasoning the agent currently uses, identifies the prompt clause that
produces or permits it, and predicts what changes when you alter the clause.
Form: "Currently agents may treat this line of reasoning as valid: [reasoning].
Removing or rewording [clause] suppresses this; therefore consider [edit] to tune
[axis]. Predicts [behavior change]; falsified by [counter-evidence]." A finding
that predicts nothing outside the case it was observed in is data, not a
conclusion.

**One falsifiable question per iteration, not one experiment.** This rule sets
the unit of an iteration; the next sets which experiments belong in it.
Single-experiment
iterations stop at "X did or did not happen on this run". A useful iteration runs
a series of small experiments that settle one falsifiable question about agent
behavior. Plan the question first, design experiments that distinguish the
candidate answers, and stop when the question is answered rather than at the
first run.

**Don't run the final case until you can predict the outcome.** Most iterations
should not run the headline case with the headline rubric. Borrow its task text
for sub-experiments at smaller scope. Run the headline case when you can
confidently predict whether it passes and why. After a failed attempt, reflect on
what understanding was missing rather than retrying an adjacent variant —
adjacency without a diagnosis samples a different point on the same uncharted
surface.

**Compare success and failure traces.** When a behavior the agent reliably
produces in isolation disappears inside a larger task, read the two reasoning
traces side by side rather than assuming a capability gap. The drift is usually a
recognition trigger or an attention budget, and it shows in the reasoning rather
than in the output.
