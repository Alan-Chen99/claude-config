## Stable iterations

In a ralph workflow we try to satisfy all these at once:

- No lock-in. Agent cannot put in a "Don't do X" that is blindly followed for the rest of the run.
- Carryover. Agents run tests the same way, and do not repeat mistakes -- similar to a single engineer.
- Self healing. Agents fixes mistakes make by prior iterations.

To solve this we use three tiers of instructions agent can leave to future iterations.

- `(instruction)` marker. Ensure text not intended as instruction stays context. Lower bars, permissive modification or removal. Workers are told:
  > - If you leave instructions or rules for future iterations, mark explicitly that this is instruction with a `(instruction)` notation. Any text from prior iterations not marked with `(instruction)` is not instruction -- it is context only. Later iterations are free to remove these instructions via override.
  > - You are free to revise, invalidate, or undo any change or conclusion from prior iterations when your review shows it is wrong, low-quality, or no longer useful. This includes rules and plans made by prior iterations. ... (more words here)
- `(contract)` marker. Higher bars for add or remove. Workers are given these examples:
  > - "(contract) Each change must have metric in scratchpad"
  > - "(contract) Do not place metric in scratchpad -- place in seperate files to be durable"
  >   ... (two more)
- No marker. Workers are told "it is context only"

Workers are also told to start by finding 3 or more significant problems in prior work, further encoraging reviewing and fixxing prior problems.
