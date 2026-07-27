## Round 9: R910 diagnostic + instruction/context ambiguity

Motivated by 10a (what is an instruction? the PROMPT.md line-9 caveat *"consider invalid / idea only"* was correctly interpreted by baseline V5 but mishandled or ignored across many earlier rounds). Two meta-hypotheses:
1. **Non-rule text may be interpreted as rules** — fixture-directory guidance, user-prompt phrases, environmental observations.
2. **Invisible influences on behavior are a discoverability gap** — everything shaping the agent's output is opaque without carefully-designed probes.

R910 added to `min.md` as a diagnostic instrument: *"list the rules or instructions you applied per commentary."* Designed as passive telemetry, not as a fix for F46.

**F50 — diagnostic instrument alters the phenomenon it measures (behavioral finding).** R910 v4 (v3's list-model + purpose sentence *"sometimes users or the system are not aware that a specific instruction is causing problems; you help by telling…"* + body *"rules or instructions"*) broke F46 skip at 2/2 replicates (v4a=7 reads, v4b=5 reads into `/root/claude-config-work/`). But the mechanism is not what the purpose text says.

2×2 ablation (n=8, {no-purpose, purpose} × {rules, rules or instructions}) plus mechanism probes (E6 generic purpose, E7 purpose says "rules" not "instructions", E8 direct R920 base-rate rule) pinned the immediate mechanism:

- The F46 magnitude requires the *interaction* of both changes; neither alone reproduces it.
- The effect comes from **scope-wording alignment** between R910's purpose sentence and body. Coherent broad scope ("instructions" in both) → agent casually extends attention to task-embedded content → happens to read the older loop. E6 replaces "detect problematic instructions" with a bland substitute; behavior preserved. The literal purpose text is not the operative element.
- E7 swaps one word (purpose "instructions" → "rules"); F46 collapses to 0 reads and the caveat is *explicitly honored*.

**R910 v4 must not be adopted as a spec addition.** A rule whose behavior can't be predicted from its text is not defensible for a global spec, even when the behavior is what you want. F54's alternative (R920, direct base-rate rule) achieves the same F46 magnitude via a mechanism whose text matches its effect — the agent explicitly reasons through the caveat and produces a rejectable argument — but R920 is a case-fitted rule that names the specific F46 scenario. Also not adoptable (overfitted).

**F55 — attention loss (baseline, restated from round 8) is what needs addressing.** R910 v4's F46 break is a side effect that happens to move this symptom on this fixture; the underlying pattern (well-generated candidate lost to competing candidates) is untouched by any R910 variant, R920, or the current R002 stack.

**F57 — the agent has no stable definition of "instruction" (behavioral finding).** Categorization of 498 rules-applied entries across 10 R910 sessions:

- Body wording `rules` → agent enumerates formal R### rules + skill-directory guidance (`prompt-engineer-v2:prompts are code`, `prompt-tests:pass percentage is not the target`, etc.). Skill-directory files are not formal rules but were honored as binding. **Direct evidence for meta-hypothesis 1.**
- Body wording `rules or instructions` → adds user-prompt sub-directive fragments (`<user:no edits>`, `<user:predict endpoint not intermediate>`, etc.).
- Purpose framing further gates on top: E7 shows that even permissive body wording gets narrowed if purpose scope disagrees.
- Task-embedded caveats (PROMPT.md line 9) essentially never enumerated (1/498 across all variants).

The agent decides on-the-fly per list what to include. **Any principled definition of "instruction" has to be written into the rule; the model does not supply one.**

**F60 — purpose framing gates caveat-classification (behavioral finding).** After F56 declared the mechanism unresolved at trace level, E9 (R910 at end-of-task, not per-commentary) still produced F46 reads at 1/2 replicates — per-commentary enumeration is not the mechanism. E10 (broad body + minimal purpose *"log which rules or instructions you honored"*) produced F46 reads *with explicit caveat engagement*:

> *"I'll sample the old-loop context referenced by PROMPT.md only enough to see whether it contains a missed architecture, not to re-litigate every trial."* Rules applied: `R044, R045, prompt-engineer-v2:avoid overfitting to the case at hand, <user: old loop invalid/idea-only>`

Contrast v4a which read *without* caveat engagement. **The interpersonal helping frame in v4's purpose sentence** (*"sometimes users or the system are not aware… you help by telling…"*) **specifically suppresses caveat-as-instruction classification** when reads happen. Strip the helping frame (E10), keep broad scope, and the caveat gets promoted to instruction-set membership.

This is meta-hypothesis 1 empirically visible: whether a piece of task-embedded text gets treated as an instruction depends on the framing around what counts as an instruction, not on any property of the text itself. F57 refined: purpose framing implicitly *decides* what qualifies for enumeration on-the-fly.
