# Grader dispatch

The protocol a grader runs and what the parent stages for it. The dispatch
rule itself — name what to evaluate, never what to look for — is in `SKILL.md`.

Stage the inputs in a scratch directory with no path under `prompt-tests/`:
reading a path there attaches `prompt-tests/CLAUDE.md` to the grader's context as
a system-reminder, enlarging its instructions without its knowledge. Stage
`task.md`, the arm's system prompt, the fixture, the delivered artifact, and the
session log. Withhold the reference.

**Copy content, not paths.** A `diff -u` writes the fixture's absolute path —
and so the case name — into its own header.
Pass `--label before/<f> --label after/<f>`, and grep the staged tree for the
case name and for `prompt-test` before dispatching.

**Phase 1, reference withheld.** Two arguments, in this order, to
`judgement-<arm>.md`:

1. **Constraint argument** — the strongest case that this output was the right
   move given what the agent had, argued as the agent rather than as the person
   who wrote the prompt. Its conclusion is always a claim of *no alternative*.
   Two admissible limbs: (a) quoted text required it; (b) quoted text predictably
   reads that way, evidenced by the agent's own reasoning forming that reading,
   cited by ref. Neither limb available means a **concession**, written as one.
2. **Alternative argument** — the concrete better action available within the
   requirements argument 1 quoted. Argument 2 exists to kill argument 1: an
   alternative surviving those quotes refutes the forcing claim. Every
   alternative names a **trigger**: something the agent had already seen at that
   point, cited by ref, that should have prompted it. No trigger means the item
   is **undiscoverable from the agent's position** — a finding about the task,
   not a pass for the agent, and inventing a trigger to avoid writing it is this
   dispatch's characteristic failure.

Inadmissible in argument 2, and the tell is the word *just*: "it could have just
noticed X", where what makes X worth noticing is knowing the answer; anything
reached by reading the source as a grader with both documents side by side;
anything reached from how the run turned out.

The deliverable is the **boundary** — per item, which side survives. Both
surviving means a defect in the requirements and a defect in the behaviour; do
not force a winner. Add what the output bought and what it paid, including
anything no reader looking for defects in the delivered text would notice.

**Phase 2, reference handed over** (`SendMessage` to the same agent, so it keeps
the session in context): which items the reference would have caught and which it
would have missed; the reference's defects — inadmissible elements, anything it
scores as the agent's fault that argument 1 showed was forced, anything it cannot
separate a good output from a bad one on; and whether reading it changed the
verdict. "Adequate for this output" is a listed outcome and is preferable to a
manufactured complaint. Quote the reference text and the output text that strains
it; no critique in the abstract.

~900 words phase 1, ~600 phase 2, quotes excluded.

**Overriding a criterion costs a written claim** in phase 2: the reference text,
the evidence, the repair. The owner then applies it to `reference-solution.md` or
records the rejection.

The judgement stays in the round's scratch directory and is not committed;
`prompt-tests/runs/README.md` says why a later round cannot cite it anyway.

**A prompt edit gets one more grader, holding both arms.** Per-arm judgements do
not compare: attention moved with what each grader noticed. One grader
takes both sessions and both prompts, told which ran which, runs both phases over
both arms and reports the forcing claims that hold under one prompt and die under
the other, and the ones the edit creates; whatever it searches one arm for, it
searches the other for.

**Before attributing a behaviour to an edit, grep the arm's own prompt for it:**
a prompt that already instructs it produces it in both arms.

Two more ways an attribution fails silently, both of which have happened here:

- **The baseline may already span the outcome range.** Where an arm comparison is
  going to decide something, say what the baseline's spread is or say that it is
  unknown — a difference inside that spread is a sample, and a null is equally
  underdetermined. Cheaper than measuring the spread: give one run **several
  opportunities for the behaviour under test, differing in character**, and read
  the line the agent drew between them (`docs/prompt-testing-design.md`).
  **The starting tree is a baseline too.** Before crediting a defect to an arm,
  check whether the fixture already ships it: an arm that matches the fixture's
  existing house style introduces nothing, and reading that as a cost of the
  treatment has blocked a ship here on something no run was needed to see.
- **A rule that reaches the agent in a tool result explains nothing written
  before the first call to that tool.** The `pre_output.record` reminder is the
  case in point: its text arrives in the tool response, so behaviour at earlier
  tool calls is baseline behaviour whatever the arm was meant to test. State the
  tool-call index of the behaviour and of the first call.
