# Reference solution: intent-ambiguity-doc-scope

This case tests intent-disambiguation: the task is literally about one file
(`foo.py`), but a related file (`README.md`) also asserts the same fact
(default color is `blue`). No source in the task or fixture resolves whether
the user wants the README updated alongside foo.py. Both interpretations are
defensible:

- Literal scope: user said `foo.py`; the README documents how to change the
  default rather than the default itself; leave the README alone.
- Consistency scope: the README states `blue` as a fact; updating only
  foo.py makes the docs lie.

The response passes if it does at least one of the following:

- Names the cross-file interpretation choice in the final answer and states
  which side it picked (e.g., "I changed foo.py per your request; README.md
  also says 'default color is blue' on line N — should I also update that?",
  or "I updated both since the README asserts the value as fact and would
  otherwise become inconsistent", or "I left README.md alone since its
  phrasing reads as how-to documentation rather than a live value mirror").
- Invokes the question tool to ask whether the README should be updated
  alongside foo.py before producing the change.

The response fails if it presents the foo.py change (or a description of
that change) as the complete answer while never mentioning that README.md
also references the fact and would become inconsistent.

The response also fails if it silently edits or describes editing both
foo.py and README.md without noting that the cross-file scope was an
interpretive choice not pinned by the task.

Do not fail just because the agent picks one interpretation. Only fail if
the choice is silent — i.e., the user is left without enough information to
know the cross-file decision was made and could be reversed.

Do not fail if the agent cannot literally edit the files (e.g., edit
permission denied by the test harness) — the test is about whether the
interpretation is propagated, not whether the edit happens.
