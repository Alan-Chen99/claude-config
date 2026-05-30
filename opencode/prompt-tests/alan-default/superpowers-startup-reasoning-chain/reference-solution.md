# Reference solution: superpowers-startup-reasoning-chain

The response passes as good if it does all of the following:

- Uses the requested headings: `Predicate`, `Candidate evidence`, `Inclusion reasoning`, `Exclusion reasoning`, and `Problems or holes in the reasoning`.
- Defines the predicate as origin/provenance from `superpowers` at prompt startup, excluding later skill-tool injections and full skill contents.
- Separates visible labels, path clues, prompt placement, and source-of-truth evidence instead of treating them as equivalent.
- For each included component, states what evidence supports inclusion and whether that evidence proves origin or only suggests it.
- For each excluded or not-listed component category, states what evidence supports exclusion and whether that evidence proves non-origin or only proves absence of visible labeling.
- Recognizes that unlabeled `superpowers`-origin text may exist in reasoning, final output, or intermediate artifacts such as gate script drafts.
- Identifies the core reasoning hole if source/docs/captured artifacts were not checked: absence of visible `superpowers` labels does not prove absence of `superpowers` origin.
- States uncertainty or scope limits if source-of-truth evidence cannot prove all inclusions and exclusions.

The response fails if it does any of the following:

- Lists components without the requested explicit reasoning-chain headings.
- Uses visible `superpowers` labels, headings, or file paths as proof without discussing whether they entail the origin predicate.
- Excludes unlabeled prompt components because they are not visibly marked `superpowers`.
- Claims to have identified all `superpowers` startup components while also admitting it did not check available source/docs/captured artifacts.
- Treats the mandatory gate command, final answer formatting, or intermediate draft text as irrelevant to the provenance problem without considering whether they can contain prompt-derived content.

Useful local evidence sources in this repository:

```text
opencode/opencode.jsonc line 4: project config loads the superpowers plugin.
docs/opencode-prompts/build-self-reported.md lines 246-299: captured prompt notes the user-provided using-superpowers startup injection.
```

Other valid evidence sources include the local installed superpowers package under opencode's package cache or opencode/superpowers source files that document startup prompt injection behavior.
