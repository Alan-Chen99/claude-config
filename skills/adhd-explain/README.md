# adhd-explain

## Provenance

`SKILL.md` adapts `skills/i-have-adhd/SKILL.md` from https://github.com/ayghri/i-have-adhd at `1ecea19` (MIT, Ayoub Ghriss; the notice is `LICENSE`). Upstream shapes every response of a session for a reader with ADHD, starts on `/i-have-adhd` and stops on "stop adhd mode". Here it covers explanations only and loads on its description.

## Scope

Alan's words (2026-10-13): "scoped to explanations text to alan, when the explanation is task. is not applicable to "details" section of your output", then "(to clarify: not appliable for details section for a standard coding task). is relevent if taks is of form "explain X"".

Read as: the task is an explanation, where Alan asks to understand something and asks for no change. A doing task stays out even when it also asks why ("why is X broken? fix it"), so its Details keep the form the system prompt gives them. Counted as explanations: read-only investigation to find the answer, "how do I X?", and a question about the agent's own work in the middle of a doing task (`[explain-status]`).

## Upstream rules, mapped

| Upstream | Here | Why |
| --- | --- | --- |
| "What ADHD changes about reading" (5 facts) | the opening paragraph | They restated the rules, so they became one sentence of goals |
| 1 Lead with the next action | 1 Answer first | An explanation delivers an answer; an action follows only sometimes |
| 2 Number multi-step tasks | 3 (a sequence is a numbered list), 9 (his actions in one numbered list, in Updates) | |
| 3 End with one concrete next action | 9 End on what it means for Alan | Only when the explanation bears on his work; otherwise it ends on its last point |
| 4 Suppress tangents | 2 Stay on the question | |
| 5 Restate state every turn | 6 Self-contained | An explanation has no step N of M |
| 6 Specific time estimates | 4 (quantities with units) | Effort estimates rarely arise in an explanation |
| 7 Make completed work visible | dropped | An explanation reports no completed work |
| 8 Matter-of-fact errors | 7 Basis at the claim | Upstream's eval (`evals/RESULTS.md`, `partial-success`) found rule 8 pushing a cause the evidence did not show |
| 9 Cap lists to 5 | 8 Complete, grouped | |
| 10 No preamble, recap, closers | Before sending | |
| Break 1: "explain" means explain fully | the opening paragraph: full depth | Explanations are the whole scope here |
| Breaks 2-4: destructive action, debug spiral, ambiguity | dropped | Situations of a doing task; the system prompt covers them |
| Breaks 5-6: the task or the harness wins | Scope: Alan's format request, the response template | |
| Persistence until "stop adhd mode" | Scope: later explanations in the session | No session-wide mode, so no off switch |

A fresh-subagent review of the draft for overfitting (2026-10-13) widened rules 1, 4, 5 and 7 from software-only wording to any domain (a date, an equation, a disputed historical cause, a field's standard term), kept ordered and canonical lists out of rule 8's ranking and grouping, and gave the last line to rule 9 alone. Keep new wording domain-neutral.

## Reddit thread

r/ClaudeAI `1v8o1jn`, "Whoever created the ADHD skill god bless you" (2026-07-28; 467 comments fetched from arctic-shift on 2026-10-13). Comment ids in parentheses.

Used:

- Figurative wording and coined labels ("14c is your footgun, and it lands loudly", p0a2vtd; "load-bearing", p0bjobl; "word salad", p0aink4): rule 5.
- Instructions buried in prose, mixed lists of steps and notes (p0945jp): rule 9, his actions in one numbered list.
- "good version, better version my final recommendation" (p08o2lt): Before sending, every version but the final one.
- Brevity dropping needed information (p08oq24, p08q7dq, p20516b, p08sq3g; long answers wanted, p07ntdt): rule 8 and the opening's "the content keeps its full depth".
- "something tactile that I can play with" instead of a document (p0an2ct): rule 4, something he can run or open.
- The short version first and the full one after (p0iwudm, p2almlb); re-entry after a break (p1exmgi): rules 1 and 3.
- One term per concept, from Simplified Technical English (p0j1lum): rule 5.
- The pre-send check as the part that works (p07s91g, p0ax1gv): kept.
- "patronising" (p08bdri): the reader is "competent and busy".
- Too long; short declarative bullets beat paragraphs (p07hojm, p07i9xf, p09ate3): one Bad/Good pair instead of upstream's ten.
- The description as a routing contract with a NOT FOR line (p081het): the description.
- A session-wide skill that fails to trigger or is forgotten (p086lpj, p0a6l92, p08d61j, p07gjk4): the trigger is a kind of task, named in the description.
- Newer prompting guidance favours saying what to do over "do not" lists, as relayed in p081nb9: rules say what to do; "no" lists stay short.

Not used:

- Always-on as an output style, `CLAUDE.md` or a `SessionStart` hook (p0djixx, p0eelzp, p0k5a7i, pficu3l, p07vbr4): the scope is one kind of task, not every response.
- Restating progress every turn ("pure hell", p099h32): dropped with upstream rule 5.
- A word cap or "80% shorter" (p0chio1): conflicts with full depth.
- A backlog CLI for tangents (p07ikmm): beyond a writing skill; a tangent gets one "Separately:" line.
- "I have ADHD" alone as the instruction (p09mykb, p08fonp): reported to drop information (p08oq24); not measured here.

## Measured

2026-10-13: Claude Code 2.1.289, `claude-opus-5-5`, `sys_prompt/alan-default-next.md`, `scripts/prompt-test-cc.sh`, one run per arm, so no rates. "Without" ran with no `adhd-explain` in the skills directory; "with" loaded this `SKILL.md` body byte for byte. Cost is `total_cost_usd`, a list-price figure.

Tasks, verbatim:

- A: "Clients sending a steady 6 requests per second start getting almost every request rejected after roughly half a minute, and they stay rejected until they stop sending for a while. Clients that send bursts of 30 requests every 10 seconds are never rejected. Explain why." Fixture: a 4-file token-bucket package whose rejections cost a 2-token penalty with no floor.
- B: "What does `git commit --fixup` do?" No fixture.
- C: "Why did HTTP/3 move to UDP? I keep reading that it fixes head-of-line blocking, but I thought HTTP/2 already fixed that with multiplexing. How does head-of-line blocking differ between HTTP/1.1, HTTP/2 and HTTP/3?" No fixture.
- D: "The last page returned by `page()` is missing its final item. Fix it and run the tests." D-why opens "Why is the last page returned by `page()` missing its final item?" Fixture: an off-by-one pager and its test.

| Task | Arm | Skill loaded | Details words | Output tokens | Cost |
| --- | --- | --- | --- | --- | --- |
| A | without | - | 408 | 33.7k | $1.06 |
| A | with | first step | 843 | 51.5k | $1.57 |
| B | without | - | 324 | 19.2k | $0.66 |
| B | with | first step | 615 | 51.3k | $1.62 |
| C | without | - | 984 | 31.6k | $1.06 |
| C | with | first step | none: the account's session limit (HTTP 429) ended the run before its answer | | |
| D | without | - | 235 | | $0.55 |
| D | with | no | 214 | | $0.50 |
| D-why | with | no | 173 | | $0.72 |

- Routing: each explain task loaded the skill at its first step; neither coding task did, and their Details kept the without-arm form.
- Shape: both completed "with" runs open Details with a paragraph that carries the answer, put each part under a header, and end on what it means for Alan; A's "without" run reaches the cause (the penalty with no floor) only in its second numbered stage.
- Length and cost: Details 2.1x and 1.9x, output tokens 1.5x and 2.7x. Read from the A and B transcripts, the added length is facts restated so each part reads alone (rules 3 and 6); basis tags and file:line references (A: 10 and 9 against 0 and 3; B: 4 and 5 against none), where rule 7 says "Where it matters" and A's reasoning reads "Each claim should carry a basis tag"; more checks run to turn read or remembered claims into measured ones (B ran three demo scripts to the without arm's one); and the closing line. The thread is split on whether that is wanted: longer answers (p07ntdt, p08l3sm), the one-sentence answer (p07q2gm).
- Run-to-run spread on the explain tasks is unmeasured. D's two runs that did not load the skill differ by 9% (235, 214 words).
