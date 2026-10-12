# cc 2.1.235 → 2.1.269: `sys_prompt/` rebase, reviewed 2026-09-12 — no prompt text changed

> **Dated record.** Claude Code **2.1.269**; the procedure is `docs/prompt-rebase.md`.

Both prompt files reviewed against a 2.1.235 tree (`archive 56801e78 src`); keys diffed, then
every section present in both builds compared, and all thirteen pins resolved against both. The
release dropped `language`, `output_style` and `scratchpad` as sections and moved the environment
block into a `messages[]` attachment; it added `opus5_reduced_delegation` (a divergence row in
`docs/prompt-rebase.md`), `willow_tern` and `brook_heron`. Nothing was adopted, because nothing
this prompt borrows moved. Two findings outlive the entry: `output_style` (60edda3), and the
scratchpad bullet inside the environment attachment that left `agent-tools env-context`
duplicating it — closed by `notes/cc-2.1.289-prompt-rebase.md`.
