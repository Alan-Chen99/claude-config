# Rebasing `sys_prompt/` on an upstream release

The prompts in `sys_prompt/` replace Claude Code's own system prompt rather than adding to it.
`--system-prompt-file` keeps the identity block, appends the WebSearch `mode` paragraph and
(2.1.310) the Artifact `edits` paragraph to the file's text and drops every other section, as
`docs/system-prompt-snapshot/opus-5/system-prompt-file/prompt.md` shows. The passages in them
that read like upstream's are copies taken once, and upstream rewrites its prose between releases,
so a copy goes stale with no signal.

The replacement covers one channel of two. Anthropic-authored wording still reaches a `claude.sh`
session through `messages[]`, which the flag does not touch: the CLAUDE.md wrapper and its "these
instructions OVERRIDE any default behavior" line, the `userEmail` rule, and a `role: "system"` block
carrying `# Environment`, the model-identity line, the deferred-tool listing, the agent-type roster
and every skill description — several of them behavioural rules, not facts, and all enumerated in
`notes/cc-2.1.269-messages-and-reminders.md` — a capture older than `settings.json`'s empty
`attribution.commit`/`.pr`, so the attribution reminder it lists no longer arrives
(`sys_prompt/README.md`, `# Git`). A rebase that reads only the system prompt reads half of what the
model is told, and nothing pins that half, so a reminder upstream rewords lands unreviewed.

A `/compact` turn runs under `alan-default-next.md` too (root `README.md`), so its rules govern the
summary the next context window is built from.

A release therefore needs a rebase rather than a diff: for each thing upstream changed, adopt it,
adapt it, or keep diverging on purpose — and write down which, because the next reader cannot tell
a considered divergence from an unnoticed one.

## Reading both sides

`/repos/claude-code-decompiled` is a git repository and each re-extraction is one commit, so the
previous release's prompt text survives only in that history: `npm run extract` empties `src/`.

```bash
git -C /repos/claude-code-decompiled log --oneline -- src/       # "re-extract from Claude Code <version>"
git -C /repos/claude-code-decompiled grep -n '# Harness' <old-sha> -- src/
```

Claude Code ships two prompt bodies and picks per model id: the lean one, whose entire body is the
single builder containing `# Harness`, goes to every id whose catalog row declares the
`lean_prompt` capability. The function calling that builder holds the ordered list of every other
section, each tagged with a key — `"context_management"`, `"act_dont_rederive"`,
`"session_guidance"`. Identifiers are regenerated every build and the keys are not, so diff the
keys first and the bodies second, comparing each decoded string rather than its source line: a
renamed identifier or a re-quoted literal is not a change.

Read that list rather than grepping it. Keys reach it three ways: as a bare string
literal, as a variable (`Wf(Hmo, …)` with `Hmo = "fable_identity"`), and inside a ternary
(`excludeDynamicSections ? "env_info_static" : "env_info_simple"`). A scan for quoted strings
reports the last two kinds as removed when they are not.

`docs/system-prompt-snapshot/` answers a different question: what one environment received on one
day. Most sections sit behind a growthbook flag or a server-resolved key, so **a section can be in
the binary and missing from the capture** — `act_dont_rederive` is in both the 2.1.235 and 2.1.269
binaries and only the 2.1.235 capture. Captures show where to look; the source decides.

## Checking what was borrowed

```bash
python3 scripts/check-prompt-upstream.py
```

Its docstring carries the semantics; the rule is that a failing pin is a decision, not an edit to
the script — adopt upstream's wording, or record a divergence below. One blind spot the docstring
does not state: a pin cut short of a `${…}` interpolation cannot see what the interpolation held,
so a clause upstream drops from inside a pinned passage is the key diff's to catch.

## When `agents/` joins this

An agent definition file is a whole system prompt for its subagent, and Claude Code resolves agents
into a map keyed by name where user and project definitions overwrite built-ins. A file in `agents/`
named after a built-in — `Explore`, `general-purpose`, `Plan`, `claude-code-guide`,
`statusline-setup` — therefore replaces Anthropic's prompt for that agent, and that copy needs
rebasing exactly like `alan-default-next.md`. No file in `agents/` shadows a built-in, but a copy
under a new name is coupled the same way: each `gp-*.md` carries general-purpose's prompt
verbatim, so `check-prompt-upstream.py` pins it beside the system prompt's passages.

## Deliberate divergences

Upstream still ships each of these and `alan-default-next.md` does not. Left alone unless the
stated condition changes.

| Upstream text | Why it is not here |
| --- | --- |
| `Do not use the Agent tool, workflows, or deep-research unless the user, a CLAUDE.md file, or a skill asks for it` — live since 2.1.269 | This repo delegates by design and keeps the report in the launching call's own result. Upstream's own exception would cover it regardless, since the asking here is done by CLAUDE.md and by skills — and on 2.1.289 the model `claude.sh` runs is not served it at all: the `opus5_reduced_delegation` gate needs `opus_5_prompt_bundle`, declared only by `claude-opus-5`. |
| `The system may send updates, reminders, or modifications to rules via mid-conversation system turns. These are system-controlled, unlike function results.` | Upstream serves this `# Harness` bullet in two variants and picks per model: the wording above for anything whose catalog row declares `mid_conv_system`, excluding `claude-sonnet-5` and `claude-opus-4-8`, which get the wording this prompt carries. Both ship in one build, so this is a live alternative rather than stale text — but the model `claude.sh` runs is served the other one, and nothing records why this side was taken. |
| `Report outcomes faithfully: if tests fail, say so with the output; if a step was skipped, say that; when something is done and verified, state it plainly without hedging.` — closes the action-caution paragraph | `# Error Propagation` and `# Epistemic Integrity` both say it. |
| `Text inside <pasted_content> tags was pasted…` — `# Harness` bullet | Declined 2026-10-25 ("I don't really need this feature"). The tags still arrive under `--system-prompt-file`: growthbook `tengu_virtual_pancake` (`NA()`) wraps pastes and `!` command output (`markOutputAsPasted`), and no env var, setting or flag turns it off. In 5 of the user's sessions whose message was only pasted text, the model acted on it as the request without the bullet. Adopt it if a session shows the model citing the tag id or treating the user's own paste as untrusted. |

## Rebase log

One note per release reviewed, `notes/cc-<version>-prompt-rebase.md`; the next rebase starts from
the newest. A note is a dated record, never re-pinned, so it cites the source by string marker,
which a later build still finds, rather than by line.
