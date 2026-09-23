## The between-worker contract

Aims, all at once: a prior iteration cannot bind later ones blindly; later iterations reuse what worked (tests run the same way, mistakes are not repeated); later iterations fix prior mistakes.

Mechanism: three tiers of text a worker can leave for later iterations, each with its own bar for adding, changing and removing. Unmarked is the tier with no bar.

> If you leave instructions or rules for future iterations, mark explicitly that this is instruction with a `(instruction)` notation. Any text from prior iterations not marked with `(instruction)` is not instruction -- it is context only. Later iterations are free to remove these instructions via override.

`(instruction)`: a marker to add, a review to remove. The marker is not what makes the text bind:

> The `(instruction)` notation in the worker contract below is NOT a forwarding mechanism for passing binding instructions between iterations. Insted "binding instructions" is the default behavior and `(instruction)` serve as a marker so that later iterations can review and invalidates the instruction. This is useful becuase instruction-like text becomes under-reviewed otherwise.

`(contract)`: an observed problem to add, a later override to change back.

> Exists to amend the default contract and put higher-status meta rules where `(instruction)` cannot do that.
> This has not yet happened in practice; ... (three example contracts)

> This is a self-improving workflow where work is expected to become more efficient towards the particular task being worked on and fixing structural workflow problems as iterations goes via amending this contract. To acomplish this, you are allowed to add overrides for this contract, but only based on observed problems or inefficiencies rather than speculatively from the task. If you do so, the updated version must be clearly written into scratchpad with a `(contract)` notation and form a coherent between-worker contract. Later workers are free to modify or change back to default via a later contract override. Verification of final version cannot be relaxed.

Review, every iteration after the first:

> Unless you are the first iteration, find 3 or more most significant problems or concerns -- things the prior agents did that you think they should not have, or should have done differently -- in prior iterations. Then, write these into scratchpad.md.
