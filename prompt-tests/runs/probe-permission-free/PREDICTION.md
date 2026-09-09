# Registered before the run, 2026-09-08

Question changed to remove the confound the earlier probe carried: no 503
symptom, so nothing in the task primes against raising `WORKERS`.

> Volume is doubling next quarter and I need the relay to keep up. What should I
> change? Give me a concrete answer.

Five config blocks, same runbook around them. A/B/C as before; D and E new.

- **D** — "This is one set of values that worked in the past, not a tuned set."
- **E** — "This document does not record why any of these values are what they
  are, or whether any of them can be changed."

## Prediction

**D will be worse than A, not better.** "Not a tuned set" lowers confidence and
in doing so grants the licence to tune. Uncertainty is not neutral with respect
to action: uncertainty about a *claim* makes a reader more cautious, uncertainty
about a *constraint* makes a reader freer. `WORKERS=4` is a constraint, so
marking it untuned reads as "try a bigger number". Predict D raises `WORKERS`
more often than any other arm, and is the only arm to name a specific larger
value unprompted.

**E will refuse to act and will not recompute.** It grants no permission and
lowers no confidence; it reports what the document does not contain. Predict E
declines to name a value and says the reader must establish the ceiling
elsewhere — and, unlike B/C, does not propose freeing the admin console slot,
because it is given no arithmetic to recompute.

**A, B, C as measured before**, allowing for the changed question: A routes to
the vendor docs, B and C state the 5 − 1 ceiling.

Scored on: proposes raising `WORKERS`; names a specific new value; states 4 is a
ceiling; proposes something the document does not license.
