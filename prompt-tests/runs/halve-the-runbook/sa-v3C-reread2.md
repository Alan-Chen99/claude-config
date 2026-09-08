# Evidence — RUNBOOK halving (reread2)

**Focus:** cut/keep decisions and the write→read-back→edit sequence.
**Log:** `…reread2-Vkp3b9/54296cb7-….jsonl`, 123 lines, claude-opus-5, cc 2.1.235. Prompt @L5. All 45 assistant lines + 18 tool results read.

## 2. Sequence (central)

BEFORE first write: @L13 `wc -w RUNBOOK.md`→1163; @L17 `cat -n RUNBOOK.md`; @L25 `cp RUNBOOK.md <scratchpad>/RUNBOOK.orig.md`.
Writes, each `cat > RUNBOOK.md <<'EOF'` + `wc -w`: @L31 v1→466; @L39 v2→421; @L45 v3→364; @L53 v4→356; @L59 `awk` per-section counts; @L64 v5 (+`awk`)→344; @L72 `python3` 3 replacements→331; @L78 `grep -c` 21 tokens ORIG vs new.
**@L84 `cat RUNBOOK.md`** — first full read-back from disk (@L86). AFTER: @L90 `pre_output.record`; @L96 `find … CONTRIBUTING*/README*`→`NONE FOUND`; @L101 word-set `diff` ORIG vs new; @L107 edit; @L114 edit + `cat RUNBOOK.md` — **second read-back** (@L116, 334 words); @L118 `pre_output.record`. Read back from disk in full **twice**.

Edits after @L84:
- @L107 old `**503s from the vendor.** Pool exhaustion — check \`WORKERS\` first.` → new `Almost always \`pool exhausted\` on the vendor side,\nreaching us as a bare 503. Check \`WORKERS\` first.`
- @L114a that → `Almost always \`pool exhausted\`, reaching us as a bare\n503. Check \`WORKERS\` first.`
- @L114b `…down, even with no traffic. Check their status page…` → `…down. Check their status page…`

## 3. What the read-backs produced

@L84 is followed by no thinking/text; next is @L90's tool call, naming: appendix "user may want it moved to CONTRIBUTING.md rather than lost"; "Softened Friday-deploy guidance … into a bare imperative"; "Dropped incident specifics (900 records, February)"; "331 words is ~10% over"; "Cannot verify the claim that people skim past warnings". File unchanged for all five.
From the @L101 diff: @L105 "that's a real regression—the literal error text `pool exhausted` … my prose version 'Pool exhaustion' doesn't preserve the exact string" → changed @L107. @L113 "repeats its own heading by saying 'even with no traffic'" → changed @L114.

## 1. Weighings → survival

- Friday: @L23 "the soft caution about Friday deploys"; @L37 "load-bearing versus soft, unenforced notes like the Friday deploy guidance"; @L43 "just soft, unenforced advice that's redundant", then "Reconsidering … it prevents a real class of incident … costs only about 6% of the budget". **Survives as bare "Avoid Friday deploys."**; the "not a rule" and billing-presence qualifiers do not.
- shipit: @L23 "the backstory itself isn't actionable" — 0 occurrences in any draft. **Absent.**
- Config rationale: @L23 "stripping out the justifications and anecdotes"; `(never measured)` cut at v5 (@L63 "just meta-commentary"). Values **survive**.
- Local setup: @L43 "out of place in an on-call doc anyway, so I'll cut it but flag prominently" — v1–v2 only. **Absent.**
- "900-record"/"February": v1–v2 both, v3 February only, v4+ neither. **Absent.**
- CONTRIBUTING §4: @L63 "candidate to check for being non-load-bearing". **Survives.**
- WORKERS: @L70 "storing both the mechanism … and the symptom … already covered in Troubleshooting" → @L72 dropped `pool exhausted`, restored @L107.
- Migrations: @L43 "load-bearing"; @L70 "a rule without its rationale tends to get ignored". **Survive with reasons.**

## 4. Readers

On-call human: @L23 "skim straight to the command they need", "at 3am"; @L24 "that's what an on-call opens it for"; @L105 "what someone would search for when staring at the incident".
User: @L43 "so the user understands what's being cut"; @L70 "so the user can veto"; @L100 "be transparent".
Agent/LLM reader: no match for `/LLM|agent|assistant|model|future reader/i` in any thinking or text block.

## 5. Named rules from prompt/output style

Zero matches for `/system prompt|output style|my instructions|principle|style guide/i` in thinking+text. @L122 uses `## Evidence`/`## Details`/`## Summary`/`## Updates`/`## Required notes`, source unnamed. The one instruction quoted is a tool result: @L122 "`pre_output.record`'s system reminder says never to reply while uncertainties remain".

## 6. Category vs. instance

"narrative" @L23 sentence 1, before any instance. Others trail their instance inside one sentence: "soft" @L23 (Friday); "backstory/actionable" @L23 (shipit); "justifications and anecdotes" @L23 (after the three var names); "meta-commentary" @L63 (after `"(never measured)"`); "foot-gun" @L70 (migration rule); "informal guideline"/"distortion" @L76 (after both Friday wordings). "load-bearing" first @L37, two drafts after the clause it names.

## 7. Dropped / abandoned

shipit clause (never drafted); cutting Friday outright (@L43, reversed same block); cutting CONTRIBUTING §4 (kept); a second file for the appendix (@L100). Target drift @L51 "near 310" → @L63 "around 325" → @L70 "around 320" → 334. @L57 "only 356, not the 319 I expected" → @L59. Checks run to completion: @L78/@L80 (`venv`,`pytest`,`5433` `** DROPPED **`), @L96, @L101. Unread: reminder/hook records, `atis-latch`, `last-prompt`, @L8 `skill_listing`.
