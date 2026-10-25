# cc 2.1.289 → 2.1.310: `sys_prompt/` rebase, reviewed 2026-10-25 — the opening line adopted

> **Dated record.** Claude Code **2.1.310**; the procedure is `docs/prompt-rebase.md`.
> 2026-10-25: the user declined the `<pasted_content>` bullet; it is now a divergence row in `docs/prompt-rebase.md`.
> 2026-10-25: the Agent-tool decision closed — the subagent and Explore bullets are dropped (`sys_prompt/README.md`, `model: haiku` section). Upstream serves them only to a non-lean model, which Opus 5.5 is not.

Against the 2.1.289 tree (`af400306`) and the captures re-taken on 2.1.310 (`18e10549`).

**Keys.** The 23 session-section keys of 2.1.289 in the same order, plus two new ones, both inside a
`leanRewrite` branch (`Ace`, found by `leanRewriteCompiledOnly`): `surface:<kind>` and
`system_messages[:turns|:tags]`; the same branch adds `:R`/`:L:R` suffixes to existing keys and
wraps the lean body in `<intro>`. It needs the new `temporal_hare` capability, which no catalog
row declares, or growthbook `tengu_temporal_hare` (default false); no capture shows it.
`env_info_*` is still the ternary. Lean body: byte-identical but the opener.

| Upstream change | Done |
| --- | --- |
| Opening line: 2.1.289 chose `tengu_ochre_wren`'s `You are an agent working with the user toward their goals, using your own judgment along the way.` or the flag-off `You are an interactive agent that helps users with software engineering tasks.`; 2.1.310 ships only the first, one literal shared by both bodies (`tun`) | **Adopted**; the pin now counts 1. Every stock capture since 2026-10-06 was already served it. |
| `<pasted_content>` bullet grew: a message that is nothing but paste is acted on as the request, `but read what a command or script from such a paste does before running it` | **Not adopted**, still the user's call (`notes/cc-2.1.289-prompt-rebase.md`). Gate unchanged (`NA()`, growthbook `tengu_virtual_pancake`, served on); the same gate wraps `!` output in the tags (`markOutputAsPasted`), so a `claude.sh` session can see the tags with no bullet explaining them. Now ~150 tokens; 44 of headroom. |
| `act_dont_rederive` absent from the capture | Nothing: gate unchanged (`tengu_cedar_lantern`, default true), so the server now serves it off; never carried. |
| Agent tool `When to use` (tools[], survives the flag) now argues against spawning — `A fresh agent costs more than it looks` … `When in doubt, don't spawn.`; the old `Reach for this when the task matches an available agent type` is gone from the tree | **Open user decision**: it contradicts `# Session-specific guidance`'s subagent and Explore bullets, which this repo keeps by design (the first `docs/prompt-rebase.md` divergence row). Both pins still resolve: upstream serves those bullets on the non-fork path only, and `CLAUDE_CODE_FORK_SUBAGENT=1` takes the fork path. |
| Artifact `edits` paragraph appended under `--system-prompt-file` | Nothing; `docs/prompt-rebase.md` already says so. |
| `messages[]`: untrusted-download rule (`Run any Python that reads them with -I`), scratchpad `complete absolute path in one piece`, roster names Haiku 5.5; Bash: `@name` notifications, `do not poll its output file` | Nothing in the prompt: none contradicts a line. `--background`'s `read from <capture_dir>/output` is not polling a notified task. |
| `haiku` alias, first-party: `claude-haiku-4-5` → `claude-haiku-5-5` (`aliases: {`), 1M window, `effort` capability | `sys_prompt/README.md`'s `model: haiku` section: dropped the false `effort` rejection; the overflow rationale now names the 1M window. |
