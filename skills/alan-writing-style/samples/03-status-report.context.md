Piece: a status report on the writing-style skill work, as a note to the user. Register: doc.

(Reconstructed after the fact from the draft; the ai draft was written from the session's own state, not from this sheet.)

Facts:
- Goal: a skill that writes or rewrites text in Alan's style, replacing `alan-writing-style`, which is a renamed copy of upstream `leon-writing-style` (Leon's voice; a 9-step script that echoes `--thoughts` back every step; upstream has dropped the skill).
- Research: two opus subagents surveyed humanizer skills and detection papers. Findings: AI tells are model specific and drift (em dash is no longer a claude tell); removing flagged words alone does not beat detectors; about 5 real samples saturate a voice profile.
- Corpus: 251 long prompts from `history.jsonl`, 23.7k words. PROMPT.md git history is unusable as-is: agent edits committed under Alan's name. Example from one file, 6 lines apart:
  Unless the prior thread attempt, you should work more efficently and focus on the core of the task -- provide a working set of mechanic to enforce the key EP invaraint.
  Unlike the prior attempt, work more efficiently and focus on the core of the task — provide a working set of mechanics to enforce the key EP invariant.
- Profile: two subagents extracted traits. Stable across chat and docs by count: explanatory colon, single ` -- `, coined terms in quotes, hedges naming the kind of confidence. None of the catalogued AI tells appear.
- Open: doc conventions (capitalization, contractions, enumeration) are not visible in prompts; which content types the skill covers.
- Plan: a single `SKILL.md`. Next: agent writes, Alan edits, repeat; then design, spec, plan.
