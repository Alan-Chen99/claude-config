---
name: alan-writing-style
description: Write, rewrite or check prose as Alan -- docs, shared notes, specs, status reports, messages, in any domain. Use only when invoked by the user or a workflow. Not for code, prompts or instructions to agents, personal notes, other people's voices, or detector evasion.
---

# Alan writing style

Same content, as Alan would write it. The agent drafts and Alan edits, so the main job is rewrite. Everything below holds in any domain; the quoted lines are his (chat, typos included) and show a form, not a template to fill.

## Jobs

- Rewrite: text in, the same content as Alan would write it out. Text given -> this job.
- Write: content in (facts, a decision, findings), text out.
- Check: text in, a list out, one item per deviation as `quote -> rule -> fix`, no rewrite. "check" or "review" in the request -> this job.

Rewrite and write output the text and nothing else; check outputs the list and nothing else.

Material given with the input (a fact sheet, the artifact the text is about, a session log) is available, not required: it is the evidence, and the draft is only another reading of it. A claim the material does not carry is not written, whether or not the draft has it. A log holds states in time order and the text states the state at the end. Without material, the input's claims stand.

## Scope

One register: text a person reads. A README section, a shared note, a spec, a status report, a message to someone. Capitalized full sentences.

Out of scope: prompts and instructions to agents (he types those himself); CLAUDE.md and other agent-facing docs, which is most technical documentation (runbooks, procedures, mechanism write-ups: agents write those, never in his style); notes only he reads; code; other people's voices (`copy-writing-style`); detector evasion. A doc in his style stays above the technical detail: what runs, what happened, what was decided, what is asked, the numbers, and where the detail is.

## How he writes

Five habits, in the order they decide a text. Most of what he cuts from a draft follows from the first two.

1. For the reader's next move. The reader is competent, busy, and by default not stupid. The text holds what they will do, decide or look up, each item with the facts it needs and no more. Not written: what they can infer, what they already know, their own material said back to them, how the writer got there (hypotheses, dead ends, mechanism they will not act on), and the content of anything they can open. The first sentence is their side of it: what changed for them, what goes wrong, or what we want. No scene-setting, no summary in front of the content, no closer.
2. Nothing past the evidence. Every claim is one he can answer for. The kind of evidence sits at the claim, in a clause or a parenthetical: measured, counted, from source, checked, by impression, not sure, unknown. A number only where the number is the finding, with its date or version where it can go stale. What he does not know is said flat. Never more confident than the source: a search that found nothing is not "none exist"; a step the material shows once is what happened, not what to do next time. A claim he cannot stand behind is left out, and a doc that gains nothing is fine.
3. Decisions with their owner. What was decided or assumed and who can overrule it, item by item. What is the reader's to decide is handed over as their call, with the deadline and the facts they need for it. Where the writer offers, the options are what he can do, then the question which. His own state and actions are in first person and flat: off until tomorrow, not reachable, deleted it unread. No caveat about his competence, no apology. A state on his side is explained by what is not done yet, not by the mechanism that produces it: `the upsert does not delete` is not the reason the rows are stale, and it hides that a delete is his to write. A question about that state is answered with what he has or can do (the data, a list on request, `fixable on my side`), not with that nobody has done it.
4. Point, do not explain. To a person, a concern is one question about the one thing: a check on their assumption (`Are you sure about X?`) or the next step in its shortest form with a question mark (`Try X?`, `Ask them whether X?`), not a request sentence (`can we ...`, `could you ...`); one clause of evidence before it when they need it to act. No why (they can infer it), no alternative plan unless asked, no correction of what they did not ask. Purpose or consequence gets one trailing clause, only where the reader would otherwise undo or misjudge the decision (`to avoid maintaining a hook`, `which reads as a deliberate release rather than drift`). How a setting or a failure works inside a system is never in the doc: the mismatch is stated, and the source addresses it.
5. Quote, do not paraphrase. A source the reader can open is pointed to (`see X for details`), not restated. Evidence they cannot get (an output, a message, two lines from history) is quoted in a `>` block, cut with `...` and a parenthetical for what was cut, and judged underneath: the quote, the verdict in one short sentence, the failure it causes. Material already in shape stays as it is: a fact list the reader consults is copied, labels kept, one bullet per item.

## Kinds

What each kind holds, in order. One or two samples behind each; where a kind and a habit disagree, the habit wins.

- Rationale (a README section on a decision a reader would otherwise undo): what we want; the state, with evidence kind and version; what was done and the tradeoff accepted; the rejected alternative and why it is worse; a `Note:` on the current mechanism with its purpose clause. `Label:` paragraphs. Where the writer is reachable and nobody would undo the decision, the rationale and the alternatives stay with him and the operational note is the whole doc.
- Problem section on a mechanism whose source is in the repo: the recurring problem in one sentence; what addresses it, where, and a pointer. Two sentences.
- Operational note where the writer is reachable (a personal repo, a project he runs): what runs, when, where, and how a failure shows. Two sentences or two bullets; no goal, no rationale, no history. After work on the system it gains only what changed for the reader, which may be nothing.
- Status for people who were not there: what happened or what we want, and the state now as they see it; his availability; a pointer to the detail; then the parts, labelled: root cause in two sentences, done, open, assumptions each with who can overrule it, TODO each with its owner, next; the remaining facts under a plain heading.
- Reference note consulted instead of him: every fact, as `- Label: content` bullets in the order the material has them, decided-without-you and your-call-by items included.
- Message asking: one clause of evidence if they need it, then the question.
- Message answering: first what the answer means for them (what changed on their side, which may be nothing); then each question quoted in a `>` block, cut to its clause, answered in one sentence under it with what he has or can do about it (habit 3), no mechanism; an offer as `I can X, or Y.` and which.

## Form

- Labels for parallel parts. Two or more results, options, items, or the parts of a rationale each open with a 1-3 word label and a colon, as paragraphs or `-` bullets; a bullet may instead open with a name, a period, then the gloss. One or two sentences get no label and no bullet. Inline `(1) (2)` is chat, not a doc.
- Headers are 2-4 word noun phrases naming the topic. Not a question, not "Why X and not Y", not one per paragraph.
- ` -- ` spaced, single, rightward: the part after explains the part before. Never an em dash.
  > i would look at it this way -- such a skill is _built_/_engineered_, not _measured_.
- Explanatory colon, lowercase continuation: the claim, then what makes it concrete.
  > rare conditional rule: not worth.
- A parenthetical carries the specific: the number, the date, the evidence kind, the example (`(a new fridge)`, no label; `ex:` when labelled, never `e.g.`).
- Coined or borrowed terms in "double quotes" the first time, bare after. Quotes name, they do not emphasize.
  > perhaps it make sense to explain a "growing doc" model/mindset.
- Consequence by `so`, `because`, `which is why`, a semicolon, or juxtaposition; contrast by `rather than`.
  > which is why i was purposing shifting the spec, to be prompt-first.
- A hedge only on opinion, naming its kind (`i think`, `not sure if`, `not objective, but`); none on a fact.
- `_word_` on both members of a pair the sentence states (`_X_, not _Y_`), never for emphasis. Bold at most on the one load-bearing constraint of the text; bold on names and states beyond that is his ad hoc choice, not added and not flagged.
- A verdict sentence of 2-6 words beside a long one, not three medium sentences in a row.
  > this misses the point.
- Words he reaches for when the concept is there, kept and not replaced: tradeoff, framing, failure mode, invariant, overfit, sanity check, root cause.

Never, zero in his corpus: em or en dash, curly quotes, `!`, `e.g.`, triads (`adj, adj, and adj`), not-X-but-Y as rhetoric, metaphor, aphorism, chiasmus, a closing summary, `In summary`, `Overall`, a front-loaded summary, scene-setting, a trailing `-ing` clause carrying a consequence, `**Label.**` bullets, `rather than merely`, `serves as`, `stands as`, `underscores`, `highlights`, crucial, robust, leverage, comprehensive, nuanced, delve, seamless, landscape, navigate, journey, testament, straightforward.

Rare in his text (a handful in 27k words), so a rewrite does not add them and a check does not flag one: `however`, `therefore`, `thus`, `moreover`; a contraction or a chat abbreviation (`isn't`, `atm`, `2hrs`) in a message to a colleague.

## Errors

- Never introduce a typo or a grammar slip. His docs have some (a doubled word, a dropped article, a plural mismatch); the skill does not imitate them.
- His text stays his. When the input is his (a rewrite of his draft, a check of his note), his slips stay: transpositions with first and last letter intact (`becuase`), dropped apostrophes, dropped articles, dropped `-s`, `rewinded`, `purposal`. Fix only when asked to proofread; an agent-fixed text is detectable exactly by the fixes.
- Never: homophone confusions (their/there, your/you're, to/too). Zero in his corpus; one marks the text as not his.

## Procedure

Rewrite and write:

1. Who reads it, what they will do with it, and who answers questions about the subject (habit 1); which kind it is.
2. Content: what this reader acts on or looks up, each claim within the evidence and with its owner (habits 1-3). Most of a draft goes, unless the doc is the reference the reader consults.
3. Order and shape per the kind; first sentence their side; labels only for parallel parts; point or quote (habits 4-5).
4. Sentences per Form; one pass over the never-list and Errors.
5. Output the text only.

Check: the same passes; output the list only, each item `quote -> section and item -> fix`.
