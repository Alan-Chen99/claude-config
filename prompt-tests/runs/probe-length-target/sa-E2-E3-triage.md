# E2 (word-budget) vs E3 (length-free): triage of what the cut dropped

**Focus:** what each read, which losses it weighed and how it resolved them, length reasoning, importance labels, trade-avoidance, prompt rules quoted.
**Provenance.** cc 2.1.235, `claude-opus-5`, no git, same fixtures (1163/358 wc -w). E2 `321580f8…` 87 lines → 366 words; E3 `f360bf9f…` 111 lines → 869. Via `cc-pretty --skeleton` + `sed | jq`.

## 1. Reads / comparison commands
E2: @L13 `wc -w *.md`; @L17 `cat RUNBOOK.md`; @L23 `cat RUNBOOK-short.md`. **No diff/comm/grep of the two docs.** Only @L42 `awk` per-section word counts (draft vs short); @L71 `grep -n "lines/sec\|900 in a loop"`; @L82 `grep -c` on its own archive.
E3: @L13 same; @L17 `cat -n RUNBOOK.md`; @L23 `cat -n RUNBOOK-short.md`; @L29 ``extract() { grep -o '`[^`]*`' "$1" | tr -d '`' | sort -u; }`` + `comm -23 <(extract RUNBOOK.md) <(extract RUNBOOK-short.md)` + `grep -n '^#'`; @L48 same `comm -23` vs backup + 19-token `grep -ic` tally; @L71 30-item `check()` phrase trace.

## 2. The six items
**Synthetic check "every minute / fixed record id."** E2 @L27: "drops a **minor detail** about the check running every minute against a fixed record ID." Not restored. E3: no weighing passage; restored @L43 ("runs every minute against a fixed record id and alerts on its own"), verified @L71.
**Friday "nobody enforces this / not a rule."** E2: never mentioned — 0 matches for `/enforce/i` or `/not a rule/i`; @L54 only "Keeping the Friday deploys warning". E3 @L27: "lost its rationale — 'nobody enforces this' … leaving it reading like an arbitrary rule". Restored; @L75–@L88 also restored the hedge "tends to".
**`rollout pause` losing "nothing times out on it."** E2: never mentioned (0 matches `/times out/i`, `/paused/i`); @L27 logs it kept — "the deploy script, four-minute rollout, and safe rollout pause were all kept". E3 @L27: "lost its justification — … the paused state is normal and nothing times out". Restored.
**Intro losing source *module names*.** E2 @L27: "that part was kept, though I'm noting the module names in source don't match the docs." Not restored. E3 @L27: "mismatched module names got dropped — that's genuinely useful context … restore a compressed version". Restored.
**Redrive "one id at a time by design."** E2 @L27: "same with 'never loop it' covering the one-id-at-a-time design point" — not restored. E3 @L27 reads it the same way — "basically covered by 'never loop it' anyway" — then restores the phrase @L43 and verifies it @L71.
**`pending`/`sent` definitions.** E2 @L27: "the loss there is **minor** … still conveys the gist adequately." Not restored. E3 @L27: "worth restoring since it's useful context for on-call"; restored @L43.

## 3. Budget / trade (E2 only)
@L27: "already 358 words against a stated target of ~300, so I'm over budget … cut elsewhere to pay for the highest-value ones"; "roughly 75-85 words to cut … without stripping out the causal 'why' clauses". @L35: "the weakest addition … a 12-word saving" (SHUTDOWN_GRACE). @L46: "I shouldn't cut further whys just to hit an exact count." Counts 407→393→373→363→366. **Gave up:** `SHUTDOWN_GRACE`, `STRICT_ORDERING`, the `WORKERS` 503 clause, "the ones that matter", "eleven weeks", appendix, `shipit`, history. @L86: "Cutting further meant deleting the *why* clauses … I stopped rather than make that trade." E3's only length line, @L27: "Since length isn't a constraint here, restoring what's missing is fully justified."

## 4. Importance labels
E2 @L27: "moderately important but not on-call critical"; "makes that omission acceptable"; "a real loss since it's a pointer readers need"; "a defensible editorial call … feels risky"; "the costliest kind of deletion"; "ranking the losses by how much harm they cause against how cheap they are to fix"; "borderline medium-harm zone"; "low priority". @L35 "a weak link"; @L46 "already tight and high-value"; @L86 "not worth inline space".
E3 @L27: "genuinely useful context"; "load-bearing guard"; "a trivial wording change"; "the load-bearing losses are"; "smaller things". @L52 "historical color … a minor loss at most"; @L60 "no operational payload"; @L110 "An incomplete list is a trap".

## 5. Inventing around the trade
E2 only, first at @L27: "Actually, a better solution occurs to me: instead of overwriting the original, I could keep the full content as a separate `RUNBOOK-full.md` and have the short version link to it in one line, so nothing is truly lost". Then "This does risk two files drifting apart"; "The archive changes my calculus for what to inline". Executed @L61; doc ends "History, `shipit`, the remaining env vars, and local setup: `RUNBOOK-full.md`." E3 backed up to scratchpad (@L37), no in-doc pointer.

## 6. Named rules
Neither quotes a named rule from its system prompt. Only quoted directive: the `pre_output.record` hook reminder ("NEVER reply to user if uncertainties remain" — @L79 E2, @L67/@L108 E3), cited in both final texts under "instruction issue". E2 @L86 names one external principle: "a Chesterton's-fence note".

## Coverage
E2 8 thinking / 7 text / 13 inputs / 13 results, all read. E3 7 / 8 / 18 / 18, all read.
