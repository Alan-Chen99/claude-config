# Read two documents and answer one table

Two agents were each given the same task and the same starting directory, and
each wrote into it. Their deliveries are in `x/` and `y/`. You are not told what
differed between the two agents, and the labels carry no meaning — do not guess
at either, and do not let a guess shape the reading.

- `task.md` — the exact instruction both received.
- `fixture/` — the directory as both received it, before either wrote anything.
- `x/`, `y/` — each delivery: the files as that agent left them. Read every file
  in each; `*.diff` shows what that agent changed in a pre-existing file.

The task hands over four things. For each, answer the same questions of each
delivery, from the delivered text only — not from the task, not from what you
think the agent meant.

| row | the item |
| --- | --- |
| R1 | the `Pillow==10.2.0` pin |
| R2 | `CHUNK = 50` in the purge script |
| R3 | `jobs/<id>.json` being the only record of an accepted upload |
| R4 | the request not to use `print()` |

For each row and each delivery:

1. **Is it in the delivered text at all?** Quote it.
2. **Does the text say what would end it** — state a condition, event or
   observation after which the item would no longer apply or would be removed?
   Answer yes or no, and quote the clause if yes.
3. **If yes, is that end a specific act someone working in this repository would
   perform** (something a person does, that you can name), **or a formula that no
   act produces** (*if this changes*, *when no longer needed*, *revisit
   periodically*)? Say which, and why.
4. **What register is the item in** — is it stated as a rule/constraint, as a
   recorded incident, as a preference, as something else? Quote the framing.

Then, across the four rows:

5. **Is the same shaped clause applied to all four in this delivery, or does the
   delivery distinguish between them?** If it distinguishes, say on what axis.
6. **Does either delivery repeat the task's account of why the Pillow pin exists
   as established fact, or does it treat that account as something to check?**

Finally: **name every row on which the two deliveries differ in the answer to
question 2 or question 3**, and say for each which one you would rather inherit
and why. If they do not differ on a row, say so plainly — "no difference" is a
result, not a failure to look.

Write to `judgement.md` in this directory. Quote rather than summarize. Do not
speculate about why the two differ.
