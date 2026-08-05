# Round 40 — Content-first probe: what would reading tell you?

> **Direct predecessor: [`round-39.md`](./round-39.md).** R39 P5 emitted single-line `reason_against` per candidate — collapsing multi-axis weighing into one clause. R40 tests whether a content-first schema (`probable_contents` + `what_each_would_tell_you` + separate for/against arrays) surfaces the axes the R39 probe hid.

## What ran

**New probe** at `/tmp/r40/p5-probe.md`. Per-candidate schema:

```
{path, probable_contents[], what_each_would_tell_you[],
 reasons_against_reading_now[], reasons_for_reading_now[], verdict}
```

`what_each_would_tell_you` paired 1-to-1 with `probable_contents` by array index. Instructions:
- Content-first phrasing ("would clarify …", "would confirm …")
- Explicit "do not use decision language"
- Multi-reason enumeration in both `reasons_*` arrays

**Re-forked R39 baseline** (`ses_032279162ffe9MMjNrj9Kv7xDH`) at same 3 pre-decision points:
- L6 → `ses_032230d9effey7ghHfvtZ3oqrs` (kept L1-L5; msg fork)
- L12 → `ses_032214e48ffeekRzUyNJY5E5tV` (kept L1-L11)
- L16 → `ses_032063adfffeP02Ftti55BDVVL` (kept L1-L15)

Outputs at `/tmp/r40/p5-{L6,L12,L16}-stdout.jsonl` (25/46/29 candidate reads).

## Findings

### N1 — Old-worktree candidates emit (a)-shape utilities

6 old-worktree candidate entries across 3 rewinds (2/1/2 at L6/L12/L16, plus one L12 hybrid). Utility phrases carry (a)-shape content ("original unresolved task framing", "historical attempts and failures", "context for why the campaign restarted") in 10/13 utility items, mixed-a/b in 3/13, pure-b in 0/13. This is content the R39 aggregate `reason_against` slot never showed.

### N2 — `reasons_against` never engages the (a)-utility itself

All 6/6 candidates get drop verdicts. Rejection axes across all 6:
- Spec-inherited framing ("invalid/idea-only"): 6/6
- Adequacy-of-current-artifacts: 6/6
- Drift-language / stale-anchoring: 5/6 (drift-rule verbatim at L12/L16 scratchpad)
- Wasted-time / distraction: 3/6
- **Rejection that engages (a)-content**: 0/6

The model surfaces (a)-utilities in one slot and rejects them via spec-frame + adequacy in another slot, without any explicit "we already have that (a)-answer" or "the (a)-answer is not decision-relevant" clause.

## Composite mechanism at R40 grain

Reframed from R39:

- **Verdict layer** — task-message-inherited target (F119). Unchanged.
- **Consideration layer** — new visibility: (a)-utilities are present as probable content of old-worktree paths.
- **Justification layer** — aggregates to spec-frame + adequacy; does not engage the per-utility (a)-content.
- **Emission layer** — F62 unchanged; JSON slots bypass heading collapse.

## Later corrections

R41 (next round) surfaces per-utility grain that R40's aggregate reason_against still collapses. R43 diagnoses probe-bias sources that inflated candidate counts and biased verdicts.

R40 tagging error corrected in later turn: "(a)-utility across 10/13 items" conflated retrospective content-knowledge (from kimi cell reads) with ex-ante utility. Under strict ex-ante tagging (based only on what a rewind-point reasoner knows from path/filename/prior-mentions), only PROMPT.md carries pure ex-ante (a); scratchpad/decisions are ex-ante (b) — findings-reuse of prior worker notes and decision records. Under corrected tagging, R40's 10/13 count drops to 4 (a)-utility candidates across R40+R41, all PROMPT.md. See R41 findings for the corrected mechanism.

## Provenance

Retained at `/tmp/r40/` — probe file, runner script, fork-response JSONs, per-rewind stdout+stderr+text.json, extraction pipeline reproducible via `jq -r '.candidate_reads[] | select(.path | test("^/root/claude-config-work/")) …'` on the `text.json` files.
