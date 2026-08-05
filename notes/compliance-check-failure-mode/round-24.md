# Round 24 — Comparator-baseline audit; R22/R23 magnitude claims corrected; R23 model confound named

Not a new probing round. This round audits R22 and R23 write-ups against directly-measured contam session data. Two errors found:

1. **Baseline lookups never performed.** R22 and R23 write-ups cite contam tool_use counts as "0" (for skip cells) and "6+" (for H6), taken from R13's narrative language *"F46 skip"* / *"6+ older-worktree reads"*. R13's "F46 skip" is a categorical crossing-axis label, not a tool_use count. Direct measurement this round via `agent-tools opencode-pretty` on the six comparator sessions shows the actual contam counts differ substantially from what was reported.
2. **R23 introduced a model version confound.** R13 Runs C/E/F ran on `openai/gpt-5.4`. R23 clean re-runs used `openai/gpt-5.5/xhigh` (inherited from `/tmp/run_r22.sh`'s hard-coded flag). The pre-run comparator inspection that would have caught this was not done. R22's H6/H9/N1 comparators were `openai/gpt-5.5/xhigh` in both contam and clean, so R22 is model-consistent; R23 is not.

## Measured contam counts vs write-up claims

| Cell | R22/R23 write-up | Actual contam total tool_use | Actual contam older-worktree crossings | Model (contam) | Model (clean) |
|---|---|---|---|---|---|
| N1 `ses_089162a4dffeiWgHMQ881UJOq3` | "0 (F46 skip)" | **42** | 0 | gpt-5.5/xhigh | gpt-5.5/xhigh |
| H6 `ses_0782dfe02ffe2L0RUtoi9fDVcL` | "6+ (F46 break)" | **56 total / 6 crossings** | 6 | gpt-5.5/xhigh | gpt-5.5/xhigh |
| H9 `ses_073df183fffeQvInu5ry2Eq8QC` | "0 (F46 skip)" | **46** | 0 | gpt-5.5/xhigh | gpt-5.5/xhigh |
| Run C `ses_082989c9bffemlrQJAKu17aqVv` | "0 (F46 skip)" | **18** | 0 | **gpt-5.4** | gpt-5.5/xhigh |
| Run E `ses_07c5fb651ffecud8NIEuS2VrFg` | "0 (F46 skip)" | **15** | 0 | **gpt-5.4** | gpt-5.5/xhigh |
| Run F `ses_0796c736dffeccAcVCwrHVv5e1` | "0 (F46 skip)" | **22** | 0 | **gpt-5.4** | gpt-5.5/xhigh |

Method: `agent-tools opencode-pretty $ses --show-usage | sed 's/\x1b\[[0-9;]*m//g'`, regex-parse `◀ result (TOOL)` markers for totals; regex-parse `filePath: /root/claude-config-work/...` for crossings; extract model from `[openai/...]` header. `opencode export` was tried first but truncates at unterminated-string JSON parse errors on these sessions.

## Corrected clean-vs-contam picture

Real signals, both axes measured on each side:

| Cell | Contam (total / crossings) | Clean (total / crossings) | Real deltas |
|---|---|---|---|
| N1 | 42 / 0 | 45 / 2 | tools flat; crossings 0 → 2 |
| H6 | 56 / 6 | 51 / 3 | tools flat; crossings 6 → 3 |
| H9 | 46 / 0 | 63 / 3 | tools +17; crossings 0 → 3 |
| Run C | 18 / 0 | 40 / 0 | tools +22; crossings unchanged (model confound bundled) |
| Run E | 15 / 0 | 40 / 0 | tools +25; crossings unchanged (model confound bundled) |
| Run F | 22 / 0 | 64 / 0 | tools +42; crossings unchanged (model confound bundled) |

The load-bearing crossing-axis signals (R22 side, model-consistent):
- **N1**: 0 → 2 crossings. Real. F68 empirical "N1 neutrality control was skip" claim contradicted at direction.
- **H6**: 6 → 3 crossings. Direction preserved (both cross). Magnitude decrease possibly within run-variance at n=1.
- **H9**: 0 → 3 crossings. Real. F74 "v5 hint-strip doesn't cross" claim contradicted at direction.

The R23 crossing-axis signal:
- **Runs C/E/F**: 0 → 0 crossings across all three. **No shift.** Frontmatter cleanup did not change crossing behavior on v1/v2/v3+minimal-task. Tool_use total shifted 15-22 → 40-64, but this is confounded by the gpt-5.4 → gpt-5.5 model change and cannot be attributed to frontmatter cleanup alone.

## What survives and what doesn't

**R22 findings that survive at direction level:**
- **F68 empirical contradiction (crossing axis).** N1 clean crosses, contam did not. Directional contradiction real. The write-up's "0 → 45 tool_use" framing was wrong (actually 42 → 45).
- **F74 core-claim contradiction (crossing axis).** H9 clean crosses, contam did not. Directional contradiction real. The write-up's "0 → 63" framing was wrong (actually 46 → 63).
- **H6 direction preservation.** Both contam and clean cross. Consistent.

**R23 findings that do NOT survive:**
- **"F72 0 tools skip contradicted."** Fabricated from misreading. R13 never claimed 0 tools; it claimed 0 crossings. Contam and clean Runs C/E/F both show 0 crossings. No contradiction of F72 established.
- **"F74a premature scope closure contradicted."** Rested on the same 0-tool misreading. Contam Run F did 22 tools of inspection with 4 todowrite planning ceremony. Clean Run F does 64 tools with different inspection breadth. Whether the H5 self-report *"operational interruption decision"* framing changes under clean spec cannot be assessed from the raw tool_use delta alone.
- **"F72 path-crossing preserved and reframed."** Framed as a preserved observation; actually a null result. Runs C/E/F crossings are 0 → 0. No shift means no evidence about the crossing axis one way or the other from R23 alone.

**Anything about Runs C/E/F clean vs contam is confounded by the model change.** To isolate the frontmatter variable, need one of:
- Re-run round-13 Runs C/E/F contam sessions on `openai/gpt-5.5/xhigh` (test whether contam v1/v2/v3 on gpt-5.5 also produce 0 crossings — if yes, no frontmatter effect on crossing).
- Re-run round-23 Runs C/E/F clean on `openai/gpt-5.4` (test whether clean v1/v2/v3 on gpt-5.4 produce the same 0 crossings — if yes, no model effect on crossing).

Either test would isolate the variable. The current R23 data cannot.

## Semantic drift in "F46"

The load-bearing terminology failure. R13's "F46 skip" and "F46 break" always meant crossing-axis (zero older-worktree reads / positive older-worktree reads). R22 and R23 write-ups drifted into using "F46 skip" as shorthand for "zero tool_use" and put tool_use totals in the numeric slot next to crossing-axis categorical labels. The metric drift compounded across two rounds before this audit.

Any future round that cites "F46 skip" should distinguish crossing-axis (the original meaning) from inspection-quantity-axis (the drifted meaning). Preferred convention going forward: use "crossing-skip" / "crossing-break" for the axis R13 tracked, and quote raw tool_use counts directly rather than F46 labels for inspection-quantity claims.

## What still needs to happen

Not deferred; escalated to explicit next-round follow-ups:

1. **Round-22 write-up magnitude corrections.** Replace "0 → 45", "0 → 63", "6+ → 51" with the actual counts. Direction claims survive; magnitude framing needs to say "small crossing shift" rather than "large tool_use shift". Corrected in the main file's per-round summary this round.
2. **Round-23 write-up retraction of "F72 contradicted".** The claim is not supported by the data. Corrected in the main file this round; round-23.md left in place as-is (historical record) with pointer to this round.
3. **Isolate the model variable on Runs C/E/F.** Requires either gpt-5.4-clean re-runs or gpt-5.5-contam re-runs of round-13 Runs C/E/F. Not done this round.
4. **F72 status is currently unknown, not contradicted and not confirmed.** The measured Runs C/E/F clean data on gpt-5.5 do not speak to F72 because the comparator is on a different model. F72 as re-stated in R13 ("worker-side reads happen under minimal task; author-side crossing does not without task/clause pressure") remains the operative characterization, unrefuted and un-strengthened by R23.

## Session anchors

**R13 contam sessions inspected (this round):**
- N1 (R12 for R22): `ses_089162a4dffeiWgHMQ881UJOq3`
- H6 (R13 for R22): `ses_0782dfe02ffe2L0RUtoi9fDVcL`
- H9 (R13 for R22): `ses_073df183fffeQvInu5ry2Eq8QC`
- Run C (R13 for R23): `ses_082989c9bffemlrQJAKu17aqVv`
- Run E (R13 for R23): `ses_07c5fb651ffecud8NIEuS2VrFg`
- Run F (R13 for R23): `ses_0796c736dffeccAcVCwrHVv5e1`

**Clean sessions from R22/R23 (unchanged from those rounds):**
- N1-clean: `ses_05af58d0bffePz5JPm6H7VVdn1` (gpt-5.5/xhigh)
- H6-clean: `ses_05af58ceeffekYw6M7teJxI6c2` (gpt-5.5/xhigh)
- H9-clean: `ses_05af58cbeffe6PDg7A76CbJqpW` (gpt-5.5/xhigh)
- Run C-clean: `ses_059f6194dffeuVeG2NvK3SbvIf` (gpt-5.5/xhigh)
- Run E-clean: `ses_059f928a0ffeUmtsYcc76OIXZU` (gpt-5.5/xhigh)
- Run F-clean: `ses_059ff09c9ffeQHRhsXzzcfBj9o` (gpt-5.5/xhigh)

**Load-bearing rule:** any re-run write-up must include comparator inspection (contam session opened via `agent-tools opencode-pretty`, both crossings and totals measured directly) before quoting a delta. Copying counts from prior narrative language is the failure mode this round documents.
