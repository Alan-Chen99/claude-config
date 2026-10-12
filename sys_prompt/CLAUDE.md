# sys_prompt/

Full replacement system prompts for `--system-prompt-file`; background and forked sessions run
without them (`docs/background-sessions.md`). A Read of any file here attaches this whole file, so
it holds only the index and the edit policy.

## Files

| File | What | When to read |
| --- | --- | --- |
| `alan-default-next.md` | The prompt `scripts/claude.sh` loads, forked from cc's lean body | Editing the prompt |
| `alan-default.md` | An earlier prompt, forked from cc's legacy body; no script loads it | - |
| `README.md` | Why each line is there — claim, hypothesis, retirement condition — and the ledger of wordings measured and not shipped | Before changing, deleting or restoring a line; before measuring a wording |

Rebasing on a Claude Code release: `docs/prompt-rebase.md`.

## Editing the prompt

Every token of the prompt is spent on every request of every session. After any edit:

1. Re-read the passage and cut a word. Repeat until cutting another would lose meaning.
2. Re-read the section. If a neighbouring line now says the same thing, delete one: two wordings
   leave nothing saying which governs.
3. Name the behaviour that changes without the line. If you cannot, drop the line.

The prompt states the rule. What dates it — versions, issue links, dates, measurements, the
reasoning — goes in `README.md` or in the doc of a mechanism the line names. A `README.md`
section quotes the text it explains in a backticked literal in its `###` heading, and gives the
claim, the hypothesis, and the retirement condition: the observation that would end the line,
naming the `prompt-tests/general/` case where it is made. Run narrative stays in the commit; a
wording measured and not shipped is a ledger row. `scripts/check-prompt-rationale.sh` fails on a
section quoting no live prompt text, and the prompt-tests skill deletes a case `README.md` stops
naming.

Measure before and after: `uv run doc-budget sys_prompt/alan-default-next.md` is the figure CI
gates; `agent-tools count-tokens --api --file sys_prompt/alan-default-next.md` is Claude context,
about 1.5x that and a different unit.

A passage copied from cc's prompt is pinned by `scripts/check-prompt-upstream.py`; a failing pin
is a decision — adopt upstream's wording or record a divergence in `docs/prompt-rebase.md` — not
an edit to the script. Strings `agent-tools` emits that the prompt quotes are pinned by
`scripts/check-prompt-coupling.sh`; `agent-tools claude` refuses to launch while it fails.

Load `prompt-engineer-v2` before an edit. Two things it does not carry, which no case exercises
and review tends to read as wording:

- **Force.** How widely an imperative binds is itself a claim: that the failure is frequent and
  costly enough to be worth the compliance cost everywhere it reaches. Two incidents support a
  caution; a requirement needs a rate and a cost.
- **Exceptions.** Before writing one, answer how much of the forbidden space it readmits: breadth
  is its extension, not how narrow its wording sounds. Over-applying a prohibition yields a duller
  artifact, over-applying a permission skips the work and ships a wrong answer, so the exception
  is the half that repays the closer reading.
