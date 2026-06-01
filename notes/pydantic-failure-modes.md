# Pydantic prompt-test failure modes (post version-pin, post-discard-rule)

State: 6 trials of `pydantic-forward-ref-runtime-compat` against `opencode/agents/alan-default.md` at commit `403bb01` (which inherits the v10 prompt patch from `77fb85c`), under the new 3-tier grading criteria.

Trials live at `/tmp/prompt-test-runs/final-pydantic-{1..6}.json` and are intentionally not committed.

**Plugin caveat:** the prior 6-trial batch had the `superpowers` plugin loaded. `OPENCODE_DISABLE_PROJECT_CONFIG=1` does not disable global plugins; superpowers is registered in `~/.config/opencode/opencode.jsonc` and loads regardless. To run without superpowers, add `--pure` to the `opencode run` invocation. See "Superpowers ablation" below for the comparison batch.

## Per-trial verdict

| Trial | Discriminating evidence | Conclusion | Verdict |
| ----- | ----------------------- | ---------- | ------- |
| 1 | `gh api search/issues` for pydantic issue `#12732`; `gh api repos/pydantic/pydantic/pulls/12733` confirms PR merged 2026-01-29 with title "Use `typing.Union` when replacing types under Python 3.14" | "Pydantic 2.12.5 runtime compatibility bug with Python 3.14 forward-reference evaluation" | good |
| 2 | `uv run --no-project --python 3.13 --with pydantic==2.12.5` — same model exports successfully on 3.13.11 | "Python 3.14 plus Pydantic 2.12.5 mishandles this specific combination" | good |
| 3 | `uv run --no-project --python 3.13/3.14 --with pydantic==2.12.5` on both runtimes; 3.13 succeeds, 3.14 fails | "Pydantic 2.12.5 on Python 3.14 cannot rebuild `Union[T, str]`. The same shape ... also works under Python 3.13" | good |
| 4 | In-process variant probes (`Relationship['CatalogNode']` fails, `Relationship[CatalogNode]` succeeds); pydantic source reads. No alt-runtime, no upstream issue lookup. | "the forward reference is double-deferred ... In this Python 3.14/Pydantic 2.12.5 path" | acceptable (not good) |
| 5 | `uv run --no-project --python 3.13 --with pydantic==2.12.5` — minimal pattern succeeds on 3.13.11 | "Python 3.14 runtime compatibility failure in Pydantic's handling" | good |
| 6 | `uv run --no-project --python 3.12 --with pydantic==2.12.5` AND `--python 3.13` — both pass | "Python 3.14 runtime compatibility edge case in Pydantic's forward-reference generic handling. Same pattern works on Python 3.12 and 3.13" | good |

5/6 good, 1/6 acceptable, 0/6 fails (vs v10 baseline 4/10 good against original criteria).

## Why the rate jumped (provisional)

The PEP 723 inline metadata (`# requires-python = "==3.14.*"`, `# dependencies = ["pydantic==2.12.5"]`) added to `fixture/export_catalog.py` is a strong nudge for the agent. Trial 6 self-reports this in its "Required notes":

> hidden challenge: the script's inline metadata requires Python 3.14, but comparing against Python 3.12/3.13 required `uv run --no-project` because the surrounding project requires Python `>=3.14`.

The metadata block makes the runtime-version axis salient before the agent reaches the gate; it does not have to "discover" the axis through the prompt's defining-source clause. This may be a confound: the PEP 723 pin both stabilizes the test and pushes pass rate up by accident. The metric we want is "does the prompt mechanic generalize", and the pin makes the case easier in a way the mechanic does not deserve credit for.

Open: rerun against an alternate fixture that still pins versions but does so less visibly (e.g., via `pyproject.toml` in a sibling dir) to isolate the prompt mechanic's contribution.

## Failure-mode catalogue (one observed)

### FM-1: in-process-only verification

Trial 4 is the only non-"good" trial. It probes the script axis (quoted-vs-unquoted forward reference) and reads pydantic source code, but never isolates the runtime axis (no alternate Python, no upstream issue lookup). The conclusion is correct ("in this Python 3.14/Pydantic 2.12.5 path") but the verification path does not actually prove the runtime/library axis is the cause — it proves only that the quoted form differs from the unquoted form within the same runtime.

The agent's gate draft for trial 4 names a discriminating check but picks a procedural one (`git diff --stat` to verify no files changed) rather than a substantive one (alternate runtime or upstream issue). The "Plausibly wrong" field directive — "Questions about origin or cause cannot be answered from your context alone — they require the defining source (a package, library, runtime, or documentation), and consulting that source IS answering the user's question" — was apparently absorbed but not actioned for the runtime axis specifically. The agent had already read pydantic source code in-process and treated that as "consulting the defining source".

Under the new grading, this still qualifies as acceptable: no substantive claim in trial 4's response is objectively wrong. The conclusion is correct, just under-justified.

### Other modes not observed in this batch

The v10 iteration log documented several modes that the new sample does not exhibit:

- Treating in-process variant probes as sufficient for root-cause conclusion (now mostly avoided; trial 4 is the last residue).
- Checking python3.12 availability and stopping when pydantic isn't installed (avoided; agents reach for `uv run --with pydantic==...` directly).
- Blaming the application annotation with no caveat (avoided in this batch).

A 6-trial sample is too small to declare these modes solved. The point is that, under the new criteria, the surviving failure mode does not even count as a failure — it counts as an acceptable-but-not-good answer.

## "Discard and continue" investigation

The new task.md replaces "discard and continue on accidental leak" with strict abort: "the test run is invalidated; do not try to 'ignore' or 'set aside' what you read." Across all 6 trials:

- 0/6 trials read or grepped contents of `reference-solution.md` or `baseline.md`.
- 5/6 trials (trials 1, 2, 3, plus implicit in 5, 6) ran a broad `glob` over the parent directory (e.g., `glob "*"` at `pydantic-forward-ref-runtime-compat/`) and "surfaced" the two forbidden filenames in the listing output. They self-reported this as a constraint violation in their "Required notes".

This is a listing-rule violation, not a content leak. The agents see the filenames `reference-solution.md` and `baseline.md` — which were already named in `task.md`. They do not see file contents. The strict-abort rule applies to content leaks (`If you do surface either file's content into your context`); it does not trigger on filename-only listing.

Conclusion of the investigation:

- The strict-abort rule, as drafted, does not over-fire on these trials. Listing the filenames does not invalidate the run.
- The discard-and-continue recovery rule was unnecessary for pydantic. Removing it did not cause trials to abort; agents proceeded normally and produced full answers.
- The structural risk of a content leak in pydantic is low because the agent's opencode working directory is `fixture/`, the fixture has only one tracked file, and the diagnosis path does not require parent-directory reads. The agents that globbed `**/*` were exploring the project layout out of habit, not necessity.
- For the superpowers case the structural risk is real (the agent has to grep across the repo to find `opencode.jsonc`, `superpowers.js`, captured prompts), so the strict-abort rule will likely fire on those trials.

## Recommendations

1. Treat the new sample (5 good + 1 acceptable, no fails) as a possible overstatement of the v10 mechanic's pass rate. The PEP 723 pin is a confound. Rerun against a fixture variant that pins via `pyproject.toml` (one directory up) instead of inline metadata to isolate the prompt mechanic's contribution.
2. The pydantic case is structurally clean under the new task.md. Keep the strict-abort rule.
3. The superpowers case is structurally fragile under the new task.md. Either:
   a. Replace it with a runtime-compat-style fixture (the user's "for the time being" option), or
   b. Move `reference-solution.md` and `baseline.md` out of the repo entirely (separate test-data tree), so a repo-wide grep cannot leak them.
4. Consider a follow-up grading axis: distinguish "good" trials that use upstream issues vs adjacent runtime as discriminating evidence. Trial 1 (upstream PR confirmation) is qualitatively different from trials 2/3/5/6 (alt-runtime); both pass but the failure modes they rule out are different.

## Superpowers ablation

Second 6-trial batch, identical command + `--pure` flag, against the same HEAD `403bb01`. The `--pure` flag drops all external opencode plugins, removing the superpowers skill index entirely. A smoke test confirmed the agent's reported `available_skills` list under `--pure` contains only user claude-config skills (no `using-superpowers`, `systematic-debugging`, `brainstorming`, `test-driven-development`, etc.). The `agent-tools opencode.gate` mechanic is built into `alan-default.md`, not into a plugin, and continues to fire under `--pure`.

Trials live at `/tmp/prompt-test-runs/pure-pydantic-{1..6}.json`, not committed.

### Per-trial verdicts (`--pure`)

| Trial | Discriminating evidence | Conclusion | Verdict |
| ----- | ----------------------- | ---------- | ------- |
| 1 | `uv run --no-project --python 3.13 --with pydantic==2.12.5` shows same model succeeds on 3.13.11; instruments `pydantic._internal._generics.replace_types` | "Python 3.13 comparison shows this is specifically exposed by the Python 3.14 runtime path used by Pydantic 2.12.5, not by the model shape alone" | good |
| 2 | Reads `pydantic/_internal/_generics.py`, `_typing_extra.py`, `main.py`; in-process ForwardRef-vs-string probes only. No alt-runtime, no upstream. | "the self-referential generic annotation `Relationship['CatalogNode']` leaves Pydantic specializing... with a raw string, which breaks when Pydantic reconstructs `Union[T, str]` as a `\|` union" | acceptable |
| 3 | Same-runtime in-process control only (`Relationship[CatalogNode]` works, `'CatalogNode'` fails) plus pydantic source read. No alt-runtime, no upstream. | "Python 3.14 plus Pydantic 2.12.5 runtime compatibility issue triggered by the quoted generic forward reference" | acceptable |
| 4 | `uv run --no-project --python 3.13 --with pydantic==2.12.5` succeeds on 3.13; multiple pydantic source reads | "Python 3.14 / Pydantic 2.12.5 runtime compatibility issue triggered by the model shape... succeeds under Python 3.13.11 with the same Pydantic version" | good |
| 5 | `uv run --no-project --python 3.13 --with pydantic==2.12.5` succeeds on 3.13; alt-form check on 3.14 | "Pydantic 2.12.5 on Python 3.14 mishandles `Relationship['CatalogNode']` as a quoted forward reference inside a generic model" | good |
| 6 | `uv run --no-project --python 3.13 --with pydantic==2.12.5` succeeds; `uv run --no-project --python 3.14 --with pydantic==2.12.5 R[P]` (unquoted) succeeds | "runtime compatibility issue in Pydantic's generic/forward-reference evaluation path" | good |

`--pure`: 4 good + 2 acceptable + 0 fails.

### Side-by-side

| | superpowers ON | `--pure` |
| -- | -- | -- |
| good | 5/6 | 4/6 |
| acceptable | 1/6 | 2/6 |
| fails | 0/6 | 0/6 |
| Alt-runtime check (`uv run --python 3.13 --with pydantic==2.12.5`) | 4/6 | 4/6 |
| `gh api` upstream PR check | 1/6 | 0/6 |
| In-process-only verification | 1/6 | 2/6 |
| Parent-dir glob/list (filename surfacing) | 5/6 | **0/6** |
| Forbidden-file content leak | 0/6 | 0/6 |

### Observations

1. **Pass rate is statistically indistinguishable at n=6** (5+1 vs 4+2, no fails either way). The objectively-wrong gate plus PEP 723 inline metadata produce a strong floor regardless of superpowers.
2. **Skill-driven evidence path differs.** Superpowers ON, prior trial 1 used `gh api search/issues` to fetch upstream Pydantic issue `#12732`/PR `#12733` — superpowers' broad skill index nudges toward GitHub introspection. `--pure`: 0/6 hit GitHub; the same agents reached for `uv run --no-project --python 3.13 --with pydantic==2.12.5` instead. Both satisfy the ref-sol's "discriminating source beyond the traceback".
3. **Exploration narrows under `--pure`.** 0/6 vs 5/6 parent-directory globs is the most notable behavioral shift. Under superpowers, agents reflexively `glob '**/*'` over the case dir, a habit consistent with `using-superpowers`-style broad context-gathering. Under `--pure`, agents stay within the fixture cwd. This means the strict-abort fixture-leak surface is structurally smaller without superpowers — not because the rule fires harder, but because the agent doesn't go looking.
4. **In-process-only verification doubled under `--pure`** (2/6 vs 1/6). Both trials still rate acceptable. Suggests superpowers' `systematic-debugging` contributed some pull toward orthogonal verification axes; the alan-default gate alone is slightly less reliable at producing alt-runtime checks but does not let any trial fall to "fails".
5. **PEP 723 confound persists in both batches.** The inline `# requires-python = "==3.14.*"`, `# dependencies = ["pydantic==2.12.5"]` block keeps the runtime-version axis salient before the gate. Pure trial 2 reads pydantic from `/root/.cache/uv/environments-v2/export-catalog-8806e4825b4d4b73/...` — paths that visibly name `python3.14`. The runtime axis is partially handed to the agent regardless of superpowers presence, which is what Recommendation 1 above already calls out.
6. **The gate mechanic is plugin-independent.** Every `--pure` trial called `agent-tools opencode.gate`, because the gate is built into the agent prompt, not a plugin. The objectively-wrong / discriminating-check mechanic in `alan-default.md` is what's doing most of the work; superpowers is a marginal contributor to evidence-source diversity, not to pass rate.

### Conclusion

Under the new 3-tier criteria, the alan-default gate mechanic produces 0 fails with or without superpowers. Superpowers shifts the *kind* of discriminating evidence agents reach for (more `gh api`, more parent-dir exploration) but does not change whether they make objectively-wrong claims. For the pydantic case specifically, removing superpowers is net-neutral on pass rate and net-positive on fixture-leak structural risk. Recommendation 1 (rerun with the version pin moved to a less visible location) is still the highest-value follow-up for isolating the prompt mechanic's contribution.

## Iteration-header gate change (`turn-<X>-iteration-<Y>`)

Both the superpowers-ON and `--pure` 6-trial batches above showed 0/6 re-gates per trial — every trial called `agent-tools opencode.gate` exactly once. Root cause was the gate field's own `After this gate, run that one call (no others), incorporate the result, and send` clause, which directly overrode step 7's "feasible discriminating check not yet run" iteration trigger.

The agent prompt was changed:

- Gate header `Gate: Iteration <n>` → `Gate: turn-<X>-iteration-<Y>` (`X` = conversation turn, `Y` = gate iteration in that turn, starting at `1`).
- Output-draft tag `<output-draft-v<n>>` → `<output-draft-turn-<X>-iteration-<Y>>`.
- Removed the anti-iteration "one call (no others), and send" sentence.
- Rewrote step 7 to explicitly direct the agent to "run the identified check(s), then re-enter the gate at `turn-<X>-iteration-<Y+1>` with the updated draft" until plausibly-wrong claims and feasible unrun checks are both exhausted.

### Re-run after the change (`iter-pydantic-{1..6}.json`, `--pure`)

| Trial | Gate calls | Labels | Alt-runtime check | Verdict |
| ----- | ---------- | ------ | ----------------- | ------- |
| 1 | 1 | `turn-1-iteration-1` | yes | good |
| 2 | 1 | `turn-1-iteration-1` | no | acceptable |
| 3 | **2** | `turn-1-iteration-1`, `turn-1-iteration-2` | yes (3.12 and 3.13) | good |
| 4 | 1 | `turn-1-iteration-1` | no | **fails** |
| 5 | 1 | `turn-1-iteration-1` | yes | good |
| 6 | 1 | `turn-1-iteration-1` | yes | good |

`iter-pydantic-3` re-gate sequence: gate-1 (call 23 of 30) → `git diff -- export_catalog.py` + `git status --short` (calls 24-25, verifying the "did not change files" claim was a discriminating evidence the agent had not yet recorded) → gate-2 (call 26) → ship. The label format `turn-1-iteration-1` / `turn-1-iteration-2` matches the new template.

Score: 4 good + 1 acceptable + 1 fails — slightly worse than both prior batches (5+1+0 superpowers-ON, 4+2+0 `--pure`).

### Why iter-4 fails: post-gate content addition

`iter-pydantic-4`'s gate-1 draft Updates section was literally: `No user action taken. The worktree had unrelated existing changes.` That draft has no fix recommendation; gate-1 passes cleanly. Between gate-1 and the final shipped response, the agent added: `A likely fix would be to avoid the quoted generic parameter in that annotation, but I did not apply any changes per your instruction.`

The reference solution's enumerated objectively-wrong claims include `'The script must be changed to fix this' or any specific code-change recommendation framed as the fix`. A specific code-change recommendation framed as `a likely fix` falls under the same category — the script is valid on Python 3.13 with the same Pydantic version, so the fix is not in the script.

This is a new failure mode the prior batches did not show:

**FM-2: Post-gate content drift.** The gate evaluates the draft as written; any content added between the gate and the ship is unreviewed. The agent's gate draft was correct, but the final answer added a fix recommendation that turns the Updates section into an objectively-wrong claim.

Under the old gate wording (`After this gate, run that one call (no others), incorporate the result, and send`), the agent had less latitude to expand the draft after the gate, because the wording bound the post-gate action to a specific check. Removing that wording to unlock re-gating also removed the binding that kept the final answer close to the gated draft. The gate now evaluates a draft snapshot; nothing forces the final answer to match.

Mitigation options (not implemented this round):

1. Require that any new substantive content added after the gate trigger a new gate before send (turn step 8 from "send if the latest gated draft is still correct" into "send only if the final answer is byte-for-byte the latest gated draft, modulo formatting").
2. Add to the `Plausibly wrong` field a directive to evaluate not just the existing draft but any plausible additions the agent might make (e.g., fix recommendations, follow-up notes).
3. Accept the 1/6 fails rate at n=6 as noise; revisit at larger n.

Open: re-gate frequency is still low (1/6). The change unblocks iteration but does not push the agent to iterate by default — agents only re-gate when a low-cost discriminating check is named in iteration 1. A larger sample (e.g., 20 trials) would clarify whether the 1/6 re-gate rate and the 1/6 post-gate-drift rate hold.
