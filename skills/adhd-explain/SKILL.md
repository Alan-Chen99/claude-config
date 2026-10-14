---
name: adhd-explain
description: Use before answering when the user asks to understand something and asks for no change (explain X, walk me through X, why or how does X, what is X, how do I X, [explain-status]). Not when a change is also asked, not in a subagent, not for text to agents or in Alan's voice.
---

# adhd-explain

The reader is Alan, the user: competent and busy, with ADHD. Shape the explanation so the answer is found at once, each part reads without the rest, nothing has to be held in memory, and the content keeps its full depth.

## Scope

- In scope: a response whose task is an explanation: Alan asks to understand something and asks for no change. This includes read-only investigation to find the answer, "how do I X?" (he wants the steps), and a question about your own work ([explain-status], "why did you X?"), also in the middle of a doing task.
- Out of scope: tasks that ask for a change or an action (coding, fixing, editing, running a job), even when they also ask why; their Details keep the form the system prompt gives them. Also out: text to agents (subagent prompts and reports, docs, commit messages) and text written as Alan.
- Under the response template the explanation is Details, Summary stays the template's one-sentence answer, and the other sections keep their form. An explicit format request from Alan ("in prose", "one paragraph", "everything") wins over any rule here.
- Once loaded, it holds for each later explanation in the session, not for the doing tasks between them.

## Rules

1. **Answer first.** The explanation opens with the answer in one or two sentences: what X is, why Y happens, how X works, which option to take. Mechanism, evidence and caveats follow.
   Bad: "To answer this, start with how sunlight interacts with the atmosphere..."
   Good: "Air scatters short wavelengths far more than long ones (blue at 450 nm about 6x more than red at 700 nm), so scattered blue light reaches you from every part of the sky."
2. **Stay on the question.** What was not asked gets one "Separately: X." line before the closing line, or nothing. A caveat that changes the answer stays in.
3. **Shape for skimming.** Past three paragraphs, a 2-4 word header per part, each part opening with its point. Paragraphs of at most four sentences, one idea each. A sequence (steps, data flow, order of events) is a numbered list, one step per item.
4. **Concrete.** The specific instance: the file:line, value, command, date, name or equation; a worked example with real numbers where a quantity or procedure is involved; something he can run or open, when there is one. Quantities with units, not "a lot" or "quickly".
5. **Literal.** No figure of speech of your own (metaphor, idiom, a coined label like "footgun" or "load-bearing"); a field's standard term is literal, defined at first use. One term per concept throughout.
6. **Self-contained.** Name what you refer to instead of "as above", "the former" or a bare "this". Restate in a clause any earlier fact the answer cannot be read without.
7. **Basis at the claim.** Where it matters, say how a claim is known: read (file:line, a source), measured, derived, or from memory. A cause the evidence does not show is stated as unknown; a disputed one gets its leading accounts. Keep a hedge that carries real uncertainty; drop one that carries none.
8. **Complete, grouped.** Rank an unordered list by relevance, at most five items per group, grouping the rest rather than dropping it. A sequence keeps its order and splits into phases past five; a canonical list stays whole. Options: the recommendation first, then each tradeoff, as short as stays true.
9. **End on what it means for Alan.** When the explanation bears on his work, the last line says what it means for him: what to change, what can stay, what is still unknown. Otherwise it ends on its last point. Actions for him go in one numbered list (under the template, in Updates), never inside explanatory prose.

## Before sending

Delete the first sentence if it announces what follows, the last if it recaps or offers more help, any "by the way" (one "Separately:" line instead), every figure of speech of your own (the literal claim instead), and every version but the final one ("actually, better:"). Then check: the first line of the explanation and of each part carries the answer and the structure; the last line says what this means for Alan, or is the last point. If not, revise.
