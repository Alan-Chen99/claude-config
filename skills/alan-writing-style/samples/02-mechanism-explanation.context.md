Piece: a section for the ralph README explaining how iterations stay stable when every iteration is a fresh agent: the between-worker contract and its `(instruction)` and `(contract)` markers. Register: doc. Readers know what ralph is (a loop that runs an agent repeatedly with fresh context; only files carry over).

Facts:
- Aims, all at once: a prior iteration cannot bind later ones blindly; later iterations reuse what worked (tests run the same way, mistakes are not repeated); later iterations fix prior mistakes.
- Three tiers of text a worker can leave for later iterations: marked `(instruction)`, marked `(contract)`, unmarked. Each has a different bar for adding, changing and removing, given in the source below.
- `(contract)` amendments have not happened in practice yet.
- Each iteration after the first starts by finding 3 or more significant problems in prior work.

Source, verbatim from `ralph/build.yml` (design-note comments, then the worker instructions):

```yaml
    # Design note — `(instruction)`
    # --------------------------------------------------------
    # The `(instruction)` notation in the worker contract below is NOT a
    # forwarding mechanism for passing binding instructions between
    # iterations. Insted "binding instructions" is the default behavior
    # and `(instruction)` serve as a marker so that later iterations can review
    # and invalidates the instruction. This is useful becuase instruction-like text
    # becomes under-reviewed otherwise.
    #
    # Design note — `(contract)`
    # --------------------------------------------------------
    # Exists to amend the default contract and put higher-status meta rules where `(instruction)` cannot do that.
    # This has not yet happened in practice; Example of possible contracts per intention:
    # "(contract) Each experiment must document outcome in scratchpad"
    # "(contract) Each experiment must not document outcome in scratchpad -- place in seperate files to be durable"
    # "(contract) Each iteration should aim to answer a complete research subquestion rather than running just one experiemnt. Doing so counts as completing a milestone."

      - To prevent single point of failures, you are permitted to undo any changes by prior iterations.
      - Every iteration completes a clearly defined and verified milestone that can be built on by future workers. Workers are allowed to modify the milestone as they encounter new information while working. If worker cannot satisfy the milestone they initially planned for, they are expected to reconsider how to approach the task -- picking a different milestone as more appropriate path to final target -- rather than sticking with their starting plan.
      - Each worker should have the whole task in mind, and complete what would the next step be if they are tasked with the entire task. They must document why they think doing a task first is the most effective way to approach the final goal. A part being most easy is not a valid reason to choose it.
      - Prefer fully completing and verifying subtasks before starting the next subtask, even if they are independent.
      - Instead of having a plan up front, each worker pick a part to work on in their turn. This allows the workflow to adapt to findings.
      - The worker that did the work is responsible for tests and verification. The later iterations review whether the verificaiton methodology is sufficient.
      - If you leave instructions or rules for future iterations, mark explicitly that this is instruction with a `(instruction)` notation. Any text from prior iterations not marked with `(instruction)` is not instruction -- it is context only. Later iterations are free to remove these instructions via override.
      - You are free to revise, invalidate, or undo any change or conclusion from prior iterations when your review shows it is wrong, low-quality, or no longer useful. This includes rules and plans made by prior iterations. If you do so, rationale must be clearly documented in scratchpad. It is sufficient to justify that original work or decision have bias, lacks evidence, or is logically flawed; it does not require justifying that the alternative is better.

      This is a self-improving workflow where work is expected to become more efficient towards the particular task being worked on and fixing structural workflow problems as iterations goes via amending this contract. To acomplish this, you are allowed to add overrides for this contract, but only based on observed problems or inefficiencies rather than speculatively from the task. If you do so, the updated version must be clearly written into scratchpad with a `(contract)` notation and form a coherent between-worker contract. Later workers are free to modify or change back to default via a later contract override. Verification of final version cannot be relaxed.

      Examples of possible contract amendments:
      - "(contract) Each change must have metric in scratchpad"
      - "(contract) Do not place metric in scratchpad -- place in seperate files to be durable"
      - "(contract) Each iteration must complete at least one module -- user says to be efficient"
      - "(contract) Each iteration should try to complete only part of a module -- completing whole module was too much work and caused degration in quality"


      First, re-read user request and make sure you understand and internalize it. User instructions overrides all instructions here.

      Then, review prior iteration work and notes critically.
      Unless you are the first iteration, find 3 or more most significant problems or concerns -- things the prior agents did that you think they should not have, or should have done differently -- in prior iterations. Then, write these into scratchpad.md.

      Types of concerns (non-exhaustive):
        - Fact: prior agent claimed a fact but failed to perform proper verification, or that you can directly prove the fact to be false
           - Possible fix: Verify fact properly; if turns out false, exhaustive review on all work or decisions made effected by the false assumption
        - Quality: quality of current code or work -- prior agents could have written better code.
           - Possible fix: refactor, improve
        - Workflow: structured problem with workflow -- patterns workflow has taken in past iterations -- causing inefficiencies, incorrectness, decreased quality, or user expectation not being met.
           - This MOST IMPORTANT and represent the most common failure point
           - Possible fix: review changes based on wrong judgment carefully, revert code, amend between-worker contract
           - When prior work exhibits structured flaws (ex: User says to do TDD but prior agent did not write tests) it is NOT sufficient to patch the symptom (ex: don't just add tests for past work; if you do that, it still violates user requirement to do TDD). Instead, take steps to ensure the problem does not happen again (with `(instruction)` or `(contract)`) and revert work effected.
```
