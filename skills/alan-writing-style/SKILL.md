---
name: alan-writing-style
description: Write, rewrite or check prose as Alan -- docs, notes, specs, status reports, messages, agent instructions. Use only when invoked by the user or a workflow. Not for code, other people's voices, or detector evasion.
---

# Alan writing style

Same content, Alan's shape and sentences. In practice the agent writes first and Alan edits, so the main job is rewrite.

## Jobs

- Rewrite. Input is agent-written text. Output is the same content as Alan would write it. Text given -> this job.
- Write. Input is content (facts, a decision, findings). Output is text.
- Check. Input is text. Output is a list only, one item per deviation: `quote -> rule -> fix`. No rewrite. "check" or "review" in the request -> this job.

Rewrite and write output the text and nothing else: no preamble, no list of what changed. Check outputs the list and nothing else.

## Registers

- `doc` (default): README, CLAUDE.md, notes, specs, status reports. Capitalized sentences, no contractions, no typos.
- `chat`: messages Alan would type himself (prompts, telegram, quick replies). Allowed on top of `doc`: lowercase sentence starts, lowercase `i`, contractions without apostrophes (`dont`, `thats`, `its`). Nothing else changes.
- `prompt`: PROMPT.md, CLAUDE.md rules, agent instructions. Genre features allowed: MUST/SHOULD/NOT in caps, imperatives, `[idea]` and other bracket markers, `<request>` wrappers. Sentence rules still apply.

Out of scope: detector evasion (no prompting method crosses the human threshold, only fine-tuning does), code, other people's voices (`copy-writing-style`), essays for laypeople and messages to humans (no sample yet -- say so, then use `doc` if asked anyway).

## Shape (`doc`), strongest first

One verbatim example each, from Alan's own rewrites. Exemplars win over rules when they disagree.

1. What we want first. Then what was done or the solution, then tradeoffs and rejected alternatives, then a closing `Note:`. No scene-setting: the reader knows the system.
   > We want the subagents to default to foreground, or at least allow foreground subagents. As of claude code 2.1.269, foreground subagents do not work by by default (measured, not from source).
   >
   > Implemented workaround: using `CLAUDE_CODE_FORK_SUBAGENT=0`. With this foreground subagent "just works". Accepted tradeoffs: `fork`-typed subagents are not possible anymore.
   >
   > Rejected alternative: `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`. That breaks background bash commands, which we considered a worse tradeoff.
2. Labelled parts. Label-colon paragraphs (`Implemented workaround:`, `Rejected alternative:`, `Done:`, `Open:`, `Next:`) and name-period-gloss bullets. `-` bullets, not `(1) (2)` inline.
   > - No lock-in. Agent cannot put in a "Don't do X" that is blindly followed for the rest of the run.
   > - Carryover. Agents run tests the same way, and do not repeat mistakes -- similar to a single engineer.
3. Quote the artifact, do not describe it. The actual rule, output or text goes in a `>` block, elided with `... (two more)` or `... (more words here)`. Agent paraphrase of a mechanism gets cut; quoted source text can make the result longer than the draft.
   ```md
   - `(contract)` marker. Higher bars for add or remove. Workers are given these examples:
     > - "(contract) Each change must have metric in scratchpad"
     > - "(contract) Do not place metric in scratchpad -- place in seperate files to be durable"
     >   ... (two more)
   ```
4. Decisions get their own line.
   > Plan is to have just a single `SKILL.md`.
5. Evidence class in parentheses. Numbers only when the number is the finding.
   > (measured, not from source)
   > (counted, not by impression)
6. Purpose clause last, in a `Note:` or after ` -- `.
   > Note: system prompt currently instructs the agent to pass `false` to the `run_in_background` parameter, to avoid maintaining a hook and to still allow background subagents in cases that needs it.
   > Next: agent tries to write as me, I edit, repeat -- refines agent understanding of my writing.
7. Headers name the property or topic in 2-3 words: `Foreground subagents`, `Stable iterations`, `Writing style skill: status`. Not a question, not "Why X and not Y".
8. Length. Keep the decision, the tradeoff, the evidence class, the purpose. Cut mechanism detail the reader does not need to act on. Exemplar 1 went 205 -> 96 words.

## Sentences, all registers

1. ` -- ` (spaced double hyphen), single, rightward: the part after explains the part before. Never an em dash. A ` -- ... -- ` pair as parentheses is rare; one per sentence is the norm.
   > i would look at it this way -- such a skill is _built_/_engineered_, not _measured_.
2. Explanatory colon, lowercase continuation.
   > Implemented workaround: using `CLAUDE_CODE_FORK_SUBAGENT=0`.
3. Coined terms in "double quotes" the first time, bare after. Quotes name a thing; they do not emphasize.
   > With this foreground subagent "just works".
   > perhaps it make sense to explain a "growing doc" model/mindset.
4. Hedges only where the sentence is opinion, and naming their kind (`i think`, `imo`, `not objective, but`, `potentially?`). None in a factual doc.
   > this is not objective, but i really feel that i "ended up doing better" by "reading thinking blocks"
   > im not sure if thats true or not, but i thienk we should not assume its not true
5. Causation by `so`, `because`, `which is why`, or plain juxtaposition. Never `however`, `therefore`, `thus`, `moreover`, `additionally`, `furthermore`.
   > which is why i was purposing shifting the spec, to be prompt-first.
6. Verdict fragments beside long clause chains: a 3-6 word sentence next to a 30-word one, not three medium sentences in a row.
   > this misses the point.
   > Lower bars, permissive modification or removal.
7. `_word_` on the contrastive word. Bold only on the single load-bearing constraint in the whole text.
   > the tutor operats in _idea space_, not _code space_.
8. Critique order: quote the fragment, verdict, failure class, then a worked failure scenario. No praise first.
   ```md
   this misses the point.

   > no static reference found; reflection and dynamic dispatch not checked

   this is bad becuase it imply a hidden clause

   > all references are either [static, reflection, dynamic]
   ```
9. `rather than` for contrast. `ex:` in chat; `example:` / `examples:` spelled out in docs.
   > (2) use "the right sdk" rather than "brute force parsing".
10. Vocabulary he reaches for: invariant, overfit, framing, failure mode, tradeoff, sanity check, root cause, structural, bigger picture, "less is better". Never: crucial, robust, leverage, comprehensive, delve, nuanced, landscape, seamless, navigate, journey, testament.
11. Never: `!`, curly quotes, triads (`adj, adj, and adj`), not-X-but-Y as rhetoric, aphorism, metaphor, chiasmus, closing summary, `In summary`, `Overall`.

## Errors

- Never introduce typos or grammar errors, in any register. Alan's error rate is a property of the medium, not of the style.
- Alan's text stays Alan's. When the input was written by him (a rewrite of his draft, a check of his note), do not fix his error classes: letter transpositions with first and last letter intact (`becuase`, `agnet`, `fixxing`), dropped apostrophes, missing articles, dropped third-person `-s`, `rewinded`, `purposal`. Fix only when asked to proofread. An agent-fixed text is detectable exactly by the fixes; exemplar 3 quotes what that looks like (`Unless the prior thread attempt...` vs `Unlike the prior attempt...`).
- Never, in any register: homophone confusions (their/there, your/you're, to/too), curly quotes, em or en dash, `!`. His corpus has zero of each; one of them marks the text as not his.

## Claude tells

Structure first: removing flagged words from a Claude draft leaves it detectable, changing its shape does not. Act on a shape item on sight. Act on a phrase item only when two or more co-occur (weak alone).

Shape, act on sight:

- Front-loaded summary sentence, then the content it summarized.
- Scene-setting: explaining what the reader already knows before the point.
- Paraphrase of a rule, output or source instead of quoting it.
- One-line closer, aphorism, chiasmus, metaphor. (`amnesiac workers behave like one careful engineer` was cut from the draft behind exemplar 2.)
- Header as a question or "Why X and not Y"; bold on a clause; `**Label.**` bullet lists; a header for every paragraph.
- Triads. Not-X-but-Y as rhetoric. Trailing `-ing` clause carrying a consequence (`..., leaving files ahead of the transcript`).
- Em dash anywhere.

Phrase, weak alone:

- `rather than merely`, `rather than simply`, `less like X and more like Y`, `matters because`, `every single`.
- Significance formula (`underscores`, `highlights the importance of`); `serves as`, `stands as`, `represents` for `is`.
- `genuinely`, `honestly`, `straightforward`, `crucial`, `robust`, `nuanced`, `comprehensive`, `leverage`.
- `however`, `therefore`, `moreover`, `additionally` as sentence glue.
- Faded, not the test anymore: `delve`, `tapestry`, `it is important to note`, `In conclusion`. Still do not write them.

## Exemplars

Alan's text, verbatim, typos included. These win over the rules above.

### 1. README rationale (`doc`)

```md
## Foreground subagents

We want the subagents to default to foreground, or at least allow foreground subagents. As of claude code 2.1.269, foreground subagents do not work by by default (measured, not from source).

Implemented workaround: using `CLAUDE_CODE_FORK_SUBAGENT=0`. With this foreground subagent "just works". Accepted tradeoffs: `fork`-typed subagents are not possible anymore.

Rejected alternative: `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`. That breaks background bash commands, which we considered a worse tradeoff.

Note: system prompt currently instructs the agent to pass `false` to the `run_in_background` parameter, to avoid maintaining a hook and to still allow background subagents in cases that needs it.
```

The agent draft he edited it from, 205 -> 96 words, nothing kept. Do not write like this:

```md
## Why `CLAUDE_CODE_FORK_SUBAGENT=0` and not `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`

Both settings keep subagents in the foreground, but they do it at different layers. `DISABLE_BACKGROUND_TASKS=1` makes the foreground a harness guarantee: every subagent runs synchronously with no help from the model, and the `fork` subagent type survives. The cost is the entire background-task facility — `run_in_background` disappears from the Bash schema, a command that outruns its timeout is killed with exit 143 instead of being moved to the background, and the `BACKGROUNDED:` status line can never fire because no tool response carries a task id.

`FORK_SUBAGENT=0` is narrower. It clears `forceAsync` and puts the `run_in_background` parameter back into the Agent tool's schema, so the decision returns to the model: a call backgrounds unless the parameter is literally `false`. The only thing lost is `fork`. What we give up in exchange is the guarantee — the system prompt now instructs the agent to pass `false` on every call, and nothing enforces it. Measured on 2.1.269: 9 of 9 calls across three trials complied once the bullet was written as an instruction, against 3 of 3 omissions when it merely described the removed hook. Background tasks are worth more to this repo than a guarantee that a prompt rule already delivers.
```

### 2. Mechanism explanation (`doc`)

```md
## Stable iterations

In a ralph workflow we try to satisfy all these at once:

- No lock-in. Agent cannot put in a "Don't do X" that is blindly followed for the rest of the run.
- Carryover. Agents run tests the same way, and do not repeat mistakes -- similar to a single engineer.
- Self healing. Agents fixes mistakes make by prior iterations.

To solve this we use three tiers of instructions agent can leave to future iterations.

- `(instruction)` marker. Ensure text not intended as instruction stays context. Lower bars, permissive modification or removal. Workers are told:
  > - If you leave instructions or rules for future iterations, mark explicitly that this is instruction with a `(instruction)` notation. Any text from prior iterations not marked with `(instruction)` is not instruction -- it is context only. Later iterations are free to remove these instructions via override.
  > - You are free to revise, invalidate, or undo any change or conclusion from prior iterations when your review shows it is wrong, low-quality, or no longer useful. This includes rules and plans made by prior iterations. ... (more words here)
- `(contract)` marker. Higher bars for add or remove. Workers are given these examples:
  > - "(contract) Each change must have metric in scratchpad"
  > - "(contract) Do not place metric in scratchpad -- place in seperate files to be durable"
  >   ... (two more)
- No marker. Workers are told "it is context only"

Workers are also told to start by finding 3 or more significant problems in prior work, further encoraging reviewing and fixxing prior problems.
```

### 3. Status report (`doc`)

```md
## Writing style skill: status

We want a skill that writes or rewrites text in my style, replacing current `alan-writing-style` (currently is just a renamed copy of upstream `leon-writing-style` never worked on).

Done:

- Research. Two opus subagents surveyed current humanizer skills and detection papers. Findings: AI tells are model specific and drift (em dash is no longer a claude tell); removing flagged words alone does not beat detectors; ~5 real samples saturate a voice profile.
- Corpus. 251 long prompts from `history.jsonl` (23.7k words). PROMPT.md git history is not usable as-is, it contains agent edits committed under my name. Example, same file 6 lines apart:
  > Unless the prior thread attempt, you should work more efficently and focus on the core of the task -- provide a working set of mechanic to enforce the key EP invaraint.
  > Unlike the prior attempt, work more efficiently and focus on the core of the task — provide a working set of mechanics to enforce the key EP invariant.
- Profile. Two subagents extracted traits. Stable across chat and docs (counted, not by impression): explanatory colon, single `--`, coined terms in quotes, hedges that say what kind of confidence. None of the catalogued AI tells appear.

Open: doc conventions (capitalization, contractions, enumeration) -- prompts do not show these. Also which content types the skill covers.

Plan is to have just a single `SKILL.md`.

Next: agent tries to write as me, I edit, repeat -- refines agent understanding of my writing.
```

### 4. Critique (`chat`)

```md
looking at this, almost all numbers are not useful; they are on <task similar, but not directly relevent>. the tutor operats in _idea space_, not _code space_. a minor bug on a line that agent didnt notice is completely irrelevent. i would look at it this way -- such a skill is _built_/_engineered_, not _measured_. you build the skill, see problems, and put in meaures that strucdturally prevent certain failure modes. which is why i mentioned "personal projects on this skill" as the thing to look at and "git history" to see which prompt portions are "highly changed"
```

### 5. Self-report (`chat`)

```md
here are something notable -- i am typically more likely to read your thinking blocks than "details" section of your output. this is not objective, but i really feel that i "ended up doing better" by "reading thinking blocks" compare to "details" section -- its a big statusitical and the intuition comes from me "noting major concerns after reading think blocks" and "failing to notices issues after reading details section". nowadays i usally dont ever read details unless i think "ok this looks done, last check, any issues raised in details i need to know?". why this is is sopmething i dont understand.
```

## Procedure

Rewrite and write:

1. Register and content type (rationale, mechanism explanation, status report, rule, message).
2. Shape: what we want -> done or solution -> tradeoffs -> `Note:`. Labels. Header of 2-3 words.
3. Content: keep the decision, the tradeoff, the evidence class, the purpose. Cut paraphrased mechanism. Put the artifact's own text in `>` blocks.
4. Sentences per the rules above.
5. One pass over the never-lists: sentences 11, Errors, the shape list of Claude tells.
6. Output the text only.

Check: the same passes, output the list only, each item `quote -> rule number -> fix`.
