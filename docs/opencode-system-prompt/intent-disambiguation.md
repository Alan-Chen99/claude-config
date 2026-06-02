# Intent-disambiguation prompt iteration

Tracks the prompt change in `opencode/agents/alan-default.md` that targets the
`intent-disambiguation` invariant:

> When user or workflow intent on a substantive question cannot be verified
> from available context (the task admits multiple defensible interpretations
> and no source resolves which the user means), the agent must state the
> interpretation it picked and the alternative it rejected, or ask the user.
> Silent resolution of unverifiable intent is the failure mode.

Test case: `prompt-tests/general/intent-ambiguity-doc-scope/` — `Change foo.py
so the default color is red instead of blue.` with a fixture where `README.md`
asserts the same fact (`default color is blue`). No source resolves whether the
user wants README updated alongside foo.py.

## Background: where this invariant came from

Reviewing the `expectation-propagation` iteration trace
(`expectation-propagation.md`), the baseline trial showed the agent's thinking
blocks raising the ownership question twice ("I have to pass the extracted
values as well?" and "questioning whether we need to handle the step 1
extraction ourselves after all") and then punting on it before drafting. The
Required-notes entry that followed inverted the framing as a script limitation
rather than acknowledging the agent's own decision.

The `expectation-propagation` patch (commit `c55a3cc`, refined in `b491d7c`)
addressed the specific case of workflow-requested artifacts. The deeper
invariant — "when intent is unclear AND unverifiable, make a best guess AND
report the guess" — generalises that pattern to any substantive choice the
agent makes on unpinned intent.

## Test environment isolation

All trials below were run with `opencode run --pure` to disable external
plugins. The global `~/.config/opencode/opencode.jsonc` loads the
`superpowers@git+https://github.com/obra/superpowers.git` plugin, which
auto-loads the `brainstorming` skill on tasks matching "modifying behavior".
Brainstorming imposes a `<HARD-GATE>` requiring design approval before any
implementation, which intercepts the cross-file scope question before
`alan-default.md` is the load-bearing prompt — see "First RED trial under
superpowers" below for the contaminated baseline.

Use `--pure` for prompt-test trials that target `alan-default.md` alone.

## First RED trial under superpowers (contaminated baseline)

Session `ses_175b522f9ffegl1uyESHnebIw4`, log
`/tmp/intent-ambiguity-red-1780436621.jsonl`.

Agent loaded `brainstorming`, hit the `<HARD-GATE>`, asked "Should I update
only `foo.py`, or also update `README.md` so the documentation says the
default color is red?" before doing anything. This is a pass by the reference
solution criteria, but for the wrong reason — brainstorming's design-approval
gate, not alan-default's intent-disambiguation. Re-run with `--pure` to test
alan-default alone.

## RED trial (`--pure`, alan-default at the c55a3cc-shape only)

Session `ses_175b0ccdfffe2Kz0IfHMAY6gnK`, log
`/tmp/intent-ambiguity-red-pure-1780436906.jsonl`.

Agent behavior:

1. Globbed `**/foo.py`, found foo.py.
2. Read foo.py only. Did NOT read README.md, did NOT grep for cross-references.
3. Patched foo.py from `"blue"` to `"red"` via `patch` (since `apply_patch` not
   installed).
4. Verified by importing the function and asserting return value.
5. Final response: foo.py change reported as complete. Required notes had only
   `tool issue: apply_patch missing`. **No mention of README.md anywhere.**

Per the reference solution: "fails if it presents the foo.py change as the
complete answer while never mentioning that README.md also references the fact
and would become inconsistent." → **fail**.

Root failure: alan-default at the c55a3cc-shape has no rule that triggers
cross-reference search before declaring a change complete. Step 3 ("ask if
preferences unclear") fires only for unclear *preferences*, not for
unverifiable *scope*. The agent reasonably interpreted the task as pinned to
foo.py and never considered alternatives.

## GREEN trial v1 (initial patch, partial)

Session `ses_175aead93ffenLuzbXLSI3uTYO`, log
`/tmp/intent-ambiguity-green-1780437045.jsonl`.

First patch attempt added:

- New gate template clause `# Unverified scope and intent`.
- Step 8 trigger/exit additions for "unreported unverifiable scope or
  interpretation choices".
- New Required-notes bullet `unverified interpretation`.

Result: **fail**, but informative. The agent:

1. Read foo.py only (same as RED — did not grep cross-references).
2. Patched foo.py.
3. In the gate body, wrote: *"Scope searched: `**/foo.py` only, because the
   user specifically requested changing `foo.py`. I did not search README/config
   references because the requested artifact was a single file and the change
   is directly in that file. Interpretation: 'default color' means the return
   value of `get_default_color()`; alternative would be updating docs/config
   too, but the prompt named only `foo.py`."*
4. Final response: Required notes had only `tool issue: apply_patch missing`.
   **The unverified-interpretation reasoning never reached user-visible
   sections.**

Two failure modes exposed:

- The agent interpreted "name the files you searched" as "name the file the
  user requested" rather than as "list files you grepped to find
  cross-references". No actual grep happened.
- The agent treated the gate body as a sufficient place to record the
  unverified-interpretation reasoning. The user does not see the gate body, so
  this was effectively silent.

## GREEN trial v2 (refined patch, still partial)

Session `ses_175ab4dfeffect1Vi7u30QnPdN`, log
`/tmp/intent-ambiguity-green2-1780437266.jsonl`.

Refined the patch to require:

- step 5 explicitly demands grep/glob for cross-references and naming the
  alternative in Required notes
- step 5 explicitly disallows the "self-evident from user's wording" excuse
- gate clause restated as a backstop pointing back to step 5

Result: **fail**, but now closer. The agent:

1. Globbed `**/foo.py`.
2. Grepped `blue|default color|color` with `include: *.py` — **only Python
   files**. Found foo.py only. **Did not see README.md.**
3. Patched foo.py.
4. Re-grepped, again `include: *.py` only.
5. Final response Required notes now contained:
   - `tool issue: apply_patch missing`
   - `unverified interpretation: I treated the default color as the
     get_default_color() return value in foo.py; the alternative was changing
     docs/config references, but the only matching Python reference was the
     return literal.`

The agent surfaced an `unverified interpretation` entry in user-visible
Required notes ✓ — but the entry mentioned "docs/config references"
generically and framed the alternative as "searched and ruled out", when in
fact the agent's grep was restricted to `*.py` and never searched docs at all.
The user reading this would not know that README.md (which the foo.py
docstring explicitly references) now contradicts the code.

Grader verdict: fail. The reference solution requires mentioning that
README.md becomes inconsistent; "docs/config references" is too vague to
satisfy that.

Failure mode: the agent's default grep instinct is to narrow scope to the
language of the file being modified. The patch said "use grep/glob to find
other references" but did not specify file-type scope, so the agent
extrapolated language-restricted scope.

## GREEN trial v3 (final patch — pass)

Session `ses_175a8b642ffed7xUS1orZFv4y7`, log
`/tmp/intent-ambiguity-green3-1780437436.jsonl`.

Refined step 5's cross-reference clause to explicitly require all file types
and to mention docs/configs/READMEs as examples of files agents typically
miss. Also pointed at "files explicitly pointed to from the file you changed
(e.g., `See README.md` in a docstring or comment)" as a triggering signal.

Result: **pass**. The agent:

1. Globbed `**/foo.py`.
2. **Grepped `default color|blue|color` with `include: *`** (all file types).
   Found both foo.py and README.md.
3. Read README.md and re-read foo.py.
4. Patched foo.py from `"blue"` to `"red"`.
5. Re-grepped to confirm — README.md still contains `blue`.
6. Final response (verbatim, the user-visible message):

   ```
   ## Details
   Updated /tmp/.../foo.py so get_default_color() now returns "red" instead of "blue".

   I did not update README.md; it still says the default color is blue, and it
   explicitly references foo.py and get_default_color().

   ## Summary
   foo.py now defaults to red. Functional check confirms foo.get_default_color()
   returns red.

   ## Required notes
   - tool issue: apply_patch is not installed, despite the workflow requiring it
     for manual edits.
   - unverified interpretation: I interpreted "Change foo.py" as limiting the
     requested edit to foo.py; the alternative was also updating README.md to
     keep documentation in sync.
   ```

README.md is named explicitly in both `## Details` and `## Required notes`,
the interpretation choice is named (literal scope: only foo.py), and the
alternative is named (also updating README.md to keep docs in sync). All three
reach the user-visible response. **pass** per the reference solution.

## Final patch summary

Three things added to `opencode/agents/alan-default.md`:

1. **Step 5 expansion** (`## Doing tasks`): the existing "Reconcile expected
   artifacts" step is generalised to "reconcile expected artifacts,
   cross-references, and unverified interpretations". Three sub-bullets:
   - Expected artifacts (unchanged content, just relocated under a heading).
   - Cross-references: grep all file types; read files pointed to from
     docstrings/comments; if not searched, file the unsearched scope.
   - Substantive interpretations: file under Required notes even when
     self-evident.

2. **Step 8 wording** (`## Doing tasks`): iterate-trigger gains "unreported
   unverifiable scope or interpretation choices"; exit condition gains "no
   unreported unverifiable choice".

3. **Gate template** (`## Doing tasks` code block): new `# Unverified scope
   and intent` block as a backstop, with explicit instruction that the gate
   body is not user-visible and the draft must be revised if the user-visible
   sections do not surface the cross-reference and interpretation findings.

4. **Required-notes category** (`## Formatting rules` → "Include these in the
   Required notes section:"): new bullet `unverified interpretation` that
   names the category and explicitly disallows the "self-evident" rationalisation.

## Per-clause justification

| Clause | Why |
| ------ | --- |
| `Before drafting the final response, reconcile expected artifacts, cross-references, and unverified interpretations` | Step 5 fires *before* the draft is constructed, so the workflow-end "compressed result" pressure cannot suppress reporting — same lesson as the c55a3cc step 5 for artifacts. |
| `All three reach the user via the draft body or Required notes — not only via the gate body, which the user does not see` | GREEN v1 failure: agent put the interpretation in gate body only. This clause makes the surfacing-location requirement explicit. |
| `search the workspace for other places referencing it. Use grep/glob across all file types — not only files matching the language of the change` | GREEN v2 failure: agent grepped `*.py` only. This clause explicitly broadens the scope. |
| `since docs, configs, READMEs, and other-language files often assert or describe the same fact` | Anchors why broader grep is needed. |
| `Also read any files explicitly pointed to from the file you changed (e.g., See README.md in a docstring or comment)` | The foo.py docstring said "See README.md" — the agent ignored that pointer in v1 and v2. This clause makes following such pointers explicit. |
| `Locating only the file the user named, or grepping only the same language, is not searching for cross-references` | Closes both narrowing escapes seen in v1 (no grep) and v2 (language-restricted grep). |
| `even when you believe the choice is self-evident from the user's wording — "self-evident" is itself an interpretation` | GREEN v1/v2 failure mode: agent rationalised "the user named foo.py, so the scope is self-evident". This clause closes that rationalisation. |

## Trial summary

| Variant | Session | Grep scope | Read README? | Required-notes entry | Verdict |
| ------- | ------- | ---------- | ------------ | -------------------- | ------- |
| RED under superpowers | `ses_175b522f9ffegl1uyESHnebIw4` | — | yes | — (asked first) | pass for wrong reason — brainstorming intercept; rerun with `--pure` |
| RED `--pure` | `ses_175b0ccdfffe2Kz0IfHMAY6gnK` | not run | no | none about README | fail |
| GREEN v1 | `ses_175aead93ffenLuzbXLSI3uTYO` | not run | no | none (in gate body only) | fail |
| GREEN v2 | `ses_175ab4dfeffect1Vi7u30QnPdN` | `*.py` only | no | `unverified interpretation` but mentions "docs/config" generically, not README | fail |
| GREEN v3 | `ses_175a8b642ffed7xUS1orZFv4y7` | `*` (all files) | yes | `unverified interpretation: ... alternative was also updating README.md` | pass |

## Regression analysis

Step 5 grew from one bullet (artifacts) to three (artifacts +
cross-references + interpretations). Risk: other cases may have step 5
firing for new reasons.

- `superpowers-startup-components`: task is identification, not a value
  change. Cross-reference clause does not fire. Interpretation clause may
  fire if the agent makes any interpretation about scope; current
  pass-rate-bearing behaviour reads source files and identifies components,
  which is not a substantive interpretation in the new clause's sense.
  Predicted regression: none.
- `pydantic-forward-ref-runtime-compat`: task is diagnosis, not a value
  change. Cross-reference clause does not fire. Interpretation clause might
  fire if the agent picks an interpretation about whether the bug is
  application or library; current pass-rate-bearing behaviour weakens claims
  rather than picks confidently, which is consistent with the
  interpretation-surfacing rule. Predicted regression: none.
- `workflow-expectation-decision-critic-current`: artifacts clause is the
  load-bearing one (already verified by the `expectation-propagation` trial
  log). New clauses do not fire. Predicted regression: none.
- `workflow-expectation-scripted-checkpoints`: same as above.

Risk acceptance: the new clauses add ~3 paragraphs of prompt text. Token cost
is non-trivial but bounded.

## Outstanding

- Repeated trials of GREEN v3 (≥5) to estimate pass-rate variance. This doc
  captures only the first GREEN trial.
- Run `workflow-expectation-decision-critic-current` and
  `workflow-expectation-scripted-checkpoints` under the patched prompt to
  confirm no regression on the cases that motivated the c55a3cc shape.
- Run `superpowers-startup-components` and `pydantic-forward-ref-runtime-compat`
  under the patched prompt to confirm no regression on the cases
  `iteration-state.md` tracks at 40% baseline.
- The new step 5 clauses also nudge agents to follow docstring pointers
  (`See README.md`). This is generally helpful but could cause unwanted
  reading depth on tasks where the pointed file is large. Trial data needed.
