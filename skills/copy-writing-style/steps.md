<!-- step 1: extract -->

# COPY WRITING STYLE - Step 1: Style Extraction

Read the style reference file below. Your goal: identify what makes this style
distinctive enough to reproduce.

## Style Reference

{STYLE_REF_CONTENT}

## Extraction

Identify the 3-5 most distinguishing features of this style, ranked by how
much they would be missed if absent. A "feature" can be structural, linguistic,
rhetorical, tonal, or anything else you notice.

If the style has a performance layer (the writer is performing a role, there is
subtext, irony, or dramatic situation), this IS the most distinguishing feature.
Rank it first.

Output a ranked list:
1. Most distinctive: [what it is and how it works]
2. Second: [...]
3. Third: [...]
(up to 5)

NEXT STEP:
<invoke cmd="agent-tools skill copy_writing_style.do --step 2" />
Execute this command now.

<!-- step 2: draft -->

# COPY WRITING STYLE - Step 2: Draft

Write or rewrite the content now, focusing on your ranked features from step 1.
The top-ranked feature matters most — if you nail that and miss #4, the result
will still feel right. If you nail #4 and miss #1, it won't.

For rewrites: identify what already matches and what clashes, then transform
the clashing parts.

Output the full draft.

NEXT STEP:
<invoke cmd="agent-tools skill copy_writing_style.do --step 3 --iteration 0" />
Execute this command now.

<!-- step 3: iterate -->

# COPY WRITING STYLE - Step 3: Iterate (round {ITERATION})

Your draft is in the conversation above. The reference is below.

## Style Reference (for comparison)

{STYLE_REF_CONTENT}

## Critique

Suppose a reader familiar with the reference says your draft "feels a bit off."
What is the single biggest cause? Compare your draft directly to the reference
— not to your extracted features (which may be incomplete).

To deliver as final: first quote 1-2 passage pairs (your text vs reference in
similar position, or full text if reference is short). State specifically what
makes them sound like the same author. If they do — deliver the final content.

Otherwise:
1. State the single biggest difference
2. Fix it
3. Output the revised draft

NEXT STEP:
<invoke cmd="agent-tools skill copy_writing_style.do --step 3 --iteration {NEXT_ITERATION}" />
Execute this command now.
