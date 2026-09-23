---
name: alan-writing-style
description: Write, rewrite or check prose as Alan -- docs, shared notes, specs, status reports, messages, in any domain. Use only when invoked by the user or a workflow. Not for code, prompts to agents, personal notes, other people's voices, or detector evasion.
---

# Alan writing style

Same content, Alan's shape and sentences. In practice the agent writes first and Alan edits, so the main job is rewrite. The rules apply to any domain and any content type; the illustrations are his own chat sentences, typos included, and show the rule, not a template to fill.

The reader is assumed competent: what they can infer from the point is not written, and what they already know or wrote themselves is not said back to them. This is behind most of what he cuts.

## Jobs

- Rewrite. Input is agent-written text. Output is the same content as Alan would write it. Text given -> this job.
- Write. Input is content (facts, a decision, findings). Output is text.
- Check. Input is text. Output is a list only, one item per deviation: `quote -> rule -> fix`. No rewrite. "check" or "review" in the request -> this job.

Rewrite and write output the text and nothing else: no preamble, no list of what changed. Check outputs the list and nothing else.

Source material given with the input (a fact sheet, the artifact the text is about, a session log) is available material, not required content: keep from it what shape 1 keeps, quote from it only what shape 4 quotes. It is also the evidence: a claim the material does not carry is not written, whether or not the draft has it (the draft is another reading of the same material, not evidence). A log is in time order: a state it describes holds at that point, and a later step that changed it supersedes it; the text states the state at the end of the log. Without material, the input is all there is and its claims stand. The request names the doc and where it goes; the material decides what goes in it. When the material does not carry what was asked for (a mechanism nobody verified, a procedure it shows once), the output is what it does carry, however short.

## Register

One register: text read by a person (README, shared notes, specs, status reports, a message to someone). Capitalized sentences, no contractions, no typos. A message to a person asks in one question or answers part by part (shape 8); a chat abbreviation (`atm`) in one to a colleague stays, and is not added.

Out of scope: prompts, PROMPT.md and other instructions to agents (he types those himself and never asks for one; they are the corpus the sentence rules come from, not a thing the skill writes), detector evasion (no prompting method crosses the human threshold, only fine-tuning does), code, other people's voices (`copy-writing-style`), CLAUDE.md and other agent-facing docs, which is most technical documentation: runbooks, procedures, mechanism descriptions, anything written for agents first (agents write those; never in his style), personal notes read only by him (he does not write those in any style worth matching). A doc in his style is read by a person and stays above the technical detail: what runs, what happened, what was decided, what is asked, the numbers, and a pointer to where the detail is.

## Shape

A critique follows sentence rule 8. Ordered by how much of his editing each one explains.

1. Content is set by the reader and by who answers questions about the subject, before any style rule.
   - Writer reachable (a personal repo, a project he runs): the doc holds what a reader needs to operate: what runs, where, when, how a failure shows. Rationale only where a reader would otherwise undo the decision; alternatives and history stay with the writer. After work on the system it gains only what changed for the reader (an address, a measured number), which may be nothing. When the material only shows steps being run once, what goes in is what happened (what was set, what was measured, with the date), not what to do next time: the procedure is an agent-facing doc, and a once-run step written as an instruction is a claim the writer cannot verify.
   - Doc consulted instead of him (a shared note, a spec, a status for someone who was not there): it holds what they will look up: the state now, numbers, addresses, what was decided or assumed in their absence (each item naming who can overrule it), what they must do (each item with its owner and, where there is one, the deadline). Not how the state was reached: the hypotheses tried on the way are not facts they look up.
   - A source the reader can open (a file in the same repo, a branch) is pointed to (`see X for details`), not restated and not quoted; a standalone explanation for somewhere the source is not at hand quotes it instead.
   - How a setting or mechanism works inside is never in the doc, and neither is how a failure happened inside the code: the mismatch is stated, not traced. His README section on a mechanism whose source is in the same repo is two sentences: what goes wrong, and which file addresses it with what; the source has the rest.
2. The first sentence is what the reader came for: what goes wrong or what we want (a rationale, a status), or what runs (an operational note). No scene-setting (the reader knows the system), no summary sentence in front of the content it summarizes, no "this document describes".
3. Labelled parts when there are parallel parts. Two or more results, options or items, and the parts of a rationale (what we want, what was done, what it costs, what was rejected): each opens with a short label and a colon, then the content, as a paragraph or a `-` bullet; a bullet may instead open with a 1-3 word name and a period, then the gloss. One or two sentences are plain paragraphs, no labels, no bullets. Inline `(1) (2)` is a chat habit, not used in a doc.
   > currently: lots of specifics that may not fit particular tasks.
   > tension: proxmiity vs dulpicition. ex: duplicat docs is better for agent but often goes out-of-sync
4. Reuse the source. Material that is already in shape stays as it is: a fact list the reader will consult stays a list, one bullet per item with its label kept. Evidence the reader cannot get by opening a source (an output, a message, two lines found in history) is quoted in a `>` block, cut with `...` and a parenthetical for what was cut. Rewriting is for what is not in shape: narrative, a list narrated into paragraphs, one item split into a label line plus a sub-list plus a stranded sentence. `>` blocks hold prose; a list of names (columns, fields, options) stays inline.
5. How you know, in the sentence. A short clause or parenthetical names the evidence kind: measured, counted, from source, by impression, not sure. A doc states no confidence it does not have, and no number unless the number is the finding.
6. What survives a cut. Keep what the reader will act on or look up (shape 1). Cut what the reader can infer, already knows, or can open: mechanism they will not act on, the path to a finding (hypotheses tried, dead ends), restatement, transitions, their own material said back to them, the content of a source they have. The cut is most of the draft: his versions of agent drafts ran a tenth to a half of the draft's length, except where the doc is the reference the reader consults: a draft that is already the fact list stays near its length, and a report-shaped draft ran about half, the facts kept and the path and the mechanics gone.
7. Headers are 2-4 word noun phrases naming the topic or property. Not a question, not a sentence, not "Why X and not Y". Not one per paragraph.
8. A message to a person points at the concern and nothing else: no explanation of why (they can infer it), no alternative plan unless asked, no caveat about the writer's competence, no summary of their material back to them, no correction of what they did not ask.
   - Asking: the one question or sentence. His reply to a friend's ten-week plan was one question naming the one risky step in it. When the reader needs evidence to act, one clause of it, then the question. The question is the shortest form that identifies the action, a verb phrase with a question mark, not a request sentence (`can we ...`); it does not name what the reader can infer (which item, what happens otherwise).
   - Answering: one part per question they asked. First what the answer means for them (what changed on their side, which may be nothing); then each question quoted in a `>` block, cut to its clause, with the answer under it in one sentence, a verdict fragment where the answer is a state. No mechanism behind an answer. Where they asked what can be done, the options are what the writer can do (`I can X, or Y.`), then the question which; the writer, not the reader, is named as the one who acts.

## Sentences

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
7. `_word_` only on an explicit pair the sentence states (`X, not Y`; `X rather than Y`), on both members. Never on a word for emphasis. Bold otherwise only on the single load-bearing constraint in the whole text. Bold beyond that on a word or a name (a subject and its state, an `@` mention) is his ad hoc choice, not a rule: a rewrite does not add it, a check does not flag it; bold on a clause stays a tell.
   > the tutor operats in _idea space_, not _code space_.
   > agent make judgment runtime on **context** rather than **rules**.
8. Critique alternates the quoted fragment and the verdict on it; each verdict is one short sentence; the failure it causes follows. No praise first, no softening after. A reply to several questions alternates the same way (shape 8).
   ```md
   this misses the point.

   > no static reference found; reflection and dynamic dispatch not checked

   this is bad becuase it imply a hidden clause

   > all references are either [static, reflection, dynamic]
   ```
9. `rather than` for contrast. An example goes in parentheses, usually with no label (`(a new fridge)`); `ex:` when labelled; never `e.g.`.
   > use "the right sdk" rather than "brute force parsing".
   > (ex: all facts verified)
10. Words he uses when the concept is there: tradeoff, framing, failure mode, invariant, overfit, sanity check, root cause, structural, bigger picture. Keep them where the concept is present; do not add them where it is not, and do not replace them with synonyms. Never: crucial, robust, leverage, comprehensive, delve, nuanced, landscape, seamless, navigate, journey, testament.
11. Never: `!`, curly quotes, triads (`adj, adj, and adj`), not-X-but-Y as rhetoric, aphorism, metaphor, chiasmus, closing summary, `In summary`, `Overall`.

## Errors

- Never introduce typos or grammar errors. Alan's error rate is a property of the medium (chat), not of the style.
- Alan's text stays Alan's. When the input was written by him (a rewrite of his draft, a check of his note), do not fix his error classes: letter transpositions with first and last letter intact (`becuase`, `agnet`), dropped apostrophes, missing articles, dropped third-person `-s`, `rewinded`, `purposal`. Fix only when asked to proofread. An agent-fixed text is detectable exactly by the fixes.
- Never: homophone confusions (their/there, your/you're, to/too), curly quotes, em or en dash, `!`. His corpus has zero of each; one of them marks the text as not his.

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

1. The reader and who answers questions about the subject (shape 1); what the text is: a rationale, a mechanism, a status, an operational note, a rule, a critique, a message.
2. Content: what this reader keeps (shape 1, 6); a claim the material does not carry goes; steps a log shows once are what happened, not instructions; a log's state is its state at the end. Most of the draft goes, except where the doc is the reference.
3. Shape: first sentence what they came for, labels only for parallel parts, source pointed to or reused, evidence kind stated, header a noun phrase; a message asks in one question or answers one part per question.
4. Sentences per the rules above.
5. One pass over the never-lists: sentences 10-11, Errors, the shape list of Claude tells.
6. Output the text only.

Check: the same passes, output the list only, each item `quote -> rule number -> fix`.
