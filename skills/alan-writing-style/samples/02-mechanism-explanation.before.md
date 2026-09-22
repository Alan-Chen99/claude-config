## Between-worker contract

Ralph gives each iteration a fresh context; only files carry over (scratchpad, memories, `decisions.md`, git). The contract in `ralph/build.yml` is the rules between a worker and the workers before and after it, so that workers with no shared memory still work as one engineer on one task.

The idea is that no iteration has authority over later ones. Text left behind is context only unless marked `(instruction)`, and even that can be invalidated later with rationale in scratchpad. Same for code -- any prior change can be undone. The marker exists because instruction-like text is under-reviewed otherwise.

Each iteration starts by finding 3 or more significant problems in prior work (fact, quality, workflow). Workflow problems matter most. ex: user says TDD but prior agent wrote no tests -- adding tests afterwards only patches the symptom; the fix is to amend the contract and revert affected work.

Note: the contract can amend itself via `(contract)` notes, but only from observed problems, not speculatively; verification of the final version cannot be relaxed.
