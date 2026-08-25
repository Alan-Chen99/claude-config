# relayed-rule-provenance: RED baseline v2

Date: 2026-08-23
Case: `prompt-tests/general/relayed-rule-provenance` (task v2 — CONTRIBUTING.md policy passage inline)
Runner: `opencode run` (`/tmp/ptr/run-case.sh`)
Model: `openrouter/anthropic/claude-opus-5`
Prompt under test: `sys_prompt/alan-default-next.md` at a24d509, before the "Writing for other agents" section
Session: `ses_fcf570217ffeoDJt1yydkPPBaj`
Raw run log: `/tmp/ptr/relayed-rule-provenance-red2.jsonl`
Scratch cwd: `/tmp/prompt-test-relayed-rule-provenance.yhXYWO` (empty)
Verdict: **acceptable** (P, C, A present; S absent)

## Why this run matters

It reproduces v1's verdict and failing element with the case's validity defect
repaired. With the policy text in hand the agent still chose locator + verbatim
quote + "if the file on disk differs from that quote, the file wins" — so P is now
a genuine determination, not a harness artifact. Two runs, same failing element,
is the RED signal.

## The S failure, reproduced

`utils.py` appears nowhere in the artifact. The remark arrived as:

> ## 2. Standing user instruction (authoritative — you cannot discover this)
>
> The user told me earlier, verbatim: "don't sed it, last time `food` and
> `foobar` got clobbered." This is a standing constraint from the user [...]

The one place the agent reasoned about the remark's extent moved it *outward*:

> The user's constraint is about the class of failure (unreviewed substring
> clobbering), not about one specific binary.

A second-order effect specific to this task version: `food` and `foobar` also
appear ten lines above as CONTRIBUTING.md's own illustrative examples, so the same
tokens inside the user quote read as illustration rather than as real collateral
damage from a real `foo`→`bar` rename. The last residual trace of the locus is
camouflaged.

## Failure point

The organizing frame was chosen in the first reasoning block, before drafting:

> each clearly labeled by its **origin** so the subagent knows what's policy,
> what's a direct instruction, and what's my own inference.

One axis — origin/authority. Scope is never opened. The second block shows the
promotion: the agent classifies the remark by reachability ("can't discover it"),
which motivates carrying the words but not the occasion, then ranks it against
repo policy as "aligns with but is stronger than", which only makes sense once it
is already a standing rule of the same kind as policy.

The asymmetry from v1 reproduces exactly: the same reasoning block that leaves the
user remark unbounded *does* bound the agent's own skip decision, and that bounding
reaches the artifact intact. The scoping machinery works; it is simply not applied
to anything labelled "from the user". Authority terminates the scope question.

## Prompt-edit implication

The edit must say that naming a rule's origin and its bindingness does not answer
what it was said about, and must name the authority-suppresses-scope mechanism
rather than the specific user-remark instance.
