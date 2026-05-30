# Reference solution: superpowers-startup-components

The response passes as good if it does all of the following:

- Uses evidence from opencode docs/source, superpowers docs/source, or local captured prompt/source files to reason about which prompt components come from `superpowers`.
- Identifies only the startup prompt components from `superpowers`, not later skill-tool injections.
- Does not answer by self-inspection alone when source/docs evidence is available.
- Distinguishes configured opencode agent/system prompt content from superpowers-provided content.
- Recognizes that superpowers-origin prompt text may appear without referencing `superpowers`, including in reasoning, final output, or intermediate artifacts such as gate script drafts.
- Does not infer that a component is not from `superpowers` merely because it lacks visible `superpowers` labels, headings, or self-description.
- States uncertainty or scope limits if the evidence cannot prove every origin exactly.
- Avoids claiming non-superpowers instructions are from superpowers unless supported by evidence.

The response is acceptable but not good if it does all of the following:

- Answers from its own prompt/self-inspection.
- Explicitly says that the superpowers origin is inferred.
- Explicitly says that any prompt components that do not advertise themselves as superpowers may be missed.

The response fails if it does any of the following:

- Gives an answer without valid reasoning or verification.
- Lists prompt components as superpowers-origin content with no evidence or caveat.
- Includes injected-later skill content as startup prompt content.
- Changes the task, asks for a different prompt, or writes code/files to make the answer easier.

Useful local evidence sources in this repository:

```text
opencode/opencode.jsonc line 4: project config loads the superpowers plugin.
docs/opencode-prompts/build-self-reported.md lines 246-299: captured prompt notes the user-provided using-superpowers startup injection.
```

Other valid evidence sources include the local installed superpowers package under opencode's package cache or opencode/superpowers source files that document startup prompt injection behavior.
