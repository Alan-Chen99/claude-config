# cc 2.1.269 → 2.1.289: `sys_prompt/` rebase, reviewed 2026-10-05/06 — one borrowed clause dropped upstream

> **Dated record.** Claude Code **2.1.289**; the procedure is `docs/prompt-rebase.md`.
> 2026-10-25: the opening line was adopted and the `<pasted_content>` bullet declined later; see `notes/cc-2.1.310-prompt-rebase.md`.

Against a 2.1.269 tree (`archive 8606fb66 src`). Same 23 keys in the same order; four bodies moved,
the rest byte-identical; all thirteen pins resolve.

**Which body, which model.** The `lean_prompt` capability on the catalog row decides (`Qr`/`dV`,
found by `"lean_prompt"`), and the legacy list it falls through to —
`sonnet`, `haiku`, `claude-3-`, opus 4.0–4.7 — is unchanged. Opus 5, Opus 5.5, Sonnet 5.5 and
Fable 5.1 all declare it (the catalog gained `claude-opus-5-5` and `claude-sonnet-5-5` this window,
moving Sonnet's branch). `fable_identity` stays `null`
for every Opus and Sonnet id. `"model": "opus"` is now `claude-opus-5-5` (`ln()`, found by
`e.opus55`), so **this prompt is loaded for Opus 5.5**, not Opus 5.

| Upstream change | Done |
| --- | --- |
| `action_caution` lost `. If what you find contradicts how it was described, or you didn't create it, surface that instead of proceeding`; clause and gate are both gone from the tree | **Adopted by deletion** — its divergence row is dropped. The `care/confirm-first` pin passed throughout: it stops at `look at the target`, where the clause was interpolated. |
| new `# Harness` bullet on `<pasted_content>` tags | **Not adopted**: growthbook `tengu_virtual_pancake`, coded default false — yet served **on** in every stock capture of 2026-10-06, as was `tengu_ochre_wren`'s opening line (`NMt`, found by `using your own judgment along the way`). Both are flag-on branches where this prompt carries the flag-off text; adopting the bullet (~80 tokens, 57 of headroom in `alan-default-next.md`) is the user's call. |
| `willow_tern`'s `# Writing for the user` | **Still not adopted**, and the gate now resolves (`gqo`, found by `tengu_willow_tern`): on for a `fable_5_1_prompt_bundle` model, off without `opus_5_prompt_bundle`, growthbook `tengu_willow_tern` (default false) otherwise — so Opus 5.5 cannot receive it. |
| a cloud-session bullet in `# Session-specific guidance`; a shortened fast-mode bullet in `# Environment`; 2.1.286's `Always run …/verify… right before the commit command`; 2.1.284's fix for a session told to use an absent `SendMessage` | Nothing: gated on a cloud session; never carried; inside the Bash `# Git` block behind the same gate; the tool's own description, arriving and leaving with it. |
| `--system-prompt` and `--system-prompt-file` now combine, file text first (`Sr`, beside the `--system-prompt-file` read), where 2.1.269 rejected the pair | Nothing: `claude.sh` passes the file alone. Still replaces every section but the identity block; block 2 is now the file's text **plus the WebSearch `mode` paragraph** (279 tokens, was 114). |
| the environment block the env-context hook complements: `workingDirectory`, `shell` and `osVersion` became optional in the snapshot schema, and a `githubCli` bullet was added | Nothing; it closes the deferred decision of `notes/cc-2.1.269-prompt-rebase.md`: `render.py` was trimmed to cc's complement on 2026-09-13, and cc has since added no line the hook renders and dropped none it leans on (a snapshot missing those fields comes only from `launchOptions.toolsMachine()`, which nothing calls). |
| `heron_brook`, `brook_heron`, `delivering_work_max`, `overcorrection`; the legacy body `alan-default.md` copies | Nothing. The first four take their text from client data or GrowthBook keyed by model. The legacy body survives as six named blocks, byte-identical. |
