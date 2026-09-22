## Between-worker contract

Three tiers of text a worker can leave for later iterations: unmarked, `(instruction)`, `(contract)`. Each has its own bar for adding, changing and removing, and the split is what lets the same text do three things at once -- a prior iteration cannot bind later ones blindly, later iterations reuse what worked (tests run the same way, mistakes are not repeated), and later iterations fix prior mistakes.

Marking and removal:

> If you leave instructions or rules for future iterations, mark explicitly that this is instruction with a `(instruction)` notation. Any text from prior iterations not marked with `(instruction)` is not instruction -- it is context only. Later iterations are free to remove these instructions via override.

`(instruction)`: a marker for review. Binding is the _default_ already, so the notation forwards nothing.

> The `(instruction)` notation in the worker contract below is NOT a forwarding mechanism for passing binding instructions between iterations. Insted "binding instructions" is the default behavior and `(instruction)` serve as a marker so that later iterations can review and invalidates the instruction. This is useful becuase instruction-like text becomes under-reviewed otherwise.

`(contract)`: the tier above `(instruction)`.

> Exists to amend the default contract and put higher-status meta rules where `(instruction)` cannot do that.

The bar for adding one:

> ... To acomplish this, you are allowed to add overrides for this contract, but only based on observed problems or inefficiencies rather than speculatively from the task. If you do so, the updated version must be clearly written into scratchpad with a `(contract)` notation and form a coherent between-worker contract. Later workers are free to modify or change back to default via a later contract override. Verification of final version cannot be relaxed.

(cut: the sentence before it, framing the workflow as self-improving)

Not used yet: no amendment has happened in practice.

Review: every iteration after the first opens by reviewing prior work.

> Unless you are the first iteration, find 3 or more most significant problems or concerns -- things the prior agents did that you think they should not have, or should have done differently -- in prior iterations. Then, write these into scratchpad.md.
