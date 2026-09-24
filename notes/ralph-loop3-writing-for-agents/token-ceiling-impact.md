# The `.ralph/agent/*` 6000-token ceiling: what it bought and what it cost

Impact analysis of one line in the loop's own `PROMPT.md`, over the ten-iteration
run that ended at `max_iterations` on 2026-09-22 (rounds 12–21, 4 h 19 m,
`0f32e2ef..0ccb29b9`):

> `.ralph/agent/*` ≤ 6000 tokens by `agent-tools count-tokens`. relocation is
> growth. Cut before add.

`.ralph/agent/` holds `scratchpad.md`, `decisions.md`, `memories.md`,
`summary.md`, `tasks.jsonl` — the only state that crosses an iteration boundary,
since each round starts with a fresh context.

A rendered version of this analysis is published at
<https://claude.ai/artifact/DhyTyaFidiKPxZwPhMDTbk>; its source is
`token-ceiling-report.html` beside this file. **This markdown governs.** The two
carry the same claims and will diverge the moment one is edited alone; the HTML
is kept only because the published page cannot be regenerated from this file.

## Summary

The rule works as a **size** control and fails as a **growth** control.

Inside the directory it names it is close to exact: ten rounds of an agent that
writes constantly ended 49 tokens heavier than they started, and the notes stayed
readable. It bought that by making every round delete something, which turned out
to be the only recurring review of carried state the loop had.

Outside that directory the material did not stop existing — it moved. The clause
meant to prevent exactly that, `relocation is growth`, never fired: across all ten
sessions it appears only where the harness pastes the rule in, and no reasoning
block applies it to a decision. Meanwhile `.claude/skills/prompt-tests/SKILL.md`,
which nothing capped, grew 26% and absorbed, word for word, rules deleted from
`memories.md` to fit under the ceiling.

And for eight of the ten rounds the loop measured itself with a narrower glob than
the rule states, so half the rounds closed above 6000 believing they were under.

## Measurements

All counts are `agent-tools count-tokens` on the default (local) backend — the
backend the rule's bare `count-tokens` selects, and the one every round used.

### The capped directory, round by round

Round-end totals over the five files, by the rule's literal glob:

| Round | End total | vs 6000 | Peak measured in-round |
| --- | --- | --- | --- |
| 12 | 5834 | −166 | 6609 |
| 13 | 6156 | **+156** | 6370 |
| 14 | 6159 | **+159** | 6252 |
| 15 | 6071 | **+71** | 6375 |
| 16 | 5926 | −74 | 6538 |
| 17 | 6118 | **+118** | 6062 |
| 18 | 6122 | **+122** | — |
| 19 | 5995 | −5 | 6756 |
| 20 | 5550 | −450 | 6088 |
| 21 | 5943 | −57 | 6306 |

Inherited state at round 12's start: 5894. Net over the run: **+49**.

Gross churn inside the directory over the same range — the "cut before add"
exchange, as git records it:

```
scratchpad.md  +1037 −1026
decisions.md    +408  −397
memories.md      +98  −110
summary.md        +1   −15
tasks.jsonl       +4    −4
                -----------
                +1548 −1552
```

Live working tree at the time of writing: **5999 of 6000**. The last 56 tokens of
headroom went to the harness summarizer rewriting `summary.md` after the final
round — a file no agent authors, whose current body reads `_No scratchpad found._`

### The three destinations, indexed to round 11

| File | Round 11 | Round 21 | Change | Governed by |
| --- | --- | --- | --- | --- |
| `.ralph/agent/*` | 5894 | 5943 | +0.8% | the user's 6000 |
| `.claude/skills/prompt-tests/SKILL.md` | 4663 | 5897 | **+26.5%** | nothing |
| `sys_prompt/CLAUDE.md` | 7417 | 7227 | −2.6% | a rule the loop wrote itself |
| `sys_prompt/alan-default-next.md` | 4261 | 4189 | −1.7% | the round's own edits |

Repo-wide the run was still deletion-positive: −1608 lines, mostly the
prompt-test case corpus.

## What it bought

**P1 — flat notes under constant writing pressure.** Each round drafts a
critique, a milestone rationale, a result, decisions and memories. 1,548 lines in,
1,552 out, +49 tokens net. The summed in-round overshoot above each round's own
starting size is about 4,930 tokens (+715, +536, +289, +409, +660, +329, +634,
+603, +756) — a lower bound, since several rounds cut before they first measured.

**P2 — it produced a reusable compression method.** The loop's most transferable
output is a cut-order it wrote for itself, and it exists because something had to
go every round. It is the part of the scratchpad every later round kept:

> Cut in this order, stopping at the first class that is load-bearing: a **claim**
> (only claims can be wrong), a **restatement** (two wordings, nothing saying
> which governs), a **duplicate of executable code** (replace with its name), a
> **trap** (what the reader gets wrong silently; keep). Deletion is the default;
> each *keep* needs the argument.

**P3 — the forced re-read caught stale and false claims.** Deleting requires
reading, and reading carried state against the round's new findings surfaced
defects nothing else in the loop checked for. Round 20 deleted two memories not as
redundant but as contradicted by its own measurement, and said so
(`iter20` required-notes: *"six memories deleted rather than kept — two are
contradicted by this round's measurement, not merely superseded"*). Round 12,
sweeping under budget pressure, found a memory citing a prompt-test case that had
already been deleted and rewrote it to drop the dead name.

**P4 — the pattern propagated to a file nobody capped.** Having worked under a
number, the loop wrote its own for the file it cared about, unprompted:

> A round that ships no prompt edit may not add a paragraph to
> `sys_prompt/CLAUDE.md`; it may replace one, and the replacement is shorter than
> what it replaced.

That file fell 2.6% over the run. This is the only result in the run that bears on
the objective's own question — whether growth can be bounded without a human
prescribing a size limit.

**P5 — the audit number ended up somewhere immutable.** Round 19 found that a
token count written inside the counted files invalidates itself, and moved the
figure to the commit message (`cf8f2dac`: *"Stating the token count inside
.ralph/agent/ changes the count it states; the number goes in the round's last
commit message instead."*). Every round since closes with a dated, unrewritable
statement of its own size.

## What it cost

**N1 — eight rounds measured something narrower than the rule.** The rule names a
tool, not a command, so each round invented one. Most used `.ralph/agent/*.md`,
which silently drops `tasks.jsonl` (193–505 tokens, 3–8% of the ceiling). Round 18
self-reported 5754; round 19 re-measured the same commit at 6122. Round 19's own
critique: *"a hard user budget unmeasured and breached for two rounds … a rule
with no command is what let two rounds miss it."*

**N2 — the measurement is inside the thing measured.** Recording the count, the
commit range, or the ceiling rule itself changes the count. Round 19's trace:
`6122 → 6756 → 6248 → 6040 → 5988 → 6010 → 6015 → 6002 → 6003 → 5995`. It
committed at 5988, updated the heading with the hash it had just created, and was
back at 6010. The fix — rewriting the contract line to say the number belongs in
the commit message — was itself longer than the line it replaced and pushed the
total to 6015; three unrelated paragraphs were cut to pay for it. One pass
intended as a cut ran one token long.

**N3 — "relocation is growth" never once fired.** The clause exists to stop the
obvious evasion. Across ten sessions it appears only in the injected rule text.
Meanwhile the most common stated reason for a deletion is that the content
"already lives in the skill" or "already lives in `sys_prompt/CLAUDE.md`". Three
such deletions can be matched to their arrival in the skill file verbatim:

| Deleted from `memories.md` under the cap | Added to `prompt-tests/SKILL.md` |
| --- | --- |
| the staged-diff leak fix | `--label before/<f> --label after/<f>` |
| the probe-naming fix | "directory sharing a word with its own fixture is found by the ordinary search…" |
| the probe-deletion rule | "A probe's directory is deleted by the round that wrote it" |

How much of the skill's +1234 tokens is displaced `.ralph` content is not
established — these three are; the rest is independent instrument work.

**N4 — roughly half the budget is spent on files the next round never sees.** Per
`/workspace/ralph/build.yml`, only `scratchpad.md` is injected into the next
iteration's prompt; `memories.md` is `inject: manual` and `decisions.md` is never
dumped in any configuration. Current split: scratchpad 2746 (46%), memories 1639
(27%), decisions 1349 (22%), tasks 185, summary 80. So the cap on the handoff
channel is effectively 2,746 of a nominal 6,000, and the rest is taxed as archive
— including two files the agent does not author, one of which the CLI cannot even
prune (`ralph tools task` has no delete; round 19 pruned `tasks.jsonl` with a
hand-written Python filter and flagged it).

**N5 — end-of-round trimming becomes word-level, at the wrong moment.** The
housekeeping block sits last, beside the handoff the round is writing for its
successor, so the cap binds hardest on the text whose quality matters most. Round
14 ran roughly fifteen measure-and-edit cycles, ending
`6035 → 6011 → 6004 → 6002 → 6000 → 5966` — the last passes removing single words.
Budget-related tool calls per round: 33 (12), 20 (13), 28 (14), 12 (15), 13 (16),
17 (17), 9 (20), 9 (21).

**N6 — compression by line number, over a semantic contract.** Round 17 compressed
the loop history with `head -110 .ralph/agent/scratchpad.md > /tmp/sp.md`, a cut
chosen by position rather than meaning. It took the rounds 1–14 digest, the round
15 digest, and the whole round-16 section — including the `(instruction)` block
round 16 had written *for round 17*. The instruction was read before it was
destroyed, but the record that would let a later round check whether 17 complied
went with it. Rounds do re-derive when they notice a gap (round 17 reconstructed a
case's entire run history with `git log`), which is recovery at a cost.

**N7 — it contradicts the harness contract, and the conflict was never resolved.**
The scratchpad directive the harness injects says to append; the user rule says to
cut. Round 16 named the conflict, decided it alone, and reported it in a closing
note: *"the between-worker contract says 'always append' to the scratchpad while
the user caps `.ralph/agent/*` at 6000 tokens. Those conflict; the budget wins …
Worth an explicit (contract) line if a later round trips on it."* No round wrote
that clause, and nothing raised it where a human would see it.

## The one that cuts both ways

The task asks that documentation stop growing *without a human setting or
prescribing a size limit*. The loop's own notes are the one surface where a human
set one — so the strongest anti-growth result in the run comes from the mechanism
the objective rules out, and says nothing about whether the agent would have
bounded itself unaided.

And it is also the only evidence that self-limiting works. Having lived under a
number, the loop wrote an unprescribed rule of the same shape for
`sys_prompt/CLAUDE.md` — replace, don't append; the replacement is shorter — and
that file fell while the file governed by nothing rose 26%. The prescribed limit
did not answer the question; it demonstrated the pattern an answer would need.

## If the rule stays

1. **Name the command, not the tool.** Eight rounds measured a narrower set than
   the rule states because each had to invent the invocation. The one that wrote
   the command down ended the breach.
2. **Exclude what the agent does not write.** `tasks.jsonl` and `summary.md` are
   harness output, the CLI cannot prune the first, and together they took the last
   250 tokens of headroom.
3. **Cap the handoff, not the archive — or cap them separately.** Half the budget
   currently constrains files the next round is never shown.
4. **Put a ledger on the destinations.** `relocation is growth` is unenforceable as
   written and fired zero times; the skill file grew 26% while the capped
   directory stood still.
5. **Forbid the number inside the counted set.** Round 19 derived this the hard
   way; it belongs in the rule, not in a contract line the next cleanup may cut.

## Method, and what is not established

Five `session-analysis` subagents in evidence mode over the ten iteration
transcripts, one focus: everything touching the ceiling. Artifacts in
`evidence/`, each citing JSONL line refs. Sessions (under
`~/.claude/projects/-root-claude-config-work/`, outside git and not durable):
`06fa1252`, `b52a94fd`, `76383586`, `05117af2`, `8cbdf6ab`, `cdcc1497`,
`08ce9bfe`, `9bb51163`, `122b4216`, `2328f962`. Rounds 16–17 were extracted on
Opus 5; the other four pairs on Sonnet, after the Opus dispatches returned an API
safeguard error — extraction depth may differ between them.

Reproducing the numbers here:

```bash
# round-by-round totals
for c in <round-end shas>; do
  for f in scratchpad.md decisions.md memories.md summary.md tasks.jsonl; do
    git show $c:.ralph/agent/$f | agent-tools count-tokens --file /dev/stdin
  done
done

# gross churn
git log --format= --numstat 0f32e2ef..0ccb29b9 -- .ralph/agent/ \
  | awk -F'\t' 'NF==3 {a+=$1; d+=$2} END {print a, d}'     # 1548 1552

# live state
cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin   # 5999
```

Not established: whether any deleted material was later needed — only two
re-derivations are on record, and a round that silently lacked something leaves no
trace. What the directory would have done with no cap — the churn figures show
what was exchanged, not what would have been kept. How much of the skill file's
growth is displacement rather than its own work.
