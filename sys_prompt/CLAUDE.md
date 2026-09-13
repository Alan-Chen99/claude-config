# sys_prompt/

Full replacement system prompts loaded via `--system-prompt-file` by `scripts/claude.sh`.
Background and forked sessions do not inherit them — read `docs/background-sessions.md` before editing.

## Files

| File                   | What                                                  | When to read |
| ---------------------- | ----------------------------------------------------- | ------------ |
| `alan-default.md`      | Known-good production prompt; forked from Claude Code's non-lean prompt body | -            |
| `alan-default-next.md` | Active development prompt, the one `claude.sh` loads; forked from the lean body Opus 5 receives | -            |

## Keep it concise

Every token here is spent on every request of every session and displaces the user's work from the
context window. A line the model would honour unprompted, or that restates a neighbour, costs context
and buys nothing.

After any edit:

1. Re-read the passage and cut a word. Repeat until cutting another would lose meaning.
2. Re-read the surrounding section. If a neighbouring line now says the same thing, delete one.
3. Name the behaviour that changes without the line. If you cannot, drop the line.

Three words can be enough — ``Prefer `model: haiku`.`` is a complete rule. Anything that dates the
line goes in this file rather than the prompt: version numbers, issue links, dates, measurements,
and the reasoning that justified the line in the first place.

Detail that fails step 3 is not discarded — it moves here, to `docs/`, or to `notes/`. The prompt
states the rule; the file carries the reasoning. That split is what lets step 1 cut hard without
losing anything.

Measure before and after:

```bash
agent-tools count-tokens --api --file sys_prompt/alan-default-next.md
```

## Rebasing on an upstream release

These files replace Claude Code's own system prompt rather than adding to it.
`--system-prompt-file` keeps one block — `You are Claude Code, Anthropic's official CLI for
Claude.` — and drops every other section, which
`docs/system-prompt-snapshot/opus-5/system-prompt-file/prompt.md` shows in full. So no
wording Anthropic ships reaches a `claude.sh` session, and the passages here that read like
upstream's are copies taken once. Upstream rewrites its prose between releases; a copy goes stale
with no signal at all.

A release therefore needs a rebase rather than a diff: for each thing upstream changed, adopt it,
adapt it, or keep diverging on purpose — and write down which, because the next reader cannot tell
a considered divergence from an unnoticed one.

### Reading both sides

`/repos/claude-code-decompiled` is a git repository and each re-extraction is one commit, so the
previous release's prompt text survives only in that history — `npm run extract` empties `src/`
first.

```bash
git -C /repos/claude-code-decompiled log --oneline -- src/       # "re-extract from Claude Code <version>"
git -C /repos/claude-code-decompiled grep -n '# Harness' <old-sha> -- src/
```

Claude Code ships two prompt bodies and picks per model; Opus 5 gets the lean one, whose entire
body is the single builder containing `# Harness`. The function that calls that builder holds the
ordered list of every other section, each tagged with a key — `"context_management"`,
`"act_dont_rederive"`, `"session_guidance"`. Identifiers are regenerated every build and the keys
are not, so diff the key list first and the section bodies second.

Read that list rather than grepping it. Keys reach the assembler three ways: as a bare string
literal, as a variable (`Jb(dRo, …)` with `dRo = "fable_identity"`), and inside a ternary
(`excludeDynamicSections ? "env_info_static" : "env_info_simple"`). A scan for quoted strings
reports the last two kinds as removed when they are not.

`docs/system-prompt-snapshot/` answers a different question: what one environment received on one
day. Most sections sit behind a growthbook flag or an env var resolved server-side per request, so
**a section can be in the binary and missing from the capture**. `act_dont_rederive` is in both the
2.1.235 and 2.1.269 binaries but only the 2.1.235 capture — the flag flipped, the release did not
drop it. Captures show where to look; the source decides.

### Checking what was borrowed

```bash
python3 scripts/check-prompt-upstream.py
```

It pins every passage `alan-default-next.md` and the env-context hook (`src/claude_config/env_context/`)
took from upstream, and requires each verbatim on both sides, as many times as recorded — the two
prompt bodies are separate literals, so a passage in both can move in one. A failing pin is a
decision, not an edit to the script: adopt upstream's wording, or record a divergence below. It is
silent about upstream text this prompt never carried; new sections come from the key diff above.

### When `agents/` joins this

An agent definition file is a whole system prompt for its subagent, and Claude Code resolves agents
into a map keyed by name where user and project definitions overwrite built-ins. A file in `agents/`
named after a built-in — `Explore`, `general-purpose`, `Plan`, `claude-code-guide`,
`statusline-setup` — therefore replaces Anthropic's prompt for that agent, and that copy needs
rebasing exactly like this one. The six files in `agents/` today are all new names, so none is
upstream-coupled and `check-prompt-upstream.py` pins nothing from them. Adding a shadow is what
changes that.

### Deliberate divergences

Upstream still ships each of these and this prompt does not. Left alone unless the stated condition
changes.

| Upstream text | Why it is not here |
| --- | --- |
| `Do not use the Agent tool, workflows, or deep-research unless the user, a CLAUDE.md file, or a skill asks for it` — live for Opus 5 since 2.1.269 | This repo delegates by design: `settings.json` holds subagents in the foreground so a report returns as the launching call's result, and `# Session-specific guidance` says when to spawn one. Upstream's own exception would cover it regardless, since the asking here is done by CLAUDE.md and by skills. |
| `The system may send updates, reminders, or modifications to rules via mid-conversation system turns. These are system-controlled, unlike function results.` | Upstream serves this `# Harness` bullet in two variants and picks per model. In the 2.1.269 captures Opus 5 and Fable 5 get the wording above; Opus 4.8 gets the wording this prompt carries. Both ship in one build, so this is a live alternative rather than stale text — but the model `claude.sh` runs is served the other one, and nothing records why this side was taken. |
| `Report outcomes faithfully: if tests fail, say so with the output; if a step was skipped, say that; when something is done and verified, state it plainly without hedging.` — closes the action-caution paragraph | `# Error Propagation` and `# Epistemic Integrity` say it at length. |
| `If what you find contradicts how it was described, or you didn't create it, surface that instead of proceeding` — follows `look at the target` | **Not reviewed.** It predates the 2.1.235 baseline and no entry explains it. Nothing else in the prompt says what to do when the look turns up a surprise; `# Executing actions with care` covers only the pattern-matched case. Decide it at the next edit to that section. |

### Rebase log

One entry per release reviewed. The next rebase starts from the last entry, so entries stay.

#### 2.1.235 → 2.1.269, reviewed 2026-09-12 — no prompt text changed

Both prompt files reviewed, against a 2.1.235 tree extracted beside the installed one
(`git -C /repos/claude-code-decompiled archive 56801e78 src`). Section keys were diffed, then every
section present in both builds had its text compared, not only the sections these files borrow —
a key list shows what a release added and removed, never what it rewrote in place.

All thirteen pins in `scripts/check-prompt-upstream.py` resolve against both trees. Of the sections
this prompt does not borrow, `bg-session`, `focus_mode`, `brief` and `subagent_steer_delegation`
differ only in renamed identifiers and in the quote style the decompiler emits, so compare the
decoded string rather than the source line.

| Upstream change | Done |
| --- | --- |
| `language`, `output_style` and `scratchpad` dropped as system-prompt sections | Nothing; none was carried here. `output_style` was handled in 60edda3. The scratchpad is now a bullet inside the environment attachment, which is what leaves `agent-tools env-context` duplicating it. |
| the environment block left the system prompt for a `messages[]` attachment, leaving three bullets behind | Nothing; never carried here. |
| `fable_identity` gained a Fable 5.1 variant | Nothing; this prompt is loaded for Opus 5. |
| new `opus5_reduced_delegation` section, replacing two 2.1.235 lines that rode the `heron_brook` fallback and loosening them to admit CLAUDE.md and skills | Deliberate divergence, above. |
| new `willow_tern` section, `# Writing for the user`: a ten-rule contract for the final message | **Not adopted.** It is off by default for Opus 5, so it is a preview rather than shipped guidance, and it contradicts `## Response template`, which requires headers on every response where the new text bans them under about 500 words. Revisit if it ships on by default. |
| new `brook_heron` section, whose text arrives from client data or growthbook keyed by model | Nothing to rebase — served, not shipped. Recorded so that unfamiliar text in a future capture is recognised instead of hunted for in the binary. |
| everything `alan-default-next.md` borrows: the five `# Harness` bullets, the action-caution paragraph, `# Context management`, three `# Session-specific guidance` bullets | Byte-identical across the two builds. Now pinned by `scripts/check-prompt-upstream.py` instead of re-read by hand. |
| the environment block, which the env-context hook re-emits: its facts left the system prompt for the attachment, it gained a scratchpad bullet, and the model and knowledge-cutoff lines left it | Nothing, and that is a deferred decision rather than a finished one — a `--system-prompt-file` session now receives Claude Code's own copy as well, so most of what the hook renders is a second copy. `env_context/__main__.py` holds the finding. Its two borrowed sentences are unchanged and now pinned. |
| the legacy prompt body, which `alan-default.md` is the copy of | Nothing. The four removals above hit that branch too, and its six prose sections are unchanged between the 2.1.235 and 2.1.269 sonnet captures. Unpinned: nothing loads this file unless a prompt-test runner is given it explicitly. |

## Why the prompt says what it says

Reasoning cut from the prompt under step 3 above, kept so a future edit can tell a live rule from
cargo. Each entry names what would retire it.

### `Prefer model: haiku` on Explore spawns

Claude Code 2.1.198 (2026-07-01) changed the built-in Explore agent's model from `haiku` to
`inherit`, so an Explore spawn now runs the session's model unless the call passes one. The change
was a reliability fix, not a quality one: issue #45357 reported that a large MCP tool surface
overflowed Haiku's prompt limit and killed every spawn. That failure needs a heavy MCP install; a
session without one keeps Haiku's headroom, and Explore is scoped to locating code rather than
reviewing or analysing it.

`Prefer` carries the escape hatch, so the prompt does not spell one out: pass `sonnet` or `opus`
when a search is genuinely hard — tracing minified identifiers through decompiled chunks, say,
rather than finding a file. Haiku also drops the session's inherited `effort` setting, which the
API rejects for that model, and falls back from adaptive to plain extended thinking.

Passing the parameter per call, rather than shadowing the built-in with a user-defined `Explore`
agent: `omitClaudeMd` is set only on built-in agent definitions and is never read from frontmatter,
so a shadow re-attaches the whole CLAUDE.md hierarchy to every spawn.

`CLAUDE_CODE_SUBAGENT_MODEL_FORCE` (2.1.257, unset here) would override every per-spawn `model`,
turning this line into an instruction the harness discards; `CLAUDE_CODE_SUBAGENT_MODEL` would not,
since 2.1.251 made it a default that an explicit `model` beats.

Retire this if the built-in default returns to `haiku`, or if Explore spawns start failing on prompt
size — which would mean the MCP surface has grown into the case #45357 describes.
