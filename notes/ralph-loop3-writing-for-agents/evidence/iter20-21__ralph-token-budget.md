# Evidence: `.ralph/agent/*` 6000-token size rule in iterations 20 and 21

**Focus:** everything in these two sessions that touches the `.ralph/agent/*` 6000-token size rule — how the agent measured it, read it, worked within it, what text it removed or moved elsewhere because of it, and what that removal cost or gained.

## Provenance

- Session 1: `/root/.claude/projects/-root-claude-config-work/122b4216-f937-4a0a-8b04-966f6d2c0b78.jsonl` — iteration 20, 510 lines, model `claude-opus-5`, cc version 2.1.269, cwd `/root/claude-config-work` (git worktree, branch `writing-for-agents2`).
- Session 2: `/root/.claude/projects/-root-claude-config-work/2328f962-1046-4885-a410-3fd8ec03c1d3.jsonl` — iteration 21, 406 lines, same model/version/cwd/branch.
- Both sessions: single user turn `"Please read and execute the task in /tmp/<tmpfile>"`; the task file is a Ralph-loop wrapper that injects `<ready-tasks>`, `<scratchpad path=".ralph/agent/scratchpad.md">` (the live file's content at session start), `<ralph-tools-memories-skill>`, and the loop's `PROMPT.md` body, ending in a "no fixed reply format" self-report via `agent-tools pre_output.record` plus a final free-text turn.
- Agent identity: no subagents dispatched for the budget work itself in either session (iter21 dispatches one `general-purpose` blind-reader subagent for an unrelated measurement).
- Extraction commands used: `agent-tools cc-pretty <path> --skeleton`; targeted `sed -n '<n>p' <file> | jq -r '.message.content[...]'` for line-level reads; a small Python script iterating the JSONL for keyword matches (`6000`, `ceiling`, `budget`, `count-tokens`, `relocation is growth`, `cut before add`, `5943`) across `thinking`/`text`/`input`/`content` fields.
- Extractor context: dispatched by a parent agent, `mode: evidence`, focus as stated in the brief (this file's title line).

## The rule, as the loop states it

Injected verbatim in the task file of **both** sessions (iter20 `@L57`, iter21 `@L45`), inside the loop's own bullet list of hard rules:

> `.ralph/agent/*` ≤ 6000 tokens by `agent-tools count-tokens`. relocation is growth. Cut before add.

No other occurrence of the phrases "relocation is growth" or "cut before add" appears in either transcript (checked by literal grep over the full JSONL); the agent's own reasoning never repeats this wording, it reasons in its own terms ("over budget", "under the ceiling", "cutting it close").

The scratchpad's own **Standing `(contract)`** section (carried into both sessions as part of the injected `<scratchpad>`) restates the operational form, credited to iteration 19:

> **The round ends under the user's `.ralph/agent/*` ceiling, with the number in its last commit message** — not in a file here, where writing it changes it. `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` < 6000. It sat over for two rounds because no line named a command. *(19)*

This is the exact command both sessions use throughout: `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` (piped through stdin, not `--file` on the glob directly). The `cat .ralph/agent/*` glob expands to every file in the directory as it exists on disk — confirmed by the `ls -la .ralph/agent/` run at iter20 `@L65`, which lists at session start: `decisions.md` (3122 B), `memories.md` (8714 B), `memories.md.lock` (0 B), `scratchpad.md` (11050 B), `summary.md` (93 B), `tasks.jsonl` (455 B), `tasks.jsonl.lock` (0 B). Neither session `cat`s or edits `summary.md` or `tasks.jsonl` individually at any point (checked by literal search for `summary.md`/`tasks.jsonl` outside the `ls -la` listing and the PROMPT.md's own generic reference to those paths) — both files are folded into the count only via the `cat .ralph/agent/*` glob, not read or acted on as content. The rule's own wording ("`.ralph/agent/*`") matches the glob used; the measurement is a sum over every file in the directory, not scratchpad.md alone or any single file.

## Iteration 19 background carried into iteration 20 (for context; not newly measured in iter20)

The scratchpad's "History" section, read into iteration 20's context at session start (`@L46`, part of the injected task file, second chunk read via `sed -n '120,330p' /tmp/<tmpfile>`), records iteration 19's own critique of the two rounds before it:

> **C1 (workflow — a hard user budget unmeasured and breached for two rounds).** `.ralph/agent/*` ≤ 6000 tokens is a user rule and nothing here ever ran the command that checks it: 5926 at 16's end, 6118 at 17's, 6122 at 18's. Two rounds grew the directory past the ceiling while writing about unbounded documentation. Cut here, and the check is now a `(contract)` line with the command in it — a rule with no command is what let two rounds miss it.

So the state entering iteration 20 is: iteration 19 introduced the standing-contract command and (per its own commit message, seen in `git log`) brought the directory back under the ceiling.

---

## Iteration 20 (`122b4216…`)

### Count-tokens calls, in order

| # | Line (tool_use → result) | Command | Result | Context |
|---|---|---|---|---|
| 1 | `@L181`→`@L183` | `python3 - <<'PY' ... PY` (rewrites scratchpad, appending the iteration-20 critique C1–C3) `\ncat .ralph/agent/* 2>/dev/null \| agent-tools count-tokens --file /dev/stdin` | `ok\n5485` | Mid-session, right after writing the round's critique into scratchpad.md; not part of end-of-round housekeeping. |
| 2 | `@L462`→`@L464` | `cat .ralph/agent/* 2>/dev/null \| agent-tools count-tokens --file /dev/stdin` (description: "Check budget") | `6088` | **Over the 6000 ceiling.** Taken right after adding 3 new memories (mem-1790070620-905c, mem-1790070627-b0f9, mem-1790070627-cbc4) at `@L454`/`@L458`. |
| 3 | `@L467`→`@L472` | `for m in mem-1790067347-5f25 mem-1790051243-3cef mem-1790067347-74ad mem-1790069038-9779 mem-1790067347-89d7 mem-1790065267-1153; do ralph tools memory delete $m 2>&1 \| tail -1; done; cat .ralph/agent/* \| agent-tools count-tokens --file /dev/stdin` | 6 "Memory deleted: …" lines, then `5008` | Six memories deleted in one call (see list below); brings the count back under 6000. |
| 4 | `@L474`→`@L476` | `python3 - <<'PY' ... PY` (rewrites decisions.md: compresses the "Closed." header paragraph, appends new `DEC-029`) `\ncat .ralph/agent/* \| agent-tools count-tokens --file /dev/stdin` | `ok\n4985` | Net decrease despite adding DEC-029, because the header paragraph was compressed in the same edit. |
| 5 | `@L481`→`@L483` | `cat >> .ralph/agent/scratchpad.md <<'EOF' ... EOF\ncat .ralph/agent/* \| agent-tools count-tokens --file /dev/stdin` | `5540` | Appends "### The round's work and result" + "`(instruction)` for iteration 21" to scratchpad. |
| 6 | `@L489`→`@L491` | `python3 - <<'PY' ... PY` (rewrites the iteration-20 header line to record the closing commit hash) `\ncat .ralph/agent/* \| agent-tools count-tokens --file /dev/stdin && git add -A && git commit -q -F - <<'EOF' iter20: commit range cf8f2dac -> end of round\n\n.ralph/agent/* is 5540 tokens against the user's 6000 ceiling.\n...EOF ...` | `5550` | Final count for the round (the commit message quotes the *prior* count, 5540, taken before this last header edit added a few tokens). |

Final self-reported "## Evidence" block (`@L508`, the session's closing free-text turn) restates the last figure with the ceiling annotated inline:
```
$ cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin
5550          # ceiling 6000
```

### Reasoning around the ceiling

- `@L453` (thinking, right before the memory-writing that pushed the count to 6088): "Time to wrap up bookkeeping — updating decisions.md, adding memories, prepping the scratchpad for the next run, and checking the budget before emitting output. … With `.ralph` currently at 5485 tokens, I need to stay economical: two memories plus trimmed decisions should keep me under the 6000 limit."
- `@L466` (thinking, after the 6088 result, before the delete command): "I'm over budget and need to free up space, so I'll cut older memories whose claims are now superseded—starting with the one about claim-handling readings saturating on handover gaps, since the newer salience memory already covers that. The `mem-1790051243-3cef` memory … is now contradicted by this round's finding … I'll keep the downstream-reader-instability memory and the round 19 findings on the shipped bullet since those still hold up. I'm going through the remaining candidates: keep the blind-read methodology note and the saturated-baseline memory, but delete the duplicate one since its rule is already captured in the standing contract; keep the shipped-line prioritization rule and the tooling-fix memory; and delete the diff-leak memory since that guidance now lives in the skill itself. Two more duplicates stand out — the probe-directory naming issue is already covered by the skill, and the 'omit by default' claim already lives in sys_prompt/CLAUDE.md — so both should go…"
- `@L172` (thinking, earlier in the session, about the *scratchpad file specifically*, before the count-tokens machinery ran): "The scratchpad budget is nearly maxed out at 5995 of 6000 tokens, so I'll need to trim iteration 19's section down to make room for the new iteration-20 critique." (This is a mental estimate stated before the compression edit at `@L181`, not a command-measured figure — no count-tokens call at exactly 5995 appears in the transcript.)

### The six memories deleted, and the stated reason for each

Quoted from the pre-deletion `cat .ralph/agent/decisions.md; cat .ralph/agent/memories.md` at `@L128` (all six IDs match the delete list at `@L467` exactly):

1. `mem-1790067347-5f25` (tag: pattern) — *"A claim-handling reading saturates when the fixture's handover STATES the gap. Asked to write a rules file from five statements of differing warrant, all four arms recorded the one 'I don't know why' as unknown rather than inventing a reason… A fixture that can fire a claim-handling line has to make one UNFLAGGED external premise load-bearing."* — deletion reason per `@L466` thinking: superseded by the newer salience memory from this round.
2. `mem-1790051243-3cef` (pattern) — *"Agents discharge an unverified claim into the CONVERSATION and leave it standing in the FILE… none names the artifact, which is the channel that outlives the session. This is the mechanism behind doc errors that need human intervention to remove."* — reason: "now contradicted by this round's finding that the baseline recorded the claim as open rather than asserting it flatly."
3. `mem-1790067347-74ad` (pattern) — *"A null from a saturated baseline bounds the FIXTURE, not the clause… Check before writing the conclusion: did every arm, including the untreated one, already do the thing?"* — reason: "duplicate … already captured in the standing contract."
4. `mem-1790069038-9779` (fix) — *"A diff staged for a blind reader leaks the case name: 'diff -u' writes the fixture's absolute path into its own header… fix is 'diff -u --label before/<f> --label after/<f>'."* — reason: "guidance now lives in the skill itself."
5. `mem-1790067347-89d7` (fix) — *"A probe directory sharing a word with its own fixture is found by the tested agent's ordinary search…"* — reason: "already covered by the skill."
6. `mem-1790065267-1153` (decision) — *"Omit by default … is deleted from sys_prompt/alan-default-next.md: run on a compression task against an arm without it, the arm carrying it made an unrequested claim of its own…"* — reason: "'omit by default' claim already lives in sys_prompt/CLAUDE.md."

Memories explicitly kept per `@L466`: the downstream-reader-instability memory (`mem-1790052470-9c1e`), "round 19 findings on the shipped bullet" (matches `mem-1790069030-eaf9` / `mem-1790069038-81d9`), "the blind-read methodology note" (`mem-1790065267-fe47`), "the saturated-baseline memory" (kept one — `mem-1790067347-74ad` was the *deleted* duplicate per the reasoning, so the surviving saturated-baseline-shaped memory is `mem-1790052470-9c1e`), "the shipped-line prioritization rule" (`mem-1790057525-9dcd`), and "the tooling-fix memory" (`mem-1790061592-858f`, about session-analysis dispatch failures).

Commit message at `@L485`/`@L487` (`f66c6e5c`) states the same six deletions and totals:

> iter20: scratchpad, decisions, memories, and the budget back under its ceiling
>
> Six memories deleted: two superseded by this round's measurement (the stated-gap reading, and the claim that agents leave the file asserting flatly -- the baseline did the opposite here), one duplicating a standing contract line, three duplicating rules that now live in the prompt-tests skill or in sys_prompt/CLAUDE.md. 6088 -> 5540 tokens.

### Content moved to another destination instead of staying in `.ralph/agent/*`

- The commit message and the `@L466` reasoning both frame three of the six deletions as **relocations**, not pure deletions: their content is stated to already live in `.claude/skills/prompt-tests/SKILL.md` (the diff-leak fix, the probe-directory-naming fix) or in `sys_prompt/CLAUDE.md` (the "Omit by default" decision record). These moves happened in **prior** rounds (the memories predate iteration 20 — their IDs carry earlier timestamps, e.g. `mem-1790069038-9779` — created 2026-09-22 per their own `created:` tag, same day but earlier in the loop); iteration 20's action is to delete the now-duplicate `.ralph/agent/memories.md` copy after confirming the durable copy already exists elsewhere, per the compression rule quoted in the injected scratchpad ("(3) a duplicate of executable code/durable text — replace with its name"). The session does not narrate these three as "relocation is growth" in those words.
- The other three deletions (items 1, 2, 3 above) are framed as content **no longer true** ("superseded", "contradicted") rather than relocated — nothing else replaces them.
- Separately, iteration 20's DEC-029 (`@L474`) is new content added *to* `.ralph/agent/decisions.md`, not moved out of it; the net token change from that edit was still negative (5008→4985) because the same edit compressed the "Closed. DEC-001–027…" header paragraph in the same script.

### Final self-report language (iter20 closing turn, `@L508`)

Under "## Required notes": *"**unexpected change**: six memories deleted rather than kept — two are contradicted by this round's measurement, not merely superseded."* No other required-notes item in iter20's closing turn references the token ceiling.

### Cost / placement in session

- Count-tokens calls: 6 total (`@L181`, `@L462`, `@L467`, `@L474`, `@L481`, `@L489`), of which one (`@L181`) sits mid-session attached to critique-writing and five sit in the final housekeeping block.
- The end-of-round housekeeping block (bookkeeping thinking at `@L453` through the `ralph emit` at `@L497`) spans JSONL lines ~453–499 of 510 total (≈9% of the session's line count, positioned at the very end).
- Bash tool calls in that housekeeping block: memory-add ×2 calls (`@L454`, `@L458`), count-tokens-only check (`@L462`), memory-delete+count-tokens (`@L467`), decisions.md edit+count-tokens (`@L474`), scratchpad append+count-tokens (`@L481`), commit (`@L485`), commit-range script+count-tokens (`@L489`), `ralph emit` (`@L497`) — 9 Bash calls.

---

## Iteration 21 (`2328f962…`)

### Count-tokens calls, in order

| # | Line (tool_use → result) | Command | Result | Context |
|---|---|---|---|---|
| 1 | `@L51`→`@L53` | `git log --oneline -25 && echo "--- status" && git status --short && echo "--- ralph" && ls .ralph/agent/ && cat .ralph/agent/* \| agent-tools count-tokens --file /dev/stdin` | (git log, `ls`: `decisions.md memories.md memories.md.lock scratchpad.md summary.md tasks.jsonl tasks.jsonl.lock`, then) `5550` | Session-opening survey; matches iteration 20's closing figure exactly. |
| 2 | `@L349`→`@L351` | `ralph tools memory delete mem-1790070620-905c && ralph tools memory delete mem-1790057525-9dcd && ralph tools memory add "…" -t pattern … && ralph tools memory add "…" -t decision … && cat .ralph/agent/* \| agent-tools count-tokens --file /dev/stdin` | 2 deletes + 2 "Memory stored" lines, then `5015` | Net decrease despite adding 2 memories, because 2 were deleted in the same call. |
| 3 | `@L353`→`@L355` | `cat >> .ralph/agent/decisions.md <<'MD' ## DEC-016 — the ninth claim-handling wording is not written this round … MD` (no explicit pipe shown in this call, but see below) | `5576` | Appends DEC-016 (full decision record on why no new claim-handling wording ships this round). |
| 4 | `@L357`→`@L362` | `cat >> .ralph/agent/scratchpad.md <<'MD' ### The round's work and result … MD\ncat .ralph/agent/* \| agent-tools count-tokens --file /dev/stdin` | `6306` | **Over the 6000 ceiling** — the largest overshoot recorded in either session (306 over). |
| 5 | `@L365`→`@L367` | `python3 - <<'PY' ... PY` (deletes the "probe's own directory…" contract line — now fully covered by the skill — and the "clause no fixture can exercise" line; rewrites the blind-reader and instruction-asserting contract lines to shorter forms) `\ncat .ralph/agent/* \| agent-tools count-tokens --file /dev/stdin` | `6072` | First cut; still over. |
| 6 | `@L369`→`@L374` | `python3 - <<'PY' ... PY` (further compresses "The compression rule" and "A line that names a consideration…" durable-method entries) `\ncat .ralph/agent/* \| agent-tools count-tokens --file /dev/stdin` | `5996` | Second cut; back under 6000. |
| 7 | `@L377`→`@L379` | `python3 - <<'PY' ... PY` (trims the "History — rounds 1–20" paragraph, dropping "the case corpus bound to the prompt by one grep, eleven of fifteen cases deleted (15)" clause and shortening the rest) `\ncat .ralph/agent/* \| agent-tools count-tokens --file /dev/stdin` | `5935` | Third cut, described as leaving headroom for the closing header edit. |
| 8 | `@L385`→`@L387` | `sed -i 's|^## Iteration 21 — \`a9fc0fc6\` → end of round$|## Iteration 21 — \`a9fc0fc6\` → \`0a2ade7e\` + this commit|' .ralph/agent/scratchpad.md && grep -n "^## Iteration 21" .ralph/agent/scratchpad.md && T=$(cat .ralph/agent/* \| agent-tools count-tokens --file /dev/stdin) && echo "budget: $T" && git add -A && git commit -q -m "iter21: commit range a9fc0fc6 -> end of round\n\n.ralph/agent/* at $T of 6000 tokens by\ncat .ralph/agent/* \| agent-tools count-tokens --file /dev/stdin\n\nClaude-Session: 2328f962…"` | `budget: 5943` | Final count, captured into a shell variable and interpolated directly into the commit message (unlike iter20, which hand-typed the number into its commit messages). |

The final self-reported "## Evidence" block (`@L404`) repeats the same figure:
```
$ cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin
5943
```

### Reasoning around the ceiling

- `@L336` (thinking, before the memory-edit sequence): "I need to pull together the scratchpad results with the instructions, check decisions.md and memories, then verify budget before doing the final commit and emitting the range."
- `@L348` (thinking, before call #2): "Memory 905c needs updating since this round refuted its claim that no wording can make a passing sentence salient, so I should replace it accordingly. Memory 9dcd also needs amending to scope the shipped-line-outranks-candidate claim to the block, per my C1 finding. I'm tracking a budget of roughly 5055 remaining." (This estimate does not match any single count-tokens result recorded — the nearest actual measurements bracketing it are 5550 at session start and 5015 after call #2.)
- `@L364` (thinking, immediately after the 6306 over-ceiling result): "I'm over the ceiling and need to trim something. Checking whether the scratchpad's contract section duplicates what's already pointed to in the prompt-tests skill file, since that redundancy looks like the cheapest thing to cut. The probe-deletion rule in the contract is fully covered by the skill file, so I can cut that line entirely per the contract's own note about operational rules living there. I can also merge the 'clause no fixture can exercise' item into my new amendment, and trim the History paragraph a bit — together that should get me down about 310 tokens."
- `@L376` (thinking, after the second cut brought the count to 5996, before the third cut): "I'm cutting it close on the token budget, so I need to trim the history paragraph a bit more to leave room for the updated iteration header and commit range line."

### What was cut in the three trimming passes (verbatim, from the diff text embedded in the Python scripts)

Cut #1 (`@L365`, contributing to 6306→6072):
- Deleted entirely: `> **A probe's own directory is deleted by the round that wrote it**, in the commit that puts the claim into \`sys_prompt/CLAUDE.md\`. Reasoning and the two records that forced it: the prompt-tests skill. *(19)*` — reason stated in the script's own comment: "covered verbatim by `.claude/skills/prompt-tests/SKILL.md`, which the contract already defers to."
- Deleted entirely: `**A clause no fixture can exercise is a deletion candidate with an outstanding test, not an open question.** *(13)*` — reason: "subsumed by this round's contract amendment."
- Shortened (not deleted): the "A round's decisive reading is made by a reader that is not the round" contract bullet, dropping its worked example (iteration 17's read).
- Shortened (not deleted): the "An `(instruction)` asserting that work is undone…" contract bullet, dropping its worked example (iteration 12).

Cut #2 (`@L369`, contributing to 6072→5996): compresses "The compression rule" bullet (removes the numbered-list formatting and restates the four classes more tersely) and shortens "A line that names a consideration does not deliver the conclusion it argues for" (drops "*(iter 13)*" citation and some wording).

Cut #3 (`@L377`, contributing to 5996→5935): trims the "History — rounds 1–20" paragraph, replacing:
> "Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — the durable home, and the file to read before touching the block. Everything else is in the commit messages. Shipped: `Say what ends it` (9, isolated 19). The case corpus is bound to the prompt by one grep; eleven of fifteen cases deleted (15). Deleted: `Omit by default` (13, 17), `Claim less` (4, 14). Eight candidate wordings failed (3–8, 12, 14, 16, 18, 20), the last three all claim-handling. Round 10 fixed a nine-round harness contamination and voided every arm stored before 2026-09-22. Every sentence still in the block has now been measured alone: the preamble (18) and `Say what ends it` (19). 20 built the fixture the claim-handling condition named and found the baseline saturated on it; what no arm marks is the premise reached for *while writing a supporting sentence*, asserted flat everywhere."

with a version that reorders and drops the "case corpus bound to the prompt by one grep; eleven of fifteen cases deleted" clause and the "Round 10 fixed a nine-round harness contamination…voided every arm" clause's placement, condensing "Every sentence still in the block…" into "Every sentence still in the block has been measured alone (18, 19)."

### The two memories deleted at the start of the housekeeping sequence, and why

From `@L349`:
1. `mem-1790070620-905c` (this round's own predecessor memory, added by iteration 20) — reason (`@L348` thinking): "needs updating since this round refuted its claim that no wording can make a passing sentence salient." Replaced by a new memory (`mem-1790071899-5e6c`) stating the refutation.
2. `mem-1790057525-9dcd` (iteration-20-era decision memory, "A shipped prompt line with a named, unmeasured negative effect outranks any new candidate line as a round's milestone…") — reason: "needs amending to scope the shipped-line-outranks-candidate claim to the block, per my C1 finding." Replaced by a new memory (`mem-1790071899-7413`) adding the scope qualifier ("but only inside the objective's scope").

Both deletions are explicit **replacements** (old claim wrong/incomplete → new claim in its place), not relocations to another file and not pure space-saving cuts — they are the trigger for calls #2 in the table, which nets to a decrease only because the two adds are smaller/net-negative combined with the two deletes.

### Content moved to another destination instead of staying in `.ralph/agent/*`

- DEC-016 (`@L353`) and the corresponding `sys_prompt/CLAUDE.md` paragraph replacement (commits `15d439ee`, `5dff4c0f` per the scratchpad text) move the round's semantic finding about claim-handling into `sys_prompt/CLAUDE.md` as the durable location, per the loop's own rule ("Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md`") — this is the loop's designed division of labor, not a budget-driven relocation.
- The self-report's "## Required notes" section states explicitly (see next section) that some of what was cut from the scratchpad in the trimming passes was cut *because* it duplicated the `prompt-tests` skill file, i.e., text considered as already relocated rather than newly moved by this round.

### Final self-report language on the ceiling (iter21 closing turn, `@L404`)

Under "## Required notes": *"**instruction issue**: the `.ralph/agent/*` ceiling forced cutting contract lines that the `prompt-tests` skill already states verbatim — the contract's own deferral line says those are not restated there, so the duplication was already out of policy."*

The `ralph emit work.iteration` call (`@L396`) ends its payload with: *"Nothing shipped to the prompt; paragraph replaced 808->791 chars. Probe promoted to prompt-tests/general/maintainer-briefing rather than deleted -- first override of the deletion rule … .ralph at 5943 of 6000."*

### Cost / placement in session

- Count-tokens calls: 8 total (`@L51`, `@L349`, `@L353`, `@L357`, `@L365`, `@L369`, `@L377`, `@L385`), spanning JSONL lines 51–387 of 406 total — i.e., a first check near the very start of the session and the remaining seven concentrated in the closing housekeeping block (lines ~336–387, ≈13% of the session's line count).
- Unlike iteration 20 (one overshoot, one correction, done), iteration 21 overshot once (6306) and needed **three** successive trimming edits (6072 → 5996 → 5935) before the ceiling was satisfied, plus one more edit for the closing commit-range bookkeeping (5943 final).
- Bash tool calls in the closing housekeeping block: memory delete+add+count (`@L349`), decisions.md append (`@L353`), scratchpad append+count (`@L357`), three trim-and-recount scripts (`@L365`, `@L369`, `@L377`), commit-range script+count (`@L385`), `ralph emit` (`@L396`) — 8 Bash calls (plus the session-opening survey at `@L51` = 9 total commands touching `.ralph/agent/*` or its count across the session).

---

## Cross-iteration notes

- Both sessions read the rule from the same injected PROMPT.md text and the same scratchpad-carried `(contract)` line; neither session's own reasoning ever recites "relocation is growth" or "cut before add" as phrases — both talk in terms of "over budget," "over the ceiling," "under the ceiling," "cutting it close."
- Iteration 20 ends at 5550 tokens (last measured value; the commit message text quotes 5540, the value from one edit earlier). Iteration 21's opening measurement reads exactly 5550, confirming the two sessions agree on the file state at the handoff point.
- In both sessions, the deletion/cut decisions are justified against three categories stated by the agent: (a) superseded/contradicted by this round's own new finding, (b) duplicated in a durable file (`sys_prompt/CLAUDE.md` or `.claude/skills/prompt-tests/SKILL.md`), or (c) duplicated within `.ralph/agent/*` itself (the standing-contract line covering a memory's claim). No instance in either session states a memory or scratchpad passage was deleted with no replacement and no durable home identified elsewhere — every cut is paired with a stated reason of one of these three kinds.
- Neither session reads or edits `tasks.jsonl` or `summary.md` as content; both are counted only via the `cat .ralph/agent/*` glob used for the ceiling check.
