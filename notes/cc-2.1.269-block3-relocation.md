# What left the cached system block in 2.1.269

> **Dated record.** Claude Code **2.1.269**, one account, one capture session
> (2026-09-11, re-derived 2026-09-30). Every figure and `src/chunk-*.js` citation
> is that build's: do not re-pin them, re-measure. The artifacts are
> `docs/system-prompt-snapshot/<model-id>/<variant>/`, whose `README.md` carries
> the capture procedure.

The substantive change this round, identical in shape across all three models (diffed
directly): four things left the cached, 1h-TTL block, and no tool or behavioral section moved
with them.

**Absent from the request, but not a code removal** — the full JSON holds no replacement: the
act-when-you-have-enough-information paragraph (`"When you have enough information to act,
act. Do not re-derive facts already established..."`), introduced in 2.1.235, appears in no
2.1.269 capture. It is **still in the 2.1.269 source**: `src/chunk-dbb93264.js:69214` builds
block 3 as labelled fragments including `Jb("act_dont_rederive", () => DRo() ? NRo : null)`,
`NRo` this exact string and `DRo` (`:69182`) resolving `I("tengu_cedar_lantern", !0)` — a
GrowthBook flag defaulting to *on*. 2.1.235 has the identical gate under the same flag
(`zB('act_dont_rederive', () => (fdE() ? mdE : null))`, `src/globals/21.js:13381`). The
paragraph vanishing from every capture reads as the live flag value for this account, the same
category as the `SendFeedback`/`Artifact` observations here, not a code change.

**Relocated to a new per-message system-reminder** (in `messages[]` — see "messages
structure"): the entire `# Environment` per-session block (`"You have been invoked in the
following environment:"`, working directory, is-git-repo, platform, shell, OS version, the
`"You are powered by the model named ..."` / `"Assistant knowledge cutoff is ..."` lines), and
`gitStatus` — no longer appended to any system block in **any** variant, the custom
`--system-prompt` one included.

**Genuinely removed from the assembly code**: the `# Scratchpad Directory` section (5 bullets,
session-specific path), introduced in 2.1.235. Its content lives inside the relocated
`# Environment` reminder, but the section-builder call is gone from the list: 2.1.235 had
`zB('scratchpad', () => cvi())` (`src/globals/21.js`); nothing producing this content appears
in 2.1.269's list at `src/chunk-dbb93264.js:69205-69224`.

What's left under `# Environment` in the cached block is static ecosystem trivia — model-id
roster, available surfaces, fast mode — so the block no longer holds anything that busts its
cache across sessions with different directories, branches or dates.

Opus's block 3 also picked up one real wording change: `"Do not call the AgentTool unless the
user requested it"` / `"Do not use workflows or deep-research unless the user requested it"`
became `"Do not use the Agent tool, workflows, or deep-research unless the user, a CLAUDE.md
file, or a skill asks for it"` — the set of things that count as authorization widened.
Sonnet's block 3 has no equivalent sentence in either version.

