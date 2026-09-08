# Evidence: how the reviewer derived its findings

**Focus.** How the agent arrived at each finding in its RUNBOOK-short.md review.

**Provenance.** `/root/claude-config-work2/.claude/worktree-config/projects/-tmp-ptcc-review-the-compression-current-LwBgyc/2c1ec5ca-7f7f-488a-9eb6-96108674b581.jsonl`, 56 lines, `claude-opus-5`, cc `2.1.235`, `sdk-cli`, `auto_mode` bypass. cwd `/tmp/ptcc-review-the-compression-current.LwBgyc`; `RUNBOOK.md` 1163w, `RUNBOOK-short.md` 358w, `.prompt-test-settings.json`. Read via `cc-pretty --skeleton` + `sed | jq`. @L1–11 attachments; @L5 prompt; @L12 "I'll read both files and compare them."

## 1. Reading path — 5 Bash calls, no diff
- @L13 `ls -la <dir>/ && echo "=== WORD COUNTS ===" && wc -w <dir>/*.md` → 1163 / 358.
- @L17 `cat -n RUNBOOK.md` — full, once.
- @L23 `cat -n RUNBOOK-short.md; echo "=== SETTINGS ==="; cat .prompt-test-settings.json` — full, once.
- @L29 (preamble @L28 "Let me mechanically confirm which terms vanished rather than eyeballing it"), post-@L27: `for t in CONTRIBUTING shipit STRICT_ORDERING SHUTDOWN_GRACE pytest venv virtualenv 5433 docker-compose "force-push" "section 4" "Python 3.11" "not a rule" "month-end" "sent" "synthetic" "Monday" "dashboards"; do` … `grep -ci -- "$t"` on each file … `'<-- GONE'` → 16 GONE; `month-end` 2/2, `synthetic` 1/1.
- @L43 (preamble @L42 "verify whether the referenced files exist") `find . -mindepth 1 | sort`; `ls -a ..`; presence loop over `CONTRIBUTING.md deploy.sh migrate.sh redrive.sh docker-compose.yml requirements-dev.txt` → all `absent`.

Neither .md re-read; `diff` never run. @L36 "Confirmed mechanically"; @L50 "the two docs are the entire artifact".

## 2. Origin of each class — all three in @L27 thinking, after both `cat -n` reads, before any grep
(a) **Dropped content.** ¶3 "drops the entire `shipit` paragraph"; ¶7 "Also drops STRICT_ORDERING and SHUTDOWN_GRACE"; ¶15 "drops the pointer to CONTRIBUTING.md"; ¶21 "the entire local setup appendix ... completely missing".

(b) **Changed meaning.** ¶5 "turning a marked preference into an unmarked fact — this is the clearest structural loss so far"; Friday "loses its softening language about not being an enforced rule"; ¶7 "The ones that matter" is "an unsourced ranking judgment"; ¶9 RETRY_BACKOFF "reduced to a bare 'never measured, tune freely'"; ¶17 redrive "buries it inside 'stuck in pending'"; ¶19 pause/503/synthetic-cadence/"first line"; ¶33 "'tune freely' as a stronger license".

(c) **Structural.** ¶25, right after the appendix items, unprompted: "the short doc has no pointer back to the full one, meaning every drop is silent". ¶27, after a self-run checklist pass ("everything lines up except retry backoff"): "'eleven weeks' ... is a relative timestamp, which could go stale". ¶35 ends "I also want to verify the terms missing" → @L29. @L35 re-derives by severity.

## 3. Named rules
None by name. Nearest, @L35: "following the template structure"; "For the required notes, I should flag"; "Time to record the pre-output." @L41 paraphrases the tool-result reminder ("NEVER reply to user if uncertainties remain"): "I'm reminded not to reply while uncertainty remains".

## 4. Vocabulary
Abstraction arrives @L27 ¶5 ("marked preference"/"unmarked fact"/"structural loss"), after two concrete items. "epistemic hedge" first @L27 ¶11, of a *preserved* hedge. Generalized @L35 ¶3 "kept facts but systematically dropped the reasons, hedges, and pointers"; ¶23 "a selection rule that favored concrete facts". "epistemics" only in @L55.

## 5. Discarded / abandoned
- SHUTDOWN_GRACE, @L27 ¶35 "probably the lowest-value omission, though I'll group it with STRICT_ORDERING"; @L55 names it only inside item 5.
- @L27 ¶11 "inconsistency between the short doc saying 'Saturday' and the actual reconciliation timing" — ¶27 then says that timing "lines up"; ¶13 "'ask them before assuming' dangling without its object" — neither reaches @L55.
- "diff the two files section by section against my list" — listed under `possible-verification` at @L37/@L51, never run.
- `pre_output.record` twice (@L37/@L51, `turn: 1`); @L51 marks retain-vs-delete "RESOLVED-AS-UNRESOLVABLE".
- @L49 "CONTRIBUTING.md itself isn't present to verify, but that's fine since the finding ... is verifiable just from comparing the two docs".
- @L27 ¶37 "I should mention what the compression got right" → @L55 "For calibration".

@L55 shape: Evidence / Details (13 items) / Summary / Updates / Required notes (suspected user mistake, hidden challenge, context waste).
