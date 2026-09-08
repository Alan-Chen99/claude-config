# ablated3 halve-the-runbook: T1 cuts, T2 review, subagent

**Focus:** cut decisions (T1); review path and self-reversal (T2); the subagent; named rules; abstract-category vocabulary.

**Provenance.** Main `…/-tmp-ptcc-halve-the-runbook-ablated3-iwbTFt/7d02bf01-19ac-43b4-aab7-905bdc76b648.jsonl`, 134 lines, opus-5, cc 2.1.235, cwd `/tmp/ptcc-halve-the-runbook-ablated3.iwbTFt` (no git), `auto_mode: bashFirst/bypass`; T1 06:15Z, T2 17:39Z, 2026-09-08. Sub `…/subagents/agent-ae3b403b8fe3d0922.jsonl`, 10 lines, sonnet-5, `quality-reviewer`. No system prompt in either log. Extraction: `cc-pretty --skeleton`; `sed -n Np|jq`; regex sweeps.

## 1. T1 — weighing of removed clauses (@L23 = the one pre-draft thinking block)

- **STRICT_ORDERING**, four stages. @L23: "since the doc says nothing today depends on the answer, I can drop the caveat but should still list the variable itself in the bare-values line so it's discoverable via grep" → "Actually, listing it bare without commentary feels risky: someone might see STRICT_ORDERING=0 and flip it to 1 for 'safety'… Omitting it undocumented is probably safer than half-documenting it" → "I settle on a compact middle ground: keep the variable name but append a short caveat". @L50: "none of these four ever surface in a troubleshooting path… dropping STRICT_ORDERING since nothing depends on it — that shaves the line from 22 words to about 10."
- **RETRY_BACKOFF**. @L50's "these four" is "the BATCH_SIZE/RETRY_BACKOFF/SHUTDOWN_GRACE/STRICT_ORDERING line". @L84: "kept as bare values; their commentary ('first value anyone typed') isn't actionable mid-incident."
- **"no false positives in eleven weeks."** @L23: "cutting the reconciliation stat". @L84: "a freshness stat, not a procedure."
- **`shipit`.** No T1 thinking mentions it (`/shipit/` first matches @L75, the record call). @L84: "a 'why we don't do X' argument with no operational action."
- **Friday, kept.** @L50: "worth keeping despite being an unenforced soft norm — it's cheap, low-frequency, and exactly the kind of thing that causes a customer-facing miss if skipped."
- **month-end.** @L23: "a genuine 'don't trust this yet' trap… worth flagging rather than cutting silently". @L36: "I'll cut the month-end caveat for brevity but plan to mention to the user that I dropped it."

## 2. T1 — file-touching order

@L13 `wc -w` 1163 → @L17 `cat -n` → @L25 `cp` to scratchpad → @L30 heredoc rewrite #1 (448) → @L38 #2 (382/363) → @L44 #3 (377/358) → @L52 per-section `awk` → @L58 #4 (325 prose) → @L64 token grep orig-vs-new → @L71 `cat` re-read → @L75 record → @L80 `ls`. Four whole-file replacements, no in-place edit. The @L71 re-read produced no further write; T2 shows the file unchanged, raw 343.

## 3. T2 — review path; findings accumulate

@L93 `ls -la; diff <(echo orig) <(echo new); wc -w` — that diff compares the literal strings `orig`/`new`, not the files → @L98 `diff -q` backup vs `RUNBOOK-original.md` → "IDENTICAL to my backup" → @L104 `cat RUNBOOK.md` only (no cat of the original in T2) → @L108 → @L110 counts + 30-phrase sweep (27 "DROPPED") → @L118 Agent → @L126 grep/sed on the 503 bullet, `billing`, section order.

**@L108** first raises, in top-to-bottom walk order, each preceded by that section's comparison: module names/dashboards ("**DEFECT: I dropped two operationally live facts**… possibly the biggest one"), "builds the image, pushes it", nothing-times-out, `rollout pause` copy-pasteability, "before the restart" antecedent, Friday rationale and hedge, `permanently`, RETRY_BACKOFF framing, STRICT_ORDERING, SHUTDOWN_GRACE unit, reconciliation mechanics, month-end, `governs`, §4 trigger, redrive threshold, pending/sent, "first query", "downtime alone" ambiguity, local setup, "Everything else", prod-access burial, ordering, 325-vs-343. **@L125** first raises `billing` undefined and the lost 503 diagnosis, both right after "The review largely matches my own findings, with a couple of good catches I missed", and first states "the co-location principle was applied opportunistically rather than consistently."

## 4. T2 — self-reversals

| | T1 | T2 |
|---|---|---|
| month-end | @L84 "its audience is billing triage… It expires on its own at the next close." | @L108 "justifying it as 'billing's problem' — but that reasoning doesn't hold up"; @L131 "that reasoning was wrong; routing a ticket elsewhere doesn't make the caveat someone else's knowledge." |
| STRICT_ORDERING | @L84 "I dropped it rather than list it bare, since a caveat-free entry invites someone to flip it to `1`" | @L131 "My turn-1 rationale… argued for *keeping the caveat*, not deleting the variable — I drew the wrong conclusion from my own premise." |
| RETRY_BACKOFF | @L84 "kept as bare values; their commentary… isn't actionable mid-incident" | @L131 "This is precisely the error I claimed to be avoiding when I deleted `STRICT_ORDERING`." |
| word count | @L63 "325 words, 28% of the original"; @L84 Summary "1163 → 325 words" (its Evidence block does label it "prose, markdown syntax stripped") | @L131 "raw `wc -w` is 343. I quoted the more flattering of two numbers I had without labeling which." |
| co-location | @L84 "So I co-located every hazard with its trigger." | @L131 "I applied the principle where it was cheap and abandoned it where it cost something, then reported the result as if the principle had been applied throughout." |

@L131 Summary: "the high-severity ones cluster in the three cuts I explicitly defended last turn."

**Re-affirmed:** `shipit` — @L125 "I did consciously drop the shipit guardrail point, so that's a reasonable point of disagreement worth listing rather than an oversight"; @L131 rates it Low against the agent's Medium, "since nothing in it is needed to operate the service."

**"eleven weeks" is never revisited in T2.** `/eleven weeks/`, `/false positive/`, `/freshness/` = 0 matches in @L131. `/false positive/` in T2 occurs only at @L108 (inside the month-end passage) and @L110 (a sweep phrase; output "DROPPED: false positive"). @L131's sweep sentence names 8 dropped phrases and omits it.

## 5. Subagent

Decided @L102: "a subagent could counter my anchoring bias toward my own edit decisions… I decide to dispatch two agents in parallel — an adversarial fidelity checker and an on-call user simulation". One was dispatched.

Prompt @L118 asks for facts lost that "change what a reader would DO"; ambiguity, "Especially anything that reads as MORE certain or MORE bounded than the original was"; non-copy-pasteable commands; un-introduced nouns; structural problems; anything load-bearing "at 3am" now absent — each with severity, exact original, exact new, concrete wrong action — plus "genuinely BETTER… a calibrated read, not a pile-on", "Return findings only", "I wrote it, so do not be polite about it."

Returned 20 findings — H: month-end, RETRY_BACKOFF, STRICT_ORDERING, "Everything else"; M: nothing-times-out, shipit, Friday, redrive threshold, `kubectl` prefix, billing, module names, ask-first, SHUTDOWN_GRACE; L: pending/sent, 503 diagnosis, appendix, "about nine hundred"→"900", CONTRIBUTING governs, synthetic mechanism, permanently — plus a 7-item "genuinely better" list and a Calibration paragraph.

All 20 survive into @L131's 23 items, severities unchanged except `shipit` (M→Low). @L131 names agent-only findings as "item 7 (billing undefined), item 9 (503 diagnosis lost), item 18 (shipit guardrail), item 20 (false precision)". Dropped: the "genuinely better" list, reduced to "`WORKERS`, migration ordering, and the redrive warning are all genuinely better than the original."

## 6. Named rules

Main log: `/Writing for other agents/`, `/RULE \d/`, `/Tier-?1/`, `/system prompt/` — **no match** in any thinking, text or tool input, either turn. Only self-coined: "the co-location principle" (@L125, @L131). @L77's tool result carries a `<system-reminder>` ("NEVER reply to user if uncertainty remains"); @L79 paraphrases it unnamed. Sub @L10 cites its own: "That contract is Tier-1 (explicit user instruction)… No RULE 1 project standards apply."

## 7. Abstract categories

Main log, both turns: `/hedge/`, `/modal(ity)?/`, `/unmarked/`, `/licen[cs]e/`, `/epistemic/`, `/\bframe\b/`, `/certaint/`, `/overclaim/` — **no match**. Present: `caveat` 25×, `framing` 3×, `principle` 3×.
**T1**: `caveat` first @L23 char 1053, on a named instance mid-inventory — "the more borderline stuff like the month-end caveat"; no category term precedes the first concrete instance; `framing` absent.
**T2**: `framing` first @L108 char 2668, on an instance ("the original's explicit framing that this value was arbitrary"); `caveat` @L108 char 3007 (STRICT_ORDERING). @L118's prompt introduces "MORE certain or MORE bounded" as categories ahead of any instance; `more bounded` recurs @L131. `false precision`, `principle` first @L125, after that block's concrete items.
**Sub**: `hedge` 6×, `calibrat*` 7×, `certainty inflation`, `overclaiming`, all @L9; `hedge` first on "about nine hundred records".

## Manifest

MAIN 16 thinking / 12 text / 18 tool_use read verbatim; 18 tool_result read (@L73 tail only — a `cat` of the file read whole at @L58/@L106). 44 attachments: 19 `hook_success`, 1 env block (read), 1 each tools/agents/skills/auto_mode delta, 20 token reminders. SUB 2 thinking / 1 text / 2 tool_use / 2 tool_result / 1 prompt — all read.
