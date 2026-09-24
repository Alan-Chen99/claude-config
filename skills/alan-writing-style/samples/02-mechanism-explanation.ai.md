## The between-worker contract

Every ralph iteration is a fresh agent with no memory of the last one; only files carry over. The text a worker leaves behind therefore has to do three things at once: keep a prior iteration from binding later ones blindly, let later iterations reuse what worked — tests run the same way, mistakes are not repeated — and let later iterations fix what earlier ones got wrong.

Ralph does this by sorting that text into three tiers, each with its own bar for being added, changed, or removed.

Unmarked text is context only. Anything a prior iteration wrote without a marker is information rather than a rule, and a later worker is free to ignore it.

`(instruction)` marks a rule meant to bind later iterations. It is not a forwarding mechanism for passing binding instructions between iterations — binding is already the default behavior. It is a marker that makes the rule reviewable, because instruction-like text becomes under-reviewed otherwise. A later worker can review an `(instruction)`, invalidate it, and remove it via override.

`(contract)` amends the default contract itself, and is where higher-status meta rules go when `(instruction)` cannot carry them. An amendment may only be added from an observed problem or inefficiency, never speculatively from the task; it is written into the scratchpad with the marker and must form a coherent between-worker contract. Later workers may modify it or change back to the default. Verification of the final version cannot be relaxed. No amendment has happened in practice yet.

The review itself is not optional. Every iteration after the first begins by finding three or more of the most significant problems in prior work.
