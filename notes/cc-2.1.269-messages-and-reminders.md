# What 2.1.269 moved out of the system prompt and into messages[]

> **Dated record.** Claude Code **2.1.269**, one account, one capture session
> (2026-09-11, re-derived 2026-09-30). Every figure and `src/chunk-*.js` citation
> is that build's: do not re-pin them, re-measure. The artifacts are
> `docs/system-prompt-snapshot/<model-id>/<variant>/`, whose `README.md` carries
> the capture procedure.

The 2.1.235 split survives: 5-family models get a dedicated `role: "system"` message after
the first user message; opus-4-7 still gets everything inline in `messages[0]`.

**New in messages[0]** (all models, every variant including `--system-prompt` and a
general-purpose subagent's first message): a system-reminder giving git attribution
instructions, between the userEmail/gitStatus reminder and the user's text:

```
<system-reminder>
Attribution for git commits and pull requests you create from here on (this
replaces Claude Code's own earlier attribution guidance, such as a previous
copy of this reminder; the user's own instructions about these lines, such as
a CLAUDE.md or memory rule, take precedence over this reminder, but do not add
attribution lines this reminder leaves out):
- End git commit messages with:
Co-Authored-By: Claude <Model Name> <noreply@anthropic.com>
- End pull request descriptions with:
🤖 Generated with [Claude Code](https://claude.com/claude-code)
</system-reminder>
```

`<Model Name>` is templated per model (`Claude Sonnet 5`, `Claude Opus 5`, `Claude Opus 4.7`)
— the other half of the `Bash` tool change above: a per-request reminder always matches the
live model where the hardcoded description could not. `gitStatus` moved into the same reminder
block as `userEmail`, unconditionally, in every variant including `--system-prompt`.

**New in the `role: "system"` message** (5-family) / **prepended within `messages[0]`**
(opus-4-7, and subagents): the per-session `# Environment` and model-identity content removed
from the cached block, verbatim, plus the `# Scratchpad Directory` content folded into the same
reminder:

```
<system-reminder>
# Environment
You have been invoked in the following environment: 
 - Primary working directory: ...
 - Is a git repository: true
 - Platform: linux
 - Shell: bash
 - OS Version: ...
 - Scratchpad directory: ... — always use it for temporary files ...
</system-reminder>

<system-reminder>
You are powered by the model named <Model>. The exact model ID is <id>.
Assistant knowledge cutoff is <date>.
</system-reminder>
```

(Sonnet wraps each reminder in `<system-reminder>` tags; opus emits the same content bare, the
split the 2.1.235 doc documented.) For a subagent this reminder is ordered *after* the
deferred-tools reminder rather than before it (`subagent/subagents/001-request.json`).

**Removed**: the `## Auto Mode Active` reminder (and opus's bare `"While auto mode is active:
..."`) is **absent from all 13 `request.json` files in this batch** — 11 top-level captures
plus both `sonnet-5/subagent` children, checked case-insensitively — where 2.1.235 had it in
eight of eight. `capture.py`'s invocation is unchanged outside the trust-dialog fix, so this is
not a capture artifact; not a rename either, since `"bypass permissions mode"` (a live reminder
heading in differently-launched sessions) is also absent from every capture; and not a 2.1.269
content change: the renderer, `case "auto_mode":` at `src/chunk-dbb93264.js:235899`, builds
three texts from one event object — `e.bypass` gives `"While bypass permissions mode is
active:\n\n${E}"` (bash-first steer text, no heading), `e.steerOnly` the same shape headed
`"While auto mode is active:"`, otherwise the full `## Auto Mode Active` text — and 2.1.235 has
the identical three-way branch at `src/globals/20.js:24362`. What is not established is
*whether* the case fires for a plain `capture.py` session, which depends on something upstream
of this function.

**A `claude.sh` session reaches `e.bypass`**, read off a live 2.1.269 log: an `auto_mode`
attachment whose `rendered[].content` is `<system-reminder>\nWhile bypass permissions mode is
active:\n\n` followed by the bash-first steer text. A plain `capture.py` session takes the
default permission mode and shows none of the three; the uncaptured `bypass-permissions`
variant is what would put the two side by side.

Reminder-list content also drifted independent of both mechanisms (skill/agent content, not
CLI behavior):
- The `claude-code-guide` agent's description dropped `"early-access enablement"` from its
  `claude plugin eval` bullet.
- `Explore` and `Plan`'s exclusion lists grew `ArtifactComments`, `ArtifactData`,
  `ArtifactCheck` — identifiers that never appear as their own `tools[]` entries in any capture.
- Several skill descriptions changed wording (`design`, `dataviz`, `artifact-design`,
  `artifact-diagramming`, `artifact-capabilities`), and `workflow-authoring` appeared — the
  authoring reference `Workflow`'s description now points to instead of including inline.

Per-message character totals, measured over the full `messages[]` array minus the fixed
17-character canary (`"say exactly: done"`, once per request as the final text block of
`messages[0]`):

| | Opus 4.7 | Sonnet 5 | Opus 5 |
|---|---|---|---|
| 2.1.235 | 13,042 | 13,026 | 12,043 |
| 2.1.269 | 14,688 | 14,677 | 14,201 |

All three grew by roughly 1,600-2,150 chars: + the Attribution reminder (~330 chars) + the
relocated Environment/identity reminder (~500-700 chars, larger than what left block 3 because
it also carries the Scratchpad content) + the skill/agent wording growth, − the removed Auto
Mode reminder (~600-700 chars sonnet-side).

