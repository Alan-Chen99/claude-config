<contrastive_examples>
CONTRASTIVE EXAMPLES

  Use these to calibrate your detection. Each pair shows the same idea
  expressed with and without the AI tell.

  TRICOLONS (pattern 1):
    WRONG: 'The system provides clear context, focused execution, and reliable results.'
    RIGHT: 'The system gives you context before execution. Results are reproducible.'
    WHY WRONG: Manufactured three-part rhythm. Real writing uses uneven counts.

    WRONG: 'It's fast, flexible, and production-ready.'
    RIGHT: 'It's fast. We've run it in production for six months.'

  CONTRARIAN OPENERS (pattern 2):
    WRONG: 'Code review isn't a gate -- it's a conversation.'
    RIGHT: 'I review code in the PR, not in a meeting.'
    WHY WRONG: Negation-then-reframe adds rhetorical drama, not information.

    WRONG: 'This is not about testing. It's about confidence.'
    RIGHT: 'The tests tell me whether the deploy is safe.'

  DEAD METAPHORS (pattern 3):
    WRONG: 'Building on a solid foundation of shared understanding.'
    RIGHT: 'Everyone reads the same spec before writing code.'
    WHY WRONG: 'Solid foundation' is dead on arrival. Name the actual thing.

    WRONG: 'Navigating the ever-evolving landscape of cloud infrastructure.'
    RIGHT: 'AWS changed their pricing model twice this year.'

  HOLLOW EMPHASIS (pattern 4):
    WRONG: 'It's important to note that error handling matters.'
    RIGHT: 'Without error handling, the queue backs up and pages oncall at 3am.'
    WHY WRONG: Announcing importance is not showing it. Show the consequence.

    WRONG: 'This is a crucial step in the deployment pipeline.'
    RIGHT: 'Skip this step and the canary won't catch regressions.'

  EXPLICIT CALLBACKS (pattern 5):
    WRONG: 'Just like we saw during planning, the review catches drift.'
    RIGHT: 'The review catches drift.'
    WHY WRONG: 'Just like we saw' patronizes the reader. They remember.

  FORMULA FOLLOWING (pattern 6):
    WRONG: Every paragraph: topic sentence, two supporting sentences, transition.
    RIGHT: Some points get one sentence. Some get a full paragraph. One gets a parenthetical.
    WHY WRONG: Uniform paragraph structure is the most detectable AI pattern.

  EUPHEMISTIC LANGUAGE (pattern 8):
    WRONG: 'The team experienced alignment challenges that necessitated a transition.'
    RIGHT: 'We fired the contractor after three missed deadlines.'
    WHY WRONG: Corporate euphemism hides the plain meaning.

  META-COMMENTARY OPENERS (pattern 10):
    WRONG: 'In this post, I'll walk you through how we built our deploy pipeline.'
    RIGHT: 'Our deploy pipeline runs 400 deploys a day. Here's the architecture.'
    WHY WRONG: Describes the text instead of the subject. Start with the thing.

    WRONG: 'Let me explain why we chose this approach.'
    RIGHT: 'We chose Postgres over DynamoDB because we need transactions.'

  OVER-JUSTIFICATION (pattern 13):
    WRONG: 'Automated testing catches regressions -- the kind that slip through
            manual review and compound into production incidents that erode user trust.'
    RIGHT: 'Automated testing catches regressions.'
    WHY WRONG: The em-dash clause defends against an unstated 'so what?'
               State the fact. If the reader doesn't see the value, they'll ask.

  COMBINED -- FULL PARAGRAPH:
    WRONG: 'Code review is not just a quality gate -- it's a crucial mechanism for
            knowledge sharing, mentorship, and continuous improvement. By fostering
            a culture of constructive feedback, teams can navigate complex codebases
            more effectively, ensuring that best practices are maintained and
            technical debt is proactively addressed.'

    RIGHT: 'I review every PR before it merges. Takes about 20 minutes. I've caught
            three bugs this month that would have hit production. The junior devs
            pick up patterns from the comments -- last week Sarah started using
            the same error-wrapping style without being asked.'

    WHY WRONG: The first version has tricolons ('knowledge sharing, mentorship,
               and continuous improvement'), dead metaphors ('navigate complex
               codebases'), hollow emphasis ('crucial mechanism'), a contrarian
               opener ('not just... it's'), and over-justification ('ensuring
               that... proactively addressed'). Five patterns in one paragraph.
               The second version has specific numbers, a named person, and
               a concrete anecdote.
</contrastive_examples>
