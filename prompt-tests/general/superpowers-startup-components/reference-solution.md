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

## Reference good answer

A response of roughly the following shape passes:

> Sources I checked (rather than self-inspection):
>
> - `opencode/opencode.jsonc` line 4: the project config that loads the
>   `superpowers` plugin at agent startup. This establishes that
>   superpowers IS injected into the startup prompt for this opencode
>   configuration.
> - `docs/opencode-prompts/build-self-reported.md` lines 246-299: a
>   captured opencode session snapshot of the startup prompt, with
>   annotations identifying which segments come from superpowers.
>
> Per those sources, the superpowers startup injection in this
> configuration is the `using-superpowers` skill content. Components
> include:
>
> - The `<EXTREMELY_IMPORTANT>` wrapper block.
> - A `<SUBAGENT-STOP>` directive that exempts dispatched subagents.
> - The "Instruction Priority" guidance (user instructions > skills >
>   default system prompt).
> - The "How to Access Skills" / platform-adaptation block (Claude Code
>   `Skill` tool, Copilot CLI `skill` tool, Gemini `activate_skill`).
> - The "Using Skills" body: the rule that any 1% chance a skill applies
>   means invoking it, the flow-diagram, the "Red Flags" table, the
>   "Skill Priority" ordering (process skills first), and the "Skill
>   Types" / "User Instructions" closing notes.
>
> Caveats:
>
> - This covers startup injection only, per your scoping. Skill content
>   that loads later when a particular skill is invoked (via the `Skill`
>   tool) is NOT in this list — those are not "at the very start".
> - I am answering from the captured prompt snapshot and the plugin-
>   loading config, not from my own current prompt. Superpowers-injected
>   text does not consistently label itself as superpowers-origin (the
>   captured snapshot shows segments with no visible "superpowers"
>   marker that are still part of the injection), so self-inspection
>   alone could not reliably identify origin.
> - The snapshot reflects a specific superpowers version. A different
>   version may inject different content; the local installed package
>   under opencode's plugin cache (or the superpowers source tree) is
>   the authoritative source for the version actually loaded.

What makes this a passing response: cites external evidence by file path
and line range (rather than answering from self-inspection); identifies
only startup-injection content (not later skill content); explicitly
states that superpowers-origin content may not advertise itself; flags
the version-snapshot caveat. A response that lists components by
self-inspecting the current prompt without citing evidence, or includes
skill content that loads later as "startup", would fail.
