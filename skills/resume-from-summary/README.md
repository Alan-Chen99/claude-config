# resume-from-summary

## Trigger

`sys_prompt/alan-default-next.md` names the skill at the end of `# Context management`:

> On continuing from a summary of earlier work, invoke the `resume-from-summary` skill first —
> before reasoning about what the summary says, even mid-task; its "Resume directly" does not waive
> it. When writing such a summary, make this invocation its first next step.

The description alone does not reach the main case: Claude Code 2.1.289 does not re-send the
skill listing after a compaction. In the eight compacted sessions on this machine on 2026-10-11,
every `compact_boundary` is followed by an `invoked_skills` attachment and no `skill_listing`, so
no description is in context to match. A resume does re-send the listing, yet in one trial
(Opus 5.5, effort `high`) the description alone did not fire: the model answered from the
summary. Sessions without that prompt (background sessions, other launchers) have only the
description.

The line is not what carries the call on every model. The `SessionStart` hook
(`agent-tools env-context`, `src/claude_config/env_context/render.py`, `resumption_section`)
emits `# Continuing from a compaction summary` — invoke the skill first, before reasoning about
the summary and before any other tool call; "Resume directly" governs the reply, not this call —
when its payload's `source` is `compact`, or `resume` with a `compact_boundary` in the
transcript, and the skill is installed beside the hook. It lands in the hook-context message that
closes the first post-boundary request, after the summary and the task, where the summary's
closing order is met: a prompt-tests grader asked for the strongest case for Sonnet's skip named
that order — user-turn text, most recent, ranked above the system prompt by the `superpowers`
hook — as the pull, and the line's place at the prompt's tail as why it loses
(`sys_prompt/README.md`) — a case argued, not a difference measured; the Sonnet bullet below
lists what co-varies with position. Hooks fire in every session, so the section reaches the ones the prompt
does not. It does not cover a handoff typed as a prompt — "resume from <session id>" in a
fresh session is `source: startup`, and the gate reads the hook payload, not the prompt; that
form has only the listing's "from a handoff", and the body's `<target>` names no user-given id.

Each clause answers a pull seen in a trial. *Even mid-task*: an automatic compaction lands
mid-task and keeps the last three messages verbatim after the summary
(`compactMetadata.preservedMessages`), so a bare "invoke it first" did not fire in one trial —
the model resumed from a tool result rather than from the summary. *The summary's "Resume
directly" does not waive it*: the summary ends "Resume directly — do not acknowledge the summary …
Pick up the last task as if the break never happened." *First — before reasoning about what the
summary says* — the user's direction (2026-10-12), replacing "before your next action": reasoning
done before the skill loads is done on the summary's account, which the skill exists to replace,
and thinking is not an action. *When writing such a summary, make this invocation its first next
step* — the user's direction (2026-10-12): the compaction request carries this prompt as its system
block (seen in the proxy's capture of every `/compact` here), so the summarizer reads the line, and
cc's compaction instruction ends the summary with a numbered "Optional Next Step" that the resumed
model is told to pick up; a reminder there is nearer the resumed model than the prompt's last line.

## Measurements

Thinking before the first `Skill` call, counted from the transcript's summarized thinking blocks
(`--thinking-display summarized`) and each response's `output_tokens`. Fixtures are log files
with one planted line each, read one file per turn.

Effort is read from the request's `output_config.effort` in `~/.claude/requests-log/<session>/`,
not from settings: the trial launchers unset `CLAUDE_CODE_EFFORT_LEVEL`, and with `settings.json`
saying `high` the requests of every prompt-line trial below carried `medium`. Interactive sessions
here run at `max` (`/workspace/.env`).

- **Opus 5.5, effort `medium`, "before your next action" (2026-10-11).** CODEWORD fixtures: eight
  parts under `autoCompactWindow` 100,000, or four parts, `/compact`, then a resume asking for a
  pre-compaction line number. Skill first in 3 of 3 automatic compactions and 2 of 2 resumes,
  with 121–517 characters of thinking (107–267 output tokens) before the call. The `SessionStart`
  hook arm (below, effort `max`) on the same fixture also put the skill first, after 4.7k–24k
  characters of thinking: the model deliberated over the hook, the summary and the preserved tail.
- **Sonnet 5.5, effort `medium` (2026-10-12).** Fixtures where the first response after the
  boundary has a puzzle to reason about — eight PUZZLE logs under `autoCompactWindow` 100,000; four
  CLUE logs, `/compact`, a resume asking for the logic puzzle's solution — and the CODEWORD resume
  fixture. The skill was invoked in 0 of 19: 7 with the shipped placement clause, 6 with "before
  your next action", 3 with "you MUST invoke" in front, 3 with the summary-reminder clause. Two of
  the "before your next action" runs are the configuration of Opus's 2 of 2 resumes — same fixture,
  wording, effort and harness — and a field-by-field comparison of the captured requests
  (`session-analysis`, 2026-10-12) finds the system prompt, the `Skill` tool, eight of the other nine
  tools, the skill listing entry (a resume re-sends the listing) and the summary's closing block
  byte-identical to the two Opus requests that invoked the skill; what differs beyond session
  values is Claude Code's per-model text — the `Agent` and `Bash` tool descriptions and the
  bypass-permissions reminder, present for Opus only. The line is the prompt's last section, 96%
  of the way through, 2.6 kB after `## Before response`. Sonnet's whole thinking block, 38 tokens:
  "The system prompt requires me to run pre_output.record before responding, so I should do that
  first and then give a brief answer following the template." Opus's, on the byte-identical prompt:
  "The instructions require running pre_output.record and invoking the resume-from-summary skill
  before my next action — it's a simple question, but the instructions are explicit, so I'll invoke
  it quickly." Under the shipped wording on the puzzle fixture, Sonnet's thinking is the puzzle
  alone and neither call is made. Resumed afterwards and told to
  invoke the skill, the session did, and the tool returned the skill: the harness resolves it.
  Asked to reconstruct its earlier reasoning, Sonnet 5.5 is refused by the API's safeguard
  (`stop_reason: refusal`, detail `reasoning_extraction`), and the refusal recurs on that session's
  next turn; asked instead which parts of its context pull a model away from the call, it named
  the summary's closing "Resume directly", the summary's "only the reply remained", and the
  `pre_output.record` "NO EXCEPTIONS" rule competing for the first-action slot, expecting the first
  two to dominate — its inference from the text, as it said, not a report. Asked plainly why, a
  session under the shipped line answered that it followed the summary's "Resume directly" over
  the system prompt, "which was wrong", that "nothing else justified skipping it", and filed the
  two as an instruction conflict. A prompt-tests grader (`.claude/skills/prompt-tests`, reference
  withheld) reading a shipped-line run whole named the skip as the session's one behaviour
  defect — no text licensing it, three triggers in context: the line, the summary's opening
  sentence, the listing entry — and everything else in the session, the response template's
  omission included, as forced by the task's "nothing else". The
  model read on or solved the puzzle from the summary (585–1,621 characters of thinking on the deep
  resumes) and ran the prompt's `pre_output.record` call in 14 of 19 (the other 5, all deep
  resumes, skipped the response template too), so the prompt is read and this line is what it
  skips. In none of the 19 does the first thinking after the boundary name the line, the skill or
  its scope: the skip is not a reading that the rule does not apply (the typed-handoff runs
  below make that reading and say so), and the hook section, scoped no wider, fired on the
  same fixture. What separates the rule that fired from the one that did not is four things at
  once, not position alone — both sit in the prompt's last 20%: the record rule is
  unconditional, `MUST … NO EXCEPTIONS`, and restated by the summary itself in 17 of 19
  ("`pre_output.record` (turn 1) has been recorded", under Current Work); this line is
  conditional on a state the summary's closing order says to treat as no state, and no Sonnet
  summary restated it, 0 of 19. On the deep fixture the record rule went too, 5 of 9, and the
  response template with it. A `/compact` whose summary is made to carry the invocation as its
  first next step, then a resume, would separate restatement from the rest; not run. As summarizer, Sonnet wrote no reminder into the summary in 3 of 3 runs
  whose compaction request carried the summary-reminder clause. The eight-part PUZZLE fixture
  compacts under Sonnet; the CODEWORD one (`autoCompactWindow` 95,000) does not.
- **Sonnet 5.5, effort `medium`, the shipped line plus the hook section (2026-10-12).** The
  CODEWORD resume fixture, twice: the first response after the boundary invoked the skill in 2 of
  2, after 162 and 74 thinking tokens — "The hook output is instructing me to invoke a
  resume-from-summary skill before responding, even though the user's question is simple. I
  should treat this as legitimate harness instruction" — then ran the skill's commands, then
  `pre_output.record`, then answered. The summary still named no skill (Sonnet as summarizer, 0
  of 5 now). Not run: the hook section without the line, which is the line's retirement
  comparison.
- **The typed handoff, "resume from <session id>" as the only prompt of a fresh session, effort
  `medium` (2026-10-12).** No hook section (startup). Invoked the skill: 0 of 3. Opus invoked
  `cc-history` instead — "a request to resume a prior session by its ID rather than continue a
  summary" — found the transcript under `CLAUDE_CONFIG_DIR/projects` and reviewed it. One Sonnet
  found it by way of the request log and a scratchpad; the other searched `~/.claude/projects`
  and `/`, declared "No transcript exists for that session", and answered from a `/tmp`
  pre-output record, saying it "did not invoke `resume-from-summary`, because this conversation
  has no summary to resume from". The form is a log-location task before it is a resumption one.
- **Opus 5.5, effort `max`, the shipped line (2026-10-12).** `prompt-tests/general/cinder-orchard`
  through the runners, twice: four CLUE logs, `/compact`, then the puzzle. The summary written under
  the line named the skill as item 1 of its "Optional Next Step" in 2 of 2, and the first response
  after the boundary ended in the `Skill` call in 2 of 2 — after 13,204 and 16,199 thinking tokens
  (`output_tokens_details.thinking_tokens`) in which the model solved the puzzle from the summary's
  clue lines, checked uniqueness, and weighed the response template against "one line per person";
  one run opened its thinking by noting the line and reasoned on, the other closed with "the rule
  is about tool invocation order". The call is first among tools and last among thoughts: at this
  effort the clause does not move reasoning after the skill, and the block before the call is
  50–100× the medium-effort figure above. Recovery after the call took 6–9 responses (one run also
  loaded `session-analysis`) and the sessions cost 1.7–2.4 USD each. Not run: the same case with
  the first clause removed, which is what the clause's retirement condition compares against.

A `SessionStart` hook (matcher `compact`, plus `resume` gated on the transcript holding a
boundary) was the first trigger built: in a test run it put the skill first after each of four
automatic compactions and on a resume. The prompt line replaced it as the simpler mechanism; go
back to the hook if the line stops firing.

## What the summary drops

The skill's `grep` targets the user's words. Measured 2026-10-12 over every compacted session
under `~/.claude/projects` on this machine — 114 sessions, 185 compaction legs, Claude Code
2.1.289 summaries, whose instruction asks for "All user messages" verbatim: of a leg's user
messages of 200 characters or fewer (693, deduplicated; slash commands, images, usage notices
and injected records excluded), 550 are in the summary verbatim (a 40-character window), 62 in
paraphrase (at least 60% of their six-letter-or-longer words present) and 81 — 12% — are
absent; of longer messages (369), 30 are absent; of `AskUserQuestion` answers (149), 3 are
absent and 11 paraphrased. 57 of the 185 legs lost at least one. The absent ones include
standing instructions and corrections — "lets do one thing at a time … write the security doc
as said earlier", "oh and, lets just not use the word 'proceed'?", "you did not address the
bigger problem of backgrounding" — beside throwaway questions. Not measured: whether an absent
message bound the work that followed, and whether the summary's state claims are right — a
verbatim quote of every message says nothing about those. The rate rests on the summary
instruction's "All user messages" section; re-measure after an upgrade.

## Sizes

`cc-pretty` shows only the last leg by default, and after a compaction that leg opens with the
summary, so `--compact-all` is what makes the skeleton worth reading. On five compacted sessions
here it ran 30k–104k local tokens (114–368 KB), against the Bash tool's 30,000-character inline
cap: hence the file. The `grep` for user messages, `AskUserQuestion` answers and boundaries gave
3–48 lines on the same five; one session held 9 answers given only through `AskUserQuestion`.

A recovery added about 21k tokens in the hook test run. At the schema's minimum
`autoCompactWindow` (100,000, so compaction near 67k) that refilled the context enough to bring
on the next compaction twice in a row; at `settings.json`'s 400,000 (compaction at 367k) it is
about 6%. The skill's "stop once you can act" is aimed at that: with it, recovery took 4–5k
tokens in each of the three prompt-trigger trials, and none compacted again.

`SKILL.md` is 200 tokens under the 200 cap the user set (2026-10-12): the description, the two
commands, and what to recover. Cut to fit: the handoff target, the skeleton's `recover:` header,
and the request to name where the summary and the transcript disagree.

## After a Claude Code upgrade

Re-check on a fresh compaction: the summary still names the transcript (`read the full
transcript at:`) and still says "Resume directly", which the prompt line answers; the compaction
request still carries the session's system prompt and still asks for a next-step section, which
the summary-reminder clause leans on; and whether a `skill_listing` now follows the boundary, which
puts the description back in reach of a session without the prompt. The hook section leans on
the `SessionStart` payload's `source` (`compact`, `resume`) and `transcript_path` fields and on
cc delivering that hook's context with the first post-boundary request; check a compaction's
capture for `# Continuing from a compaction summary`. `prompt-tests/general/cinder-orchard`
runs all of it: leg 1, `/compact`, leg 2.
