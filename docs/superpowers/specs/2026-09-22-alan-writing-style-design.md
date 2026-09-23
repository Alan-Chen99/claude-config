# alan-writing-style: single SKILL.md

We want a skill that writes or rewrites text in my style. Current `alan-writing-style` is a renamed copy of upstream `leon-writing-style` never worked on: the voice it describes is not mine, its 9-step script echoes `--thoughts` back into every step, and upstream has dropped the skill. Plan is to replace it with a single `SKILL.md`; nothing is loaded at runtime besides that file.

## Jobs

- Rewrite. Input is agent-written text; output is the same content as I would write it. This is the main job: in practice the agent writes first and I edit.
- Write. Input is content (facts, a decision, findings); output is text.
- Check. Input is text; output is a list of deviations, each as quote -> rule -> fix. No rewrite.

Job is inferred from the request: text given -> rewrite; content only -> write; "check" or "review" -> check.

## Registers

- `doc` (default): README, CLAUDE.md, notes, specs, status reports. Capitalized sentences, no contractions, no typos.
- `chat`: messages I would type (prompts, telegram). Lowercase sentence starts, lowercase `i`, contractions without apostrophes are allowed; nothing else.
- `prompt`: PROMPT.md and agent instructions. Genre features allowed (MUST/SHOULD, imperatives, `[idea]`, `<request>`); sentence rules still apply.

2026-09-23: `prompt` removed on Alan's word ("why would i ask you to write prompt?"), and `chat` with it for the same reason; the one register left is `doc`. Messages to a person are sampled since (06, 09, 12) and are `doc`: capitalized, one question or sentence. Record: `skills/alan-writing-style/CLAUDE.md`, sample 13.

Out of scope, stated in SKILL.md: detector evasion (no prompting method crosses the human threshold, only fine-tuning does), code, other people's voices (`copy-writing-style` does that), essays for laypeople and messages to humans (no sample yet).

## Evidence

Samples. `skills/alan-writing-style/samples/`, three before/after pairs: `NN-<name>.before.md` is the agent draft I edited from, `NN-<name>.after.md` is my rewrite. Pair 1 (readme rationale) was edited from an unadapted agent draft, 205 -> 96 words, nothing kept. Pairs 2 and 3 were edited from drafts already written "as me": pair 2 (mechanism explanation) nothing kept, pair 3 (status report) ~90% kept. Listed in the skill dir `CLAUDE.md` for future edits to the skill; SKILL.md embeds excerpts by copy and does not reference the files.

Corpus. 251 of my long prompts from `~/.claude/history.jsonl` (23.7k words), used for sentence-level traits. Not style: anything correlated with the text being a prompt (imperatives, MUST/SHOULD, `[idea]`, addressing an agent) and anything correlated with it being a chat turn (`so`, `lets`, `ok`, questions). Not evidence: PROMPT.md git history, it contains agent edits committed under my name.

Research (two subagent reports, session scratchpad only): AI tells are model specific and drift, example: em dash is no longer a Claude tell; removing flagged words does not beat detectors, structure does; ~5 samples under 1500 words saturate a voice profile; positive examples beat prohibitions; editors fixing AI text replace 74% / delete 18% / insert 8%, so insertion quotas are wrong.

## SKILL.md content

Sections in order. No step script, no `--thoughts`, no marker quotas, no word-count sufficiency check.

2026-09-23: rewritten after an overfitting review (`skills/alan-writing-style/CLAUDE.md`, round 8). Sections now: jobs, scope, how he writes (five habits: for the reader's next move; nothing past the evidence; decisions with their owner; point, do not explain; quote, do not paraphrase), kinds, form, errors, procedure. Items 3 and 4 below survive as the kinds and the form checklist, with the never-list restricted to words at zero in the corpus. Acceptance gains a rating procedure beside retention (CLAUDE.md there, Iteration).

1. Frontmatter: `name: alan-writing-style`; description says what it does and "use only when invoked by user or workflow".
2. Jobs and registers, as above.
3. Shape rules for `doc`, ordered by strength, one verbatim example each from samples:
   - What we want first, then what was done or the solution, then tradeoffs and rejected alternatives, then a closing `Note:` with a purpose clause. No scene-setting; the reader is assumed to know the system.
   - Labelled parts. Label-colon paragraphs (`Implemented workaround:`, `Rejected alternative:`, `Done:`, `Open:`, `Next:`) and name-period-gloss bullets (`No lock-in. Agent cannot put in a "Don't do X" that is blindly followed for the rest of the run.`). `-` bullets, not `(1) (2)` inline.
   - Quote the artifact instead of describing it: `>` blocks of the actual rule, output or text, elided with `... (two more)`.
   - Decisions get their own line (`Plan is to have just a single SKILL.md.`).
   - Evidence class in parentheses (`(measured, not from source)`, `(counted, not by impression)`); numbers only when the number is the finding.
   - Purpose clause at the end (`to avoid maintaining a hook and to still allow background subagents in cases that needs it`, `-- refines agent understanding of my writing`).
   - Headers name the property or topic in 2-3 words (`Foreground subagents`, `Stable iterations`); not questions, not "Why X".
   - Agent paraphrase of mechanism gets cut; expect about half the length. Keep the decision, the tradeoff, the evidence class, the purpose.
4. Sentence rules, all registers, one verbatim example each from samples or corpus:
   - Single rightward ` -- ` expansion; the part after explains the part before. Never an em dash.
   - Explanatory colon, lowercase continuation.
   - Coined terms in "double quotes" the first time, bare after (`"just works"`). Quotes name things, they do not emphasize.
   - Hedges only where the sentence is opinion, and naming their kind (`i think`, `imo`, `not objective, but`). None in a factual doc.
   - Causation by `so`, `because`, `which is why`, or juxtaposition. Never `however`, `therefore`, `moreover`, `additionally`.
   - Verdict fragments beside long clause chains (`Lower bars, permissive modification or removal.`).
   - `_word_` for contrast; bold only for the one load-bearing constraint.
   - Critique order: quote the fragment, verdict, failure class, worked failure scenario.
   - `rather than` for contrast. `ex:` in chat, `example:` spelled out in docs.
   - Vocabulary: invariant, overfit, framing, failure mode, tradeoff, sanity check, root cause, structural, bigger picture. Never crucial, robust, leverage, comprehensive, delve, nuanced, landscape.
   - Never: `!`, curly quotes, triads, not-X-but-Y, aphorism, metaphor, closing summary.
5. Errors policy:
   - Never introduce typos or grammar errors, in any register.
   - When the input is my own text, do not fix my error classes (letter transpositions with first and last letter intact, dropped apostrophes, article omission, agreement, `rewinded`, `purposal`) unless asked to proofread. An agent-fixed text is detectable exactly by those fixes; the PROMPT.md pair in `samples/03-status-report.after.md` is the example.
   - Never: homophone confusions (their/there, its/it's as confusion), curly quotes, em dash. These mark text as not mine.
6. Claude tells, ordered by strength, with the "weak alone" rule: shape mismatches act on sight (front-loaded summary, scene-setting, paraphrase, closer or chiasmus, headers as questions, bold on clauses); phrase-level items only in combination (`rather than merely/simply`, `less like X and more like Y`, `matters because`, `every single`, significance formula, `serves as`, `-ing` riders, `genuinely/honestly/straightforward`, mannered adjectives). Faded tells (delve, tapestry, "important to note") listed as faded, not as the test.
7. Exemplars, under 1500 words: the three `after` samples verbatim; pair 1 before/after; two corpus excerpts (`#313`, `#352` in the session corpus; text copied into SKILL.md, the corpus is not in the repo). Samples win over rules when they disagree.
8. Procedure. Rewrite and write: register and content type -> shape -> content selection -> sentences -> never-list pass -> output text only. Check: the list only.

## Files

- Delete: `skills/alan-writing-style/references/`, `skills/alan-writing-style/README.md`, `skills/scripts/skills/alan_writing_style/`, `skills/scripts/tests/test_alan_writing_style.py` (conftest has no entry for it).
- Add: `skills/alan-writing-style/SKILL.md` (rewritten), `skills/alan-writing-style/samples/0{1,2,3}-*.{before,after}.md`.
- Update: `skills/alan-writing-style/CLAUDE.md` (files table: `SKILL.md`, `samples/`, with the retention numbers above), `skills/CLAUDE.md` row for `alan-writing-style/`.
- `leon-writing-style` untouched.

## Acceptance

Not tested in this iteration. Procedure for later: agent writes a fresh piece with the skill, I edit, `git diff --no-index --word-diff` retention >= 80% (pair 3 of this session: ~90%). Each new pair goes into `samples/`; rules in SKILL.md change only from a pair. No prompt-tests case, the skill is user-invoked.
