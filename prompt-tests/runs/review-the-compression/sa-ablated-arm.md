# Focus: how the agent derived its RUNBOOK-short findings

**Provenance.** `ee9b8958…jsonl` in project `-tmp-ptcc-review-the-compression-ablated-jujUsW`; 58 lines; claude-opus-5; cc 2.1.235 `sdk-cli`; cwd `/tmp/ptcc-review-the-compression-ablated.jujUsW`; task @L5. Read via `cc-pretty --skeleton` + `sed|jq`; all thinking, text and tool inputs read; L19/L25 skimmed.

## 1 Reading path (all Bash)
- @L13 `ls -la <dir>/ && echo "=== WORD COUNTS ===" && wc -w <dir>/*.md` → `1163`/`358`.
- @L17 `cat -n RUNBOOK.md`; @L23 `cat -n RUNBOOK-short.md` + `cat .prompt-test-settings.json` — both in full (135/49 lines).
- @L27 thinking: 22 paragraphs, 4,959 output tokens; no tool call between L25 and L27.
- @L29 loop of `grep -ci -- "$t"` on both files, 16 terms: `STRICT_ORDERING SHUTDOWN_GRACE shipit CONTRIBUTING force-push venv pytest docker-compose 5433 "by design" "not a rule" "module names" dashboards Monday acknowledges reload` → 16/16 `short=0`.
- @L36 `grep -n '^##'` both; `grep -n -iE "never (been )?(measured|put|run|documented)|not a rule|by design|nobody has|we think|unproven|not an oversight|conversation to have" RUNBOOK.md`; short side `-iE "never|nobody|unproven|by design|not a rule|we think|declined"`.
- @L41/@L53 `agent-tools pre_output.record`; @L46 `ls -la; find . -type f`, `find . -iname 'CONTRIBUTING*' -o -iname 'README*'`, `git rev-parse`. No `diff`; neither file re-read.

## 2 Finding origins (all in @L27, after both `cat -n` reads, before any grep)
(a) Dropped — P4 "the guardrail around not switching to the platform team's `shipit` pipeline"; P6–7 "quietly cutting `STRICT_ORDERING=0`… loses an explicitly flagged unknown"; P11 "CONTRIBUTING.md governs repo conventions, and section 4 on force-pushing… trips people up"; P14 "The entire local setup appendix got cut — roughly 110 words".
(b) Changed meaning — P3 "'nothing times out'… shortened to just 'safe'"; P5 Friday "turns a soft, unenforced norm into what reads like a hard rule"; P6 "'the ones that matter' is an added editorial judgment"; P8 "'Tune freely' strips that conditional framing"; P12 "by design, not a limitation to 'fix'"; P13 "runs every minute against a fixed record id".
(c) Structural — P19–20 "these cuts are invisible… 'reader doesn't know there's anything to check'"; P21 "relative time references ('eleven weeks,' 'in March,' 'in February') got copied without absolute dates".

## 3 Counting claim
Produced @L27 P17–18, before any grep. P17 "The pattern worth naming is how the original marks epistemic status…" + five phrases. P18: "…month-end being unproven survives, the unknown threshold survives, RETRY_BACKOFF's 'never measured' status survives but its conclusion gets flipped, and the finance-declined point partially carries over. But it drops STRICT_ORDERING's untested status, the shipit reasoning, the Friday-not-a-rule note, and the redrive-by-design point entirely." @L35: "I should verify the epistemic-marker claim by pulling out the hedging phrases from the original." @L36's grep returned 8 full-doc hits (ll. 23, 34, 54, 56, 75, 81, 98, 110), 5 short-doc hits (28, 34, 44, 46, 48). Grep hits and the answer's 8 named phrases differ one each way: grep matched `we think` (l.54), unnamed in the answer; the answer names "never measured" (ll.48–49, split "never been / measured", no grep hit).

## 4 Named rules
No rule, principle or convention from the system prompt or output style is named in any thinking block. @L40: "planning to format the response with evidence, details, and required notes per the template, though I have no delegation to log since I did this myself." @L43/@L55 carry `NEVER reply to user if uncertainties remain. Do more verification and research`; @L45 answers "I should keep pushing to verify rather than settle for uncertainty"; @L57 files it under "instruction issue". No skill invoked.

## 5 Vocabulary
Within @L27: "guardrail" P4, "modality" P5, "conditional framing" P8, "'don't improve this' category" P12, "epistemic status"/"hedging"/"honesty about uncertainty" P17, "guardrails" P19 — each after concrete instances; P17 follows the section pass ending at P15.

## 6 Dropped or abandoned
@L27 P10 environments "implicitly covers that ground, so it's acceptable"; P11 redrive "actually a reasonable reorganization"; P22 "SHUTDOWN_GRACE is… the weakest of the config complaints… fairly defensible". P21 names two checks never run, absent from the answer: "'the ledger' versus 'the ledger service'" and "vendor's connection limit versus the configured worker count". @L41's three `uncertainties` become @L53's "None affecting the findings…" after @L46's `find`.
