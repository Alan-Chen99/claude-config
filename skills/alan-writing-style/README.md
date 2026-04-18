# Alan Writing Style

Style-matched content generation and review. The skill orchestrates a 9-step
workflow (classify -> purpose -> draft -> detect AI tells -> positive markers ->
voice alignment -> consolidate -> refine -> quality gate) driven by
`writing_style.py`.

## Invisible Knowledge

### Why Progressive History Instead of Flat Template

The history template is progressive -- it shows only sections the LLM has
already created in prior steps. At step 2, only Classification is visible.
By step 8, all sections are visible. This prevents the LLM from being
confused by placeholder sections it hasn't filled yet.

### Why Step-Back Principles Use Meta-Cognitive Questions

Step 3 uses Step-Back Prompting (Zheng et al., 2023). Two questions ("What
makes Alan's voice distinctive?" and "What would make this sound AI-generated?")
prime the agent to retrieve first principles before drafting.

### Why Overflow Steps Have Focus Variation

Steps beyond 9 produce diminishing returns. Step 10 focuses on HIGH-confidence
violations, step 11 on MED-confidence, step 12+ notes diminishing returns.
This prevents the agent from endlessly re-checking resolved items.

### Why No Resource File Loading

Unlike alan-coding-style which loads reference files from `references/*.md`,
writing style rules are embedded directly in the step actions. Writing style
checks are self-contained descriptions of patterns to detect, not reference
material that varies by task type.
