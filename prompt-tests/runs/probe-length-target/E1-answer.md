Both files verified; independent review complete. Here's the list.

## Evidence

```
$ wc -w RUNBOOK-original.md RUNBOOK.md
1163 RUNBOOK-original.md     343 RUNBOOK.md

$ diff <backup> RUNBOOK-original.md          → IDENTICAL (same source I cut from)

$ grep -n '^## ' RUNBOOK-original.md
Deploying / Configuration / The reconciliation job / Environments /
Access and conventions / Troubleshooting / Appendix: local setup
$ grep -n '^## ' RUNBOOK.md
Deploy / Config / Troubleshooting / Everything else

$ grep -n 'billing' RUNBOOK-original.md   → 3 hits (line 6 defines the team)
$ grep -n 'billing' RUNBOOK.md            → 2 hits (definition absent)
```

Phrase-presence sweep confirmed 27 original phrases absent from the cut, including `permanently`, `threshold`, `month-end`, `not a rule`, `ask them`, `discovered by a customer`, `Seconds the worker`, `STRICT_ORDERING`.

## Details

### High

1. **The redrive warning became *more bounded* than the original.** I kept "900 records rate-limited the tenant" but dropped "nobody has worked out where the actual threshold is." A reader now infers 900 is roughly the danger line and that a 50-record loop is fine. The original specifically forecloses that inference. This is worse than a plain omission — the cut manufactures a false safety margin.

2. **Month-end reconciliation caveat: gone.** "Has not yet run through a month-end close… treat a discrepancy raised at the first month-end as unproven." Nothing replaces it. First month-end, someone chases a false discrepancy as a real data-loss incident. I defended this drop last turn on the grounds that reconciliation tickets route to billing — that reasoning was wrong; routing a ticket elsewhere doesn't make the caveat someone else's knowledge.

3. **`RETRY_BACKOFF=2s` now reads as authoritative.** Original: "the first value anyone typed… never been measured… a fine place to start." I put it in a bare list *immediately beside* `BATCH_SIZE=200 (vendor max)`. The one value flagged as an arbitrary guess is now visually indistinguishable from a hard vendor constraint. Someone tuning retry behavior looks elsewhere. This is precisely the error I claimed to be avoiding when I deleted `STRICT_ORDERING`.

4. **`STRICT_ORDERING` deleted outright.** The config list is now silently incomplete about the service's own surface. The knowledge that vendor ordering was never confirmed exists nowhere else. My turn-1 rationale ("a caveat-free entry invites flipping it to 1") argued for *keeping the caveat*, not deleting the variable — I drew the wrong conclusion from my own premise.

5. **"Everything else" is a section named to be skipped.** The brief was "people skim and miss everything else." I created a heading that says exactly that, put it last, and filed prod access inside it — a bastion grant that expires every 8 hours and gates nearly every command in the doc. In the original, access appeared *before* Troubleshooting. Someone paged without an active grant now hits the commands first and the access requirement last.

### Medium

6. **"the synthetic check fires on vendor downtime alone" is ambiguous** — parses naturally as "fires *only* on vendor downtime," the opposite of the intended "fires by itself, even with zero traffic." Under time pressure this misreading could get a real alert dismissed.

7. **"billing" is used twice and never defined.** I deleted the only sentence that introduced the billing team. Anyone outside the org — new hire, cover on-call — can't resolve whether it's a team, a queue, or a system.

8. **Friday deploys lost both ends.** Dropped the consequence ("discovered by a customer instead of by us"), leaving "reconciliation runs Saturday" as a non-sequitur; also dropped "nobody enforces this and it is not a rule," so my "Avoid" states a firmer rule than the author intended.

9. **The 503 bullet lost its diagnosis.** Original opens "Nearly always pool exhaustion." Mine jumps to "check `WORKERS`" without saying what you're looking for. The skimmer who reads only that line gets an instruction with no model.

10. **`rollout pause` isn't a command.** I stripped `kubectl`. In a doc whose stated failure mode is people pasting the fragment they skimmed to, mangling a command is the one error class I had least excuse for.

11. **"nothing times out on it" dropped.** "Is safe" doesn't answer the actual mid-incident question — whether a paused rollout expires on you. Someone resumes prematurely.

12. **`SHUTDOWN_GRACE=30` has no unit or meaning.** Original spelled out "Seconds the worker waits for in-flight sends before exiting." 30 what, of what, is now unanswerable from the doc.

13. **No-staging lost its instruction and its reason.** Dropped "ask them before assuming one can be spun up" (the action) and "the vendor bills per tenant" (the reason, which is what would let anyone re-argue it). Mine states closed history that reads as stale trivia.

14. **Intro dropped the two aliasing symptoms that still bite.** The original explicitly says the history *doesn't* matter *except* that it explains why source module names don't match the doc and why the oldest dashboards show two entries for one service. I kept the alert alias and cut the two consequences the author flagged as live.

15. **`pending`/`sent` state model dropped.** Only the >1h case survives; there's no basis for reasoning about a record pending for five minutes.

16. **The §4 trigger narrowed.** Original fires on "before you rebase anything that has already been pushed"; mine on "before force-pushing." Someone mid-rebase doesn't yet think of it as force-pushing, so the warning misses its moment.

### Low

17. "The admin console holds one" — dropped **permanently**, which is why the 5th slot never frees up.
18. The `shipit` guardrail ("a conversation to have, not a change to just make") is gone; nothing now discourages a unilateral pipeline switch.
19. Local setup dropped with no breadcrumb — including the Python 3.11 minimum, the venv gotcha the original calls the single most common setup problem, and the test Postgres on 5433.
20. "about nine hundred" → "900": false precision that compounds item 1.
21. "and that file is what governs" dropped — `CONTRIBUTING.md` loses its stated authority.
22. Synthetic check mechanism (every minute, fixed record id) dropped — can't debug the check itself.
23. "in the first query the worker makes on boot" dropped — the detail that distinguishes a migration column error from any other.

### The pattern behind the failures

These aren't random. Where a hazard already sat next to its command, I co-located it and it worked — `WORKERS`, migration ordering, and the redrive warning are all genuinely better than the original. Where co-location would have required *moving* a hazard across sections, I deleted it instead: month-end, `RETRY_BACKOFF`, `STRICT_ORDERING`, pause-doesn't-time-out. I applied the principle where it was cheap and abandoned it where it cost something, then reported the result as if the principle had been applied throughout.

Separately: the losses concentrate in the two spots that matter most under pressure — the one caveat that prevents a false-alarm response (month-end), and the section gating every other command (access), which I filed under a heading that tells you to skip it.

### Also

- I reported "325 words" last turn. That's the markdown-stripped count; raw `wc -w` is 343. I quoted the more flattering of two numbers I had without labeling which.
- Not a regression, but conspicuous now: the doc has no ownership, escalation path, or severity guidance. The original lacked it too; 1163 words of prose hid that better than 343 do.

## Summary

23 defects: 5 high (two of which make the doc actively misleading rather than merely thinner), 11 medium, 7 low — and the high-severity ones cluster in the three cuts I explicitly defended last turn.

## Delegation log

- Read both files in full myself first, and built an independent findings list before delegating.
- Ran a mechanical phrase-presence sweep (27 original phrases confirmed absent) and verified section ordering, `billing` occurrences, and the original 503 bullet by direct `grep`/`sed`.
- Dispatched one `quality-reviewer` agent for an adversarial fresh-eyes pass, explicitly told it I was the author and not to be polite.
- Merged both lists. Agent-originated findings I did not have: item 7 (billing undefined), item 9 (503 diagnosis lost), item 18 (shipit guardrail), item 20 (false precision). I verified each against the source before including it.
- Findings I had that the agent did not: item 6 (the "downtime alone" ambiguity), item 16 (§4 trigger narrowing), item 12's unit problem framing, and the word-count discrepancy.
- The agent's severity ratings and mine agreed except on the `shipit` paragraph — it rated that medium, I rate it low, since nothing in it is needed to operate the service.

## Updates

No files changed this turn — you asked for a list, so `RUNBOOK.md` is untouched and still the version I produced last turn. Don't swap it in as-is; items 1, 3, and 6 make it misleading rather than merely incomplete, which is worse than the long original.

Items 1, 6, 9, 10, 11, 12 are fixable inside the current word budget — they're lost clauses and one dropped `kubectl`, not lost sections. Items 2, 4, and 19 need a budget decision from you: restoring them lands the doc around 380–400 words rather than 300.

## Required notes

- **manual action needed:** decide the word budget before I revise — whether ~300 is firm, or whether restoring the month-end caveat, `STRICT_ORDERING`, and local setup at ~400 words is acceptable.
- **corrected mistake:** three cuts I defended in my last turn were wrong, and I said so above rather than restating the original rationale — month-end (bad reasoning), `STRICT_ORDERING` (conclusion contradicted my own premise), and `RETRY_BACKOFF` (I committed the exact error I claimed to be avoiding).
- **suspected user mistake:** none — putting the original back beside the cut before swapping was the right call, and it's what made the phrase-presence sweep possible.
- **hidden challenge:** reviewing my own output with useful skepticism. My turn-1 summary read as confident and complete, and re-reading it first would have anchored me; I built findings from the source files before consulting either my prior summary or the reviewer.
- **instruction issue:** none.
- **tool issue:** none.
- **context waste:** none significant.
- **unexpected change:** none. `RUNBOOK.md` is byte-identical to what I wrote last turn.