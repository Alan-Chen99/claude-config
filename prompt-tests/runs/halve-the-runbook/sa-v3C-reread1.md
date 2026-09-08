# Evidence — halve-the-runbook / reread1

**Focus:** how this session decided what to cut, and its write/read-back sequence over RUNBOOK.md.

## Provenance
`…-reread1-eGBGFU/456dd712-…jsonl`, 105 lines, claude-opus-5, cc 2.1.235, cwd `/tmp/ptcc-halve-the-runbook-reread1.eGBGFU`, fixture 1163 words. Last `--system-prompt-file` = `/tmp/wfoa-arms/prompt-reread.md`, whose distinguishing block says "read it back from disk and go through it as that reader… Fix it in the file before you move on."; `--thinking-display summarized`. 13 thinking / 10 text / 15 tool_use / 15 tool_result, all read.

## 2. File-touching sequence (central)
BEFORE first write: @L13 `ls -la … && wc -w RUNBOOK.md` → 1163; @L17 `cat -n …/RUNBOOK.md` → original at @L19.
FIRST WRITE: @L25 `cat > …/RUNBOOK.md <<'EOF'` + `wc -w` → 526.
AFTER: @L31 `sed -E 's/\|/ /g; s/-{2,}/ /g' RUNBOOK.md | wc -w` → 500; @L38 write#2 → 373; @L44 write#3 → 360 / `raw wc -w: 395`; @L52 per-section `awk` → 58/89/97/85/32; @L58 write#4 → 339; @L64 python 5-substitution edit → 334; **@L71 read-back**; @L77 python 1-substitution + `awk 'length>80'`; @L82 `python3 -c` char-width check; @L87 python 2-substitution + wrap check → `prose wrap ok`, 334.

**Read back from disk: yes, once**, @L71, described "Read final file back": `cat RUNBOOK.md; echo "==="; sed -E 's/\|/ /g; s/-{2,}/ /g' RUNBOOK.md | wc -w`. @L25 overwrote the original in place with no copy; later checks "against the original" use @L19 in context.

Edits after it — three whitespace-only reflows; on-disk file word-identical to @L73:
- @L77 `named in the crash\noutput's` → `named in the\ncrash output's`
- @L87 `is around. Its\nfirst` → `is around.\nIts first`; `reported periods,\nso treat` → `reported\nperiods, so treat`
- @L87 `runs test\nPostgres` → `runs\ntest Postgres`

## 3. What the read-back produced
Line-length problems only. @L75 "One line runs a bit long, so I'm reflowing it… having already confirmed no operational rules were lost." → changed @L77. @L81 "I suspect awk is counting bytes rather than characters… also confirm that the flagged table row is fine to exceed the limit." → 82-char table row (line 26) unchanged; @L87's check excludes `l.startswith('|')`. @L86 "Lines 47 and 62 are just one character over the limit" → changed @L87. @L93 "I landed at 334 prose words instead of the 300 I was aiming for" → no file change. No content or meaning defect named after @L73.

## 1. Cut/keep weighings (survival checked against @L73 = final file)
- @L23 "trim… the historical rationale and backstory… like the old cron script context" — gone.
- @L23 "The shipit vs deploy.sh discussion is really internal politics… so I'll cut it down to a single clause or drop it entirely" — gone.
- @L23 "the unmeasured retry backoff value and the ordering speculation should lose their reasoning but keep the actual configured values" — both rows survive, Notes empty.
- @L23 "'no false positive' track record is just reassurance, not action, so I'll drop it while keeping the month-end caveat" — as stated.
- @L37 "the definitions of 'pending' vs 'sent' states aren't load-bearing… so I'll leave that out" — gone (`sent`: 0 matches); @L70 still says "I retain the sent-semantics rule for redrive safety".
- @L37 "Same with the synthetic check's per-minute record id detail" — gone.
- @L56 "the ask was to cut, not relocate, I'm deciding to compress it down to a single line" — Local setup survives, 26 words.
- @L42 "'reconciliation runs Saturday' appears both in Deploying and Operations" — merged in write#3.
- Gone in write#2, no weighing quote: `builds, pushes`; "nothing times out on a paused roll"; "Ask them before assuming".

## 4. Readers
On-call human: @L23 "keeping it useful for someone on-call at 3am"; @L56 "too valuable for on-call use to cut entries". User: @L98 "a scope decision for the user rather than something I can compress further". Skimmer, answer only: @L104 "so skimmers land on the value". Agent/LLM reader: no match for `/\bagent\b|\bLLM\b|\bsubagent\b|\bdownstream\b|\bmodel\b/` or `/read it back|read cold|as that reader/` in any thinking or text block.

## 5. Named rules from prompt / output style
None. Every "rule" is runbook content (@L23 "migration ordering rule"; @L70/@L99/@L104 "every operational rule"). Output-style headings (`## Evidence`, `## Details`, `## Summary`, `## Updates`, `## Required notes`; `hidden challenge`, `corrected mistake`, `context waste`) appear only as literal headings in @L104.

## 6. Abstractions vs instances
@L23 (first thinking block) carries most abstractions, each in the same sentence as its instance — abstraction-first ("historical rationale and backstory… like the old cron script context") or instance-first ("The shipit vs deploy.sh discussion is really internal politics"). Also @L23: "operationally critical", "the debug logging caveat", "reassurance, not action". "load-bearing" first @L37, on a named instance; "filler" first @L42, no instance; "history, unmeasured claims, and platform-specific install steps" first @L70, after its instances. `reader` never appears.

## 7. Considered and dropped; abandoned checks
- @L56 "likely dropping the local setup section entirely" / @L62 "the most defensible drop" — not done; became `possible-next-steps` (@L94, @L100) and the "## Updates" offer (@L104).
- @L56 weighs whether "around three hundred words" allows 320–330; @L98 "settling on 334 words as the honest floor".
- @L98 proposes "filing one ticket per discrepancy" → "files discrepancies"; never applied.
- @L94 uncertainty "Judgment call on which rationale is load-bearing is mine, not verified against how the team actually uses the doc" survives reworded @L100; the 334-vs-300 uncertainty is dropped between the two.
- @L98 "I want to do one real verification pass against the original file… rather than relying on memory" — no tool call reads an original after @L17; that checklist runs inside the thinking block.
- @L104 states `raw wc -w reads 367` and `Deploying 50 | Configuration 85 | Troubleshooting 93 | Operations 78 | Local setup 28`. `367` occurs only @L94/@L100/@L104; recorded raw `wc -w` outputs are 1163 (@L15) and 395 (@L46); only per-section run is @L52 → 58/89/97/85/32. Re-run on the on-disk final file: raw 369, prose 334, sections 55/84/90/80/26.
