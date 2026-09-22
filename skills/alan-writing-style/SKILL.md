---
name: alan-writing-style
description: Write, rewrite or check prose as Alan -- docs, notes, specs, status reports, messages, agent instructions, in any domain. Use only when invoked by the user or a workflow. Not for code, other people's voices, or detector evasion.
---

# Alan writing style

Same content, Alan's shape and sentences. In practice the agent writes first and Alan edits, so the main job is rewrite. The rules apply to any domain and any content type; the illustrations are his own chat sentences, typos included, and show the rule, not a template to fill.

## Jobs

- Rewrite. Input is agent-written text. Output is the same content as Alan would write it. Text given -> this job.
- Write. Input is content (facts, a decision, findings). Output is text.
- Check. Input is text. Output is a list only, one item per deviation: `quote -> rule -> fix`. No rewrite. "check" or "review" in the request -> this job.

Rewrite and write output the text and nothing else: no preamble, no list of what changed. Check outputs the list and nothing else.

## Registers

- `doc` (default): README, notes, specs, status reports, anything read later by someone else. Capitalized sentences, no contractions, no typos.
- `chat`: messages Alan would type himself (prompts, telegram, quick replies). Allowed on top of `doc`: lowercase sentence starts, lowercase `i`, contractions without apostrophes (`dont`, `thats`, `its`). Nothing else changes.
- `prompt`: PROMPT.md, CLAUDE.md rules, agent instructions. Genre features allowed: MUST/SHOULD/NOT in caps, imperatives, `[idea]` and other bracket markers, `<request>` wrappers. Sentence rules still apply.

Out of scope: detector evasion (no prompting method crosses the human threshold, only fine-tuning does), code, other people's voices (`copy-writing-style`).

## Shape

Mainly `doc`; a chat critique follows sentence rule 8. Ordered by how reliably Alan does it.

1. The point first. The first sentence is the goal, the decision, or the finding. No scene-setting (the reader knows the system), no summary sentence in front of the content it summarizes, no "this document describes".
2. Labelled parts. A paragraph opens with a short label and a colon, then the content; the label names whatever the part is (a result, an open question, a tradeoff, a note). A bullet opens with a 1-3 word name for the item, a period, then the gloss. `-` bullets in docs; inline `(1) (2)` is chat.
   > currently: lots of specifics that may not fit particular tasks.
   > tension: proxmiity vs dulpicition. ex: duplicat docs is better for agent but often goes out-of-sync
3. Quote, do not describe. When the text is about an artifact (a rule, an output, a message, a source), the artifact's own words go in a `>` block; cut with `...` and a parenthetical saying what was cut. Paraphrase of an artifact is the first thing he replaces. Quoting can make the result longer than the draft.
4. How you know, in the sentence. A short clause or parenthetical names the evidence kind: measured, counted, from source, by impression, not sure. A doc states no confidence it does not have, and no number unless the number is the finding.
5. What survives a cut. Keep: the decision, the tradeoff and the alternative rejected, how you know, the purpose (once, after the thing it explains). Cut: mechanism the reader does not need to act on, restatement, transitions, anything the reader already knows.
6. Headers are 2-4 word noun phrases naming the topic or property. Not a question, not a sentence, not "Why X and not Y". Not one per paragraph.

## Sentences, all registers

1. ` -- ` (spaced double hyphen), single, rightward: the part after explains or qualifies the part before. Never an em dash. One per sentence; a ` -- ... -- ` pair as parentheses is rare.
   > i would look at it this way -- such a skill is _built_/_engineered_, not _measured_.
2. Explanatory colon, lowercase continuation: claim, colon, the thing that makes it concrete.
   > rare conditional rule: not worth.
   > this breaks a new invairnt category: decision without reason.
3. Coined or borrowed terms in "double quotes" the first time, bare after. Quotes name a thing; they do not emphasize.
   > perhaps it make sense to explain a "growing doc" model/mindset.
   > there are infintely many "implicit expectations".
4. Hedges only where the sentence is opinion, and naming their kind (`i think`, `imo`, `not objective, but`, `not sure if`, `potentially?`). None in a factual sentence.
   > this is not objective, but i really feel that i "ended up doing better" by "reading thinking blocks"
   > im not sure if thats true or not, but i thienk we should not assume its not true
5. Causation by `so`, `because`, `which is why`, or plain juxtaposition. Never `however`, `therefore`, `thus`, `moreover`, `additionally`, `furthermore`, `in other words`.
   > which is why i was purposing shifting the spec, to be prompt-first.
6. Verdict fragments beside long clause chains: a 2-6 word sentence next to a 30-word one, not three medium sentences in a row.
   > this misses the point.
   > sometimes is better.
7. `_word_` on the contrastive word, the one the sentence turns on (`**word**` in chat too). Bold otherwise only on the single load-bearing constraint in the whole text.
   > the tutor operats in _idea space_, not _code space_.
   > agent make judgment runtime on **context** rather than **rules**.
8. Critique alternates the quoted fragment and the verdict on it; each verdict is one short sentence; the failure it causes follows. No praise first, no softening after.
   ```md
   this misses the point.

   > no static reference found; reflection and dynamic dispatch not checked

   this is bad becuase it imply a hidden clause

   > all references are either [static, reflection, dynamic]
   ```
9. `rather than` for contrast. `ex:` for examples in chat, `example:` in docs; never `e.g.`.
   > use "the right sdk" rather than "brute force parsing".
   > (ex: all facts verified)
10. Words he uses when the concept is there: tradeoff, framing, failure mode, invariant, overfit, sanity check, root cause, structural, bigger picture. Keep them where the concept is present; do not add them where it is not, and do not replace them with synonyms. Never: crucial, robust, leverage, comprehensive, delve, nuanced, landscape, seamless, navigate, journey, testament.
11. Never: `!`, curly quotes, triads (`adj, adj, and adj`), not-X-but-Y as rhetoric, aphorism, metaphor, chiasmus, closing summary, `In summary`, `Overall`.

## Errors

- Never introduce typos or grammar errors, in any register. Alan's error rate is a property of the medium, not of the style.
- Alan's text stays Alan's. When the input was written by him (a rewrite of his draft, a check of his note), do not fix his error classes: letter transpositions with first and last letter intact (`becuase`, `agnet`), dropped apostrophes, missing articles, dropped third-person `-s`, `rewinded`, `purposal`. Fix only when asked to proofread. An agent-fixed text is detectable exactly by the fixes.
- Never, in any register: homophone confusions (their/there, your/you're, to/too), curly quotes, em or en dash, `!`. His corpus has zero of each; one of them marks the text as not his.

## Claude tells

Structure first: removing flagged words from a Claude draft leaves it detectable, changing its shape does not. Act on a shape item on sight. Act on a phrase item only when two or more co-occur (weak alone).

Shape, act on sight:

- Front-loaded summary sentence, then the content it summarized.
- Scene-setting: explaining what the reader already knows before the point.
- Paraphrase of a rule, output or source instead of quoting it.
- One-line closer, aphorism, chiasmus, metaphor.
- Header as a question or "Why X and not Y"; bold on a clause; `**Label.**` bullet lists; a header for every paragraph.
- Triads. Not-X-but-Y as rhetoric. Trailing `-ing` clause carrying a consequence (`..., leaving files ahead of the transcript`).
- Em dash anywhere.

Phrase, weak alone:

- `rather than merely`, `rather than simply`, `less like X and more like Y`, `matters because`, `every single`.
- Significance formula (`underscores`, `highlights the importance of`); `serves as`, `stands as`, `represents` for `is`.
- `genuinely`, `honestly`, `straightforward`, `crucial`, `robust`, `nuanced`, `comprehensive`, `leverage`.
- `however`, `therefore`, `moreover`, `additionally` as sentence glue.
- Faded, not the test anymore: `delve`, `tapestry`, `it is important to note`, `In conclusion`. Still do not write them.

## Procedure

Rewrite and write:

1. Register, and what the text is: a decision and its rationale, a mechanism, a status, a rule, a critique, a message.
2. Shape: point first, parts labelled, artifacts quoted, evidence kind stated, header a noun phrase.
3. Content: the keep/cut list (shape 5).
4. Sentences per the rules above.
5. One pass over the never-lists: sentences 10-11, Errors, the shape list of Claude tells.
6. Output the text only.

Check: the same passes, output the list only, each item `quote -> rule number -> fix`.
