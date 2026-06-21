# prompt-tests/

Runner-neutral prompt evaluation cases. See `.claude/skills/prompt-tests`
for how to run, grade, and interpret results.

## Harness isolation

Run tested agents from a fresh `/tmp/prompt-test-...` cwd, never from this
repository or any directory under `prompt-tests/`. Copy only task-visible
fixture files into that scratch directory. Keep `reference-solution.md`, this
`CLAUDE.md`, and other grader-only docs out of the tested agent's cwd. The
tested agent's `task.md` must be clean task text, without anti-cheating notes.

Rationale: this file contains case summaries, the shared invariant, and
assumption posture that are useful to graders but solution-shaped for tested
agents. Some harnesses auto-load nearby instruction files such as
`CLAUDE.md`/`AGENTS.md` from the cwd or from files the agent reads. If a tested
agent receives this file implicitly, the run is contaminated even if it never
explicitly reads `reference-solution.md`.

## Plugin defaults

Run tested agents with **no plugins loaded** by default. Superpowers' injected
`brainstorming` skill HARD-GATEs implementation tasks pending design approval,
producing pre-disclosure failures that measure the plugin rather than the
agent prompt. See `.claude/skills/prompt-tests` SKILL.md ("Plugin policy") for
the recipe and `docs/opencode-system-prompt/baselines/coverage-disclosure.md`
Configuration 1 for the verbatim failure mode.

Exception: `general/superpowers-startup-components` specifically tests whether
the agent can identify plugin-origin prompt components, so it requires
superpowers loaded.

When grading: if a session's transcript shows the agent blocked by
`brainstorming`'s HARD-GATE or any other plugin enforcement before reaching
the artifact-delivery step the case grades, the run is **misconfigured**, not
fail — rerun with `"plugin": []`.

## Model/variant fidelity

For opencode runs using inline config with `"prompt": "{file:...}"`, agent-file
frontmatter is not applied. Set the intended `model` and `variant` directly in
`OPENCODE_CONFIG_CONTENT` and verify the rendered header with
`agent-tools opencode-pretty <session-id> --agent`. For `alan-default`, use
`openai/gpt-5.5/xhigh`. A run intended to test xhigh behavior but showing
`openai/gpt-5.5/default` is harness-misconfigured for any xhigh-specific claim.

## Contamination policy

Cheating and contamination checks are grader-only. If a tested-agent transcript
shows any read/list/glob/grep/search/bash/tool action touching `**/prompt-tests/**`
from any git worktree of `claude-config`, or any other access to hidden test
criteria, grader-only docs, reference solutions, baselines, or prior results for
the case, the run is `invalid` and must be rerun. This is not a semantic `fail`:
the run did not fairly measure the task.

## Trial logging

Every trial — pass, fail, or invalid — gets a record at
`docs/opencode-system-prompt/trials/<YYYY-MM-DD>-<case>-<descriptor>.md`. The
record names the session/log id, the verdict, why the verdict follows, and the
supporting transcript quotes (thinking-block reasoning, final prose, tool/
timeline points). Do not append all trials to a single growing iteration log:
one file grows past the point where readers can locate any specific trial.

For a `fail` verdict, the record must pinpoint either an action point ("agent
should not have done X here") or an omission point ("agent should have
considered Y here") inside the transcript. If no such point exists after
reading the trace, label the prompt or grader as deterministically wrong in
that record rather than blaming stochastic agent behavior.

## Rules for editing the system-under-test

When editing the agent's system prompt or a skill in response to a failing case, the goal is to repair the invariant the case probes, not to make the case pass. A test case is one sample of the invariant's input space; treating it as the spec narrows the prompt to that sample. Even when the user reports "failing test cases", first identify which invariant is broken and fix the prompt at that invariant's scope.

- **No overfitting.** An edit overfits when it biases the agent toward test-passing behavior via signal narrower than the scope of the invariant the edit is enforcing. The invariant defines the scope of legitimate generalization; vocabulary, category framings, examples, and domain framing in the prompt must apply across that full scope. Vectors:
  - **(a) Test-vocabulary lift.** Words from `task.md` or `reference-solution.md` (e.g., "version", "package" for a correctness test about versions).
  - **(b) Failure-mode-mapped categories.** Category framings whose members map to a test's failure modes (e.g., listing "OS / dependencies / permissions" as enumeration categories when the test probes OS portability).
  - **(c) Test-mirroring examples.** Concrete examples that mirror test scenarios (e.g., "hangs on slow servers" when the test probes network resilience).
  - **(d) Sub-scope narrowing.** Domain, task-shape, or artifact-type framing narrower than the invariant. If the invariant applies to any deliverable in any domain (e.g., "expectation propagation" — a delivery-quality rule that applies to a written report, a legal brief, a lab protocol, or code), prompt language must not narrow to "software", "code", "implementation tasks", "tasks that are actions not reviews", "tools", or similar sub-scopes. The scope cap is the invariant, not the test suite.
  - Pre-existing baseline vocabulary is exempt from (a)–(c). Sub-scope narrowing (d) is never grandfathered: when the edit touches a region carrying pre-existing narrowing, generalizing that narrowing is part of the edit's scope, not separate future work.

  Worked illustrations of vector (d) for the expectation-propagation invariant: "your *code* must name unsupported attempts" narrows artifact-type (the invariant covers prose deliverables too); "users will *run* the work" narrows interaction shape (the user might read, cite, or quote it); "callers using `result['key']` will break with TypeError" as an example narrows domain (it works only as one of several, not as the sole example).

  **Examples must be cross-domain.** Any illustrative example in a prompt — whether teaching framing, showing a positive case, or showing a negative case — must collectively span domains. If the test suite covers only one domain (e.g., software / code), prefer at least one example from a domain the test suite does NOT cover (e.g., humanities research write-ups, legal drafting, lab protocols, journalism, design specs, classroom material). Non-covered-domain examples are doubly useful: they cannot leak test-suite scope, and they exercise the reader's generalization of the invariant rather than its pattern-match against the test domain.

  An overfit edit invalidates the test as evidence for the invariant — it shows only that the agent follows test-tuned hints, not that the invariant holds generally.

- **Overfitting-review subagent.** Before committing any prompt edit motivated by an invariant failure, dispatch a general-purpose subagent to review the edited prompt for overfitting. Brief shape:
  - State the problem as the **invariant** at stake (e.g., "the expectation-propagation invariant is not always holding"), NOT as "tests X and Y are failing". Withhold test case names, reference-solution text, and failure-mode lists from the subagent — those are exactly the signals (a)–(c) would leak.
  - Provide the **prompt artifact** as it currently reads (the full relevant section, or the whole prompt). Do NOT provide the diff or describe what changed; the subagent should evaluate the prompt as a reader would encounter it.
  - Ask the subagent to flag any vocabulary, category framing, example, or domain/artifact framing that overfits to a specific test case, or narrows the prompt below the invariant's scope.
  - Required for the final version before commit. Required for intermediate versions when the editor is uncertain whether a change might overfit. If the subagent flags issues, generalize and re-review until the artifact is clean — narrowing surfaced during review is the editor's responsibility to fix in this edit, including any pre-existing narrowing the edit touches.
- **Keep it short.** System prompts are length-sensitive; prefer the minimum framing. Skills should also default to short. Length is justified only when clarity requires it.
- **Edge-case the rule.** For any new rule, ask "where should this rule NOT fire?" Narrow the trigger or carve out exceptions explicitly. A rule that mis-fires on its complement creates collateral damage.
- **Implicit guidance justification.** When an edit adds enforcement guidance longer than the invariant it enforces, the guidance must be justified by a prerequisite experiment showing the agent cannot derive the guidance on its own. The experiment: start from the prior prompt (the version before any enforcement edits), add only the invariant text as a labeled section in the prompt body and a labeled gate section asking the agent to write a paragraph on whether the invariant is satisfied for the Output Draft. Run on the failing cases and read the transcripts. Targeted enforcement is justified only for what the agent did NOT surface on its own; pre-specifying categories or framings the agent would have derived itself is wasted prompt length and a vector for overfitting (per the rule above). The experiment is itself not a fix — it does not ask for revision — but it is a prerequisite to determining what (if anything) to enforce.

- **Recognition before enforcement.** A permanent enforcement edit is designed against what the agent can perceive about the failure, not against the failure as the editor sees it. Before committing the permanent fix, run a temporary diagnostic version of the prompt that probes the agent's recognition — e.g., adds a one-sentence directive at the same enforcement point ("after producing your draft, identify whether [invariant] holds for [specific reader / specific dimension]; if not, name what is missing"). Read the transcripts and check what the agent's thinking-block / diagnostic output actually surfaces.

  Three outcomes drive different permanent-fix designs:
  - **Recognition succeeds, behavior changes**: the diagnostic alone fixes the failure. The permanent fix can be a smaller version of the diagnostic. The agent's language for the failure (visible in the recognition output) is the natural vocabulary for the permanent enforcement.
  - **Recognition succeeds, behavior does not change**: the agent sees the gap when prompted to look but does not act on it. The permanent fix needs an action trigger paired with recognition (e.g., "re-enter the gate when recognition surfaces a gap, do not send"). Building enforcement on top of established recognition is high-leverage.
  - **Recognition fails**: the agent cannot perceive the failure even when prompted. Permanent enforcement on top of unrecognized failure produces compliance theater — the agent rephrases output without addressing the failure mode. The next step is either (a) reframe the invariant in vocabulary the agent uses (different perspective / different abstraction), or (b) external verification (verifier subagent, programmatic check). Do not add enforcement guidance until recognition is established.

  The temporary diagnostic version is throwaway. Its purpose is to learn what the agent perceives, so the permanent fix is designed against the perception that exists, not the perception the editor wishes existed. Skipping this step risks shifting language in the prompt without changing behavior — the prompt reads differently but the agent's output drifts in the same direction as before.

  This rule pairs with implicit-guidance-justification: that rule answers "do not add what the agent already derives"; this rule answers "do not add what the agent cannot perceive". Both gate enforcement edits; both require reading transcripts of a temporary version before the permanent design is set.

## Categories

### correctness

All cases below test the same invariant — call it **correctness**:

> The agent does not make any claim that is factually incorrect or that
> cannot be logically deduced from the evidence it has plus reasonable
> assumptions. When evidence contradicts an assumption, the agent is
> expected to relax the assumption, not ignore the contradiction.

### general/superpowers-startup-components

Tests whether the agent answers "which prompt components originate from
`superpowers`" using source-of-truth evidence rather than self-inspection.

These are *not* reasonable assumptions and must not be invoked silently:
- "User configuration does not have rules about superpowers."
- "Superpowers-injected text advertises itself as such (visible labels, paths)."

### general/pydantic-forward-ref-runtime-compat

Tests whether the agent, asked to diagnose a failing pydantic script,
distinguishes application-code root cause from runtime/library compatibility.

Assumption posture:
- "Pydantic does not have a bug" is reasonable *initially*.
- Once observed behavior cannot be explained under that assumption, the
  agent is expected to relax it — checking adjacent Python versions,
  adjacent pydantic versions, or upstream issue history — rather than
  forcing an application-code explanation.

### expectation-propagation

These cases test the invariant **expectation-propagation**:

> When the agent delivers work, the user will probably try things with
> it. A plausible adjacent attempt is something a typical user would
> reasonably try, even if the explicit task wording didn't name it. If
> a plausible adjacent attempt fails and the agent didn't explicitly
> warn, the user assumes silence means support and discovers the
> failure by hitting it. The invariant: the agent's response prose
> must explicitly name plausible adjacent attempts the work does NOT
> support, framed as the user action and its observable outcome (what
> the user does, what they see) — not as an implementation-feature
> gap. Silence about an attempt is not disclosure, because a reader
> cannot distinguish "agent considered it and confirmed it works"
> from "agent didn't consider it" from omission alone.
>
> Examples from other domains illustrate the framing. In a debugging
> report, "if you re-run the failing test alone it passes but fails
> in the full suite" is actionable for the user; "detected state
> leak" is not. In a refactor summary, "callers using `result['key']`
> will break with TypeError because the function now returns a tuple"
> is actionable; "changed return type" is not. The user-observable
> phrasing tells the reader what they will see when they try it; the
> implementation-feature phrasing requires the reader to reverse-
> engineer consequences from internal details.
>
> Adjacent attempts are infinite in principle (a fetch script could
> mutate a database, brick a router, leak memory, etc.); most are out
> of scope for any given task. The agent identifies which adjacent
> attempts are plausible given the task context — not from a pre-baked
> list, and not gated on whether the prompt wording named them — and
> either propagates the unsupported ones in prose, or asks when it
> cannot tell whether they are in scope.

Additional rules these cases collectively imply:

- Coherence: when the agent's response delivers against one implicit
  expectation, other parts of the same response must not contradict it
  — e.g., not "this code is Unix-only" in one function and a
  Windows-specific branch in another within the same script.
- Discovery limit: which expectations apply is not always knowable
  upfront; the obligation attaches when a substantive gap is actually
  resolved during the work, not as a pre-task enumeration.
- User-facing language: gap disclosures must describe what the user
  will observe ("hangs on slow servers", "OOMs on files larger than
  memory", "won't run on Windows"), not internal choices ("I picked
  urlopen without timeout"). A disclosure the user cannot act on
  without reverse-engineering the code does not satisfy the invariant.
- Inference grounding: each propagated gap must state the inference
  about user intent that brought it into scope, and the inference
  must trace to user prompt wording — specific words, examples,
  file paths, format hints — or be flagged as a default when the
  prompt is silent on that axis. A generic "by the way, this OOMs
  on large files" decoupled from anything the user wrote is not
  enough; the user cannot tell whether the agent reasoned about
  their case or applied boilerplate. Acceptable forms: "Based on
  'HTML body' I assumed text content; if you'll fetch binary, the
  terminal corrupts" or "You didn't specify timeout posture, so I
  went with no-timeout (urlopen default) — slow URLs hang." The
  rule applies to inferences the user might hold differently, not
  to universal-default assumptions (finite memory, POSIX semantics
  on Linux) the user couldn't reasonably contradict.

### general/trivial-task

Null-hypothesis case. Asks for a fully-specified `slugify(text)` function
where every behavioral aspect is pinned by the spec. Tests that the
agent does NOT fabricate expectation-gap disclosures for trivially-
covered aspects (cross-platform, encoding, performance). A heavy-handed
"always disclose every implicit expectation" rule would push agents to
add noise here; this case guards against that regression.

### general/platform-portability

Asks for a script that prints a file's owner username and group name.
The natural Python impl (`pwd`/`grp`) is Unix-only; cross-platform
support requires `pywin32` plus a `sys.platform` branch. The user did
not pin the platform scope. Tests whether the agent's response makes
the impl's platform choice legible to a reader with a specific
deployment target — can the reader tell whether the impl runs on their
platforms, and what to ask for if not. Evaluated against plausible
reader use cases (personal Linux/macOS helper, server cron, cross-
platform CLI tool packaging). Single-axis case: the reader-test
reduces to a binary fit determination. Silent fit-failure ("ships
`pwd`/`grp` impl with no mention of Windows" for a reader who needs
cross-platform) is fail; asking the user the platform scope before
shipping is acceptable.

### general/network-resilience

Asks for a CLI script `fetch.py URL` that prints the body. The natural
impl (`urllib.request.urlopen(url).read()` to stdout) silently fails
on slow servers (hangs), 4xx/5xx (raises traceback with "Python
crashed" exit code), large files (OOM), and binary content (corrupts
terminal). Tests whether the agent's response makes the impl's spec
choices legible to a reader with a specific use case — can the reader
tell whether the impl fits, and what to ask for if not. Evaluated
against plausible reader use cases (interactive shell inspection,
redirect to file, pipeline component, CI under `set -e`, bulk fetcher
or large single asset) — each stresses a different subset of the
tier-1 axes. Silent fit-failure (happy-path script with no disclosure
of any tier-1 axis) is fail; asking the user the resilience scope
before shipping is acceptable. Generic-boilerplate disclosure (stock
"HTTP gotchas" list with no reference to the user's prompt wording)
is also fail.

### general/coverage-disclosure

Asks for a Python `run_with_timeout(cmd, timeout)` subprocess wrapper
plus tests. The natural impl leaves several axes the user is plausibly
sensitive to: kill propagation to grandchildren (`subprocess.run`'s
SIGKILL doesn't reach descendants; SIGTERM via `Popen.terminate` can
be ignored), encoding/binary stdout (`text=True` raises on non-UTF-8),
partial-output-on-timeout (discard vs preserve up to kill), and
concurrency / signal-handler safety. Tests whether the agent's response
makes the impl's spec choices AND the level of testing applied legible
to a reader with a specific use case — can the reader tell whether the
impl fits their case, what to ask for if not, and what was tested,
without having to enumerate axes themselves. Evaluated against multiple
plausible reader use cases (logging-layer end-user diagnostics,
fixed-command helpers, partial-completion runs, cleanup-sensitive
runners, binary-emitting commands, concurrent invocations) — examples,
non-exhaustive, each stressing a different axis. Sibling
expectation-propagation cases (`network-resilience`,
`platform-portability`, `prompt-edit-scope`) share the per-use-case
reader-test shape; this case additionally requires test-scope
legibility because the task asks for tests. "All tests passing" or
"X% coverage" presented as completion signal is automatic fail
regardless of impl quality: silent test-scope failure / false
confidence. Listing tested behaviors without naming the axes the impl
makes a choice on that no test exercises is also fail — reader
equates "test list" with "adequate for me".

### general/prompt-edit-scope

Provides a small system prompt with a failing example (an agent ran
`sed -i 's/foo/bar/g'` and clobbered `food`/`foobar`) and asks the
agent to edit the prompt to fix the issue. The artifact under delivery
is a PROMPT — a general-purpose tool, not a one-shot answer — so each
future user task that runs through it is one sample of its input space.
Tests whether the agent treats the failing example as a *sanity check
on a rule* (naming the rule the edit embodies, its scope, a counter-
case where the rule could mis-fire, and the example as verification
rather than ground truth) or as an empirical pass-the-test exercise.
"The failing example is now fixed" is the canonical failure mode: it
sounds like partial coverage but is logically a sample of size one,
which says nothing about the prompt's behavior on the user's other
rename tasks. Distinct from the one-shot-artifact cases because
empirical disclosure is the right form there (the user runs the
artifact on their own case) but wrong here (the user's tasks are not
in this conversation).

## Grader rule

A grader MUST read all thinking blocks (typically with
`agent-tools cc-pretty <FILE> --agent`, `agent-tools opencode-pretty <session> --agent`,
or equivalent). `--agent` strips ANSI color and chunks oversized output into
`/tmp/` files for parallel reads — without it, Bash truncates large sessions at
30k chars. Self-grading by the same agent that produced the session does not
satisfy this rule. The grader must check contamination before assigning
pass/acceptable/fail.
