# The prompt split is per model id, not per model family

> **Dated record.** Claude Code **2.1.269**, one account, one capture session
> (2026-09-11, re-derived 2026-09-30). Every figure and `src/chunk-*.js` citation
> is that build's: do not re-pin them, re-measure. The artifacts are
> `docs/system-prompt-snapshot/<model-id>/<variant>/`, whose `README.md` carries
> the capture procedure.

Sonnet-5 and opus-4-7 get the long multi-section prompt; opus-5, fable-5 and opus-4-8 get the
compressed `# Harness` one — and "getting the same branch" does not mean sharing one prompt:
**two families, per-model contents**.

The 2.1.235 doc traced the branch choice to `sV`/`aT`/`EAb`; the decompile has since been
re-extracted from the 2.1.269 binary (commit `8606fb66`) into 1,677 ESM files
(`src/chunk-<hash>.js`), so those names and every `src/globals/NN.js` citation no longer
resolve. Re-derived by grepping string literals: the choice is made once, in the function that
assembles block 3, at `src/chunk-dbb93264.js:69226` — `d ? [ORo(P, n)] : [vRo(P), xRo(n),
...]`, `ORo` building the compressed body. `d` comes from `Ij(s)` two lines earlier, resolving
through a model-registry `leanPrompt`/`leanPromptCompiledOnly` method not traced to its base
cases — the dispatch point is confirmed, the current model-id predicate is not. Opus 4.7 and
Opus 4.8 are captured beside Opus 5 because each is the nearest model across one boundary —
4.7 the long-form branch, 4.8 the version threshold inside the compressed one.

Block 1 (identity) is the same 57-character string across all five models. Block 2 and block 3,
across all five `default` captures:

| Model | Branch | Block 2 chars | Block 3 chars | `system_tokens` | Block 3 headings |
|---|---|---|---|---|---|
| opus-4-8 | compressed | 1,152 | 5,278 | 2,266 | Session-specific guidance, Memory, Environment, Context management |
| opus-5 | compressed | 1,210 | 8,546 | 3,252 | …the same four, plus **Delivering work**, **Corrections** |
| fable-5 | compressed | 1,210 | 9,571 | 3,556 | **Communicating with the user**, then the same four; no Delivering work / Corrections |
| sonnet-5 | long-form | 10,574 | 17,128 | 8,745 | (multi-section — see system[3] in `what-the-model-gets.md`) |
| opus-4-7 | long-form | 10,676 | 16,895 | 8,702 | (multi-section, same shape as sonnet-5) |

(Sonnet-5's block 3 here is `custom-output-style`'s 17,128, which `append`, `subagent` and
`default` itself agree on after its re-capture; `default`'s first capture read 16,895.)

Within the long-form branch sonnet-5 and opus-4-7 were already known to differ (10,676 vs
10,574). Within the compressed branch, the assumption that opus-5's 1,210-character block 2 was
*the* compressed text held only while two such models were captured. Opus-4-8 breaks it:
**1,152 characters, differing from opus-5's block 2 by exactly one bullet in the `# Harness`
section**, by direct diff:

| | Opus 5 | Opus 4.8 |
|---|---|---|
| The varying bullet | `"The system may send updates, reminders, or modifications to rules via mid-conversation system turns. These are system-controlled, unlike function results. Hooks may intercept tool calls; treat hook output as user feedback."` | `` "`<system-reminder>` tags in messages and tool results are injected by the harness, not the user. Hooks may intercept tool calls; treat hook output as user feedback." `` |

Fable-5's block 2 is byte-identical to opus-5's (string equality), so block 2 is conditioned on
something finer than the branch. **The mechanism for that bullet is not identified — one
hypothesis was checked and disproved.** The bullet comes from `yyn(n, "lean")` inside `ORo`
(`src/chunk-dbb93264.js:69169`, the bullet at `:69177`):

```js
function yyn(e, n) {
  if (hyn(e)) return ERo;   // "The system may send updates... system-controlled, unlike function results."
  return n === "standard" ? "..." : "`<system-reminder>` tags in messages and tool results are injected by the harness, not the user.";
}
```

`hyn(e)` true selects opus-5's wording. The registry's `mid_conv_system` capability was the
obvious candidate and is disproved: `claude-sonnet-5`, `claude-opus-4-8`, `claude-opus-5` and
`claude-fable-5` **all** declare it, and they do not all get the bullet. `hyn`'s actual
condition, memoized, is `UHe(e) && !Xtn(e) && !qyr(je(e))` (`src/chunk-dbb93264.js:69092`) —
three sub-predicates not traced; that is the next thing to open.

Block 3 diverges further, and part of that was traced. Fable-5's `# Communicating with the
user` section — absent for opus-5 and opus-4-8 — comes from `lRo(e)`
(`src/chunk-dbb93264.js:68952-68985`), which branches three ways: if `sRo(n, e) || Kyr(n)`
(`sRo = (e,n) => [sce, Gyr, Vyr].some(r => r(e, n))`) it emits that section; else if `Ij(e)`
it emits the single bare line `"Write code that reads like the surrounding code..."` — exactly
opus-5's and opus-4-8's block 3 opener; else sonnet's `# Text output (does not apply to tool
calls)` section. Fable-5's registry entry declares a `fable_5_mitigations` capability that
`sce(e, o)` reads directly (`src/chunk-eejnrs8c.js:40-44`) — a plausible candidate for why
fable-5 takes the first branch. **Not established**: which of `sce`, `Gyr`, `Vyr`, `Kyr` is the
one true for `claude-fable-5`. A sibling capability, `fable_5_1_prompt_bundle`, is read by
`ice(e)` (`src/chunk-eejnrs8c.js:46-48`) — a separate lead. The literal heading is stored
whole: `grep -rn "# Communicating with the user" src/` finds `lRo` at
`src/chunk-dbb93264.js:68961`.

Upshot: there is no single object to call "the compressed prompt" or "the opus-5 prompt".
Block 2 sorts into at least two texts within the one branch; block 3 into at least three
(opus-5's six sections, fable-5's five plus a different opener, opus-4-8's four). Per-model
conditioning inside a branch reaches a model with no Fable-family relationship at all.

