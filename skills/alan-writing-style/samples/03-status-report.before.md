## Writing style skill: status

We want a skill that writes or rewrites text in my style, replacing current `alan-writing-style` (a renamed copy of `leon-writing-style`: the voice is not mine, the 9-step script echoes `--thoughts` back every step, and upstream has dropped the skill).

Done:

- Research. Two opus subagents surveyed current humanizer skills and detection papers. Findings: AI tells are model specific and drift (em dash is no longer a claude tell); removing flagged words alone does not beat detectors; ~5 real samples saturate a voice profile.
- Corpus. 251 long prompts from `history.jsonl` (23.7k words). PROMPT.md git history is not usable as-is, it contains agent edits committed under my name. Example, same file 6 lines apart:
  > Unless the prior thread attempt, you should work more efficently and focus on the core of the task -- provide a working set of mechanic to enforce the key EP invaraint.
  > Unlike the prior attempt, work more efficiently and focus on the core of the task — provide a working set of mechanics to enforce the key EP invariant.
- Profile. Two subagents extracted traits. Stable across chat and docs (counted, not by impression): explanatory colon, single ` -- `, coined terms in quotes, hedges that say what kind of confidence. None of the catalogued AI tells appear.

Open: doc conventions (capitalization, contractions, enumeration) -- prompts do not show these. Also which content types the skill covers.

Next: agent writes, I edit, repeat; then design, spec, plan, single SKILL.md.
