# Temporal Contamination in Code Comments

Terminology for comments that leak code history, change processes or planning
artifacts. @agent-technical-writer and @agent-quality-reviewer both apply it.

## The Core Principle

> **Timeless Present Rule**: Comments must be written from the perspective of a
> reader encountering the code for the first time, with no knowledge of what
> came before or how it got here. The code simply _is_.

In a plan, comments are written _as if the plan was already executed_.

The fix for every category: **extract the technical justification, discard the
change narrative** -- find the useful information buried in the comment
(problem, behavior) and restate it in the timeless present.

## Detection Heuristic

Evaluate each comment against these five questions. Signal words are examples
-- extrapolate to semantically similar constructs.

### 1. Does it describe an action taken rather than what exists?

**Category**: Change-relative

| Contaminated                           | Timeless Present                                            |
| -------------------------------------- | ----------------------------------------------------------- |
| `// Added mutex to fix race condition` | `// Mutex serializes cache access from concurrent requests` |
| `// Changed to use batch API`          | `// Batch API reduces round-trips from N to 1`              |

Signal words: "Added", "Replaced", "Now uses", "Changed to", "New", "Updated",
"Refactored"

### 2. Does it compare to something not in the code?

**Category**: Baseline reference

| Contaminated                               | Timeless Present                                                    |
| ------------------------------------------ | ------------------------------------------------------------------- |
| `// Replaces per-tag logging with summary` | `// Single summary line; per-tag logging would produce 1500+ lines` |
| `// Previously handled in caller`          | `// Encapsulated here; caller should not manage lifecycle`          |

Signal words: "Instead of", "Rather than", "Previously", "Replaces", "Unlike the
old", "No longer"

### 3. Does it describe where to put code rather than what code does?

**Category**: Location directive (e.g., `// After the SendAsync call`,
`// Add this at line 425`)

Signal words: "After", "Before", "Insert", "At line", "Here:", "Below", "Above"

**Action**: Always delete. Location is encoded in diff structure, not comments.

### 4. Does it describe intent rather than behavior?

**Category**: Planning artifact

| Contaminated                           | Timeless Present                                         |
| -------------------------------------- | -------------------------------------------------------- |
| `// TODO: add retry logic later`       | _(delete, or implement retry now)_                       |
| `// Will be extended for batch mode`   | _(delete -- do not document hypothetical futures)_       |
| `// Temporary workaround until API v2` | `// API v1 lacks filtering; client-side filter required` |

Signal words: "Will", "TODO", "Planned", "Eventually", "For future",
"Temporary", "Workaround until"

**Action**: Delete, implement the feature, or reframe as a current constraint.

### 5. Does it describe the author's choice rather than code behavior?

**Category**: Intent leakage

| Contaminated                               | Timeless Present                                     |
| ------------------------------------------ | ---------------------------------------------------- |
| `// Intentionally placed after validation` | `// Runs after validation completes`                 |
| `// Chose polling for reliability`         | `// Polling: 30% webhook delivery failures observed` |

Signal words: "intentionally", "deliberately", "chose", "decided", "on
purpose", "by design", "we opted"

**Action**: The reader needs WHY the approach works, not that someone decided.
Test: delete the intent word; if the comment still makes sense, leave it
deleted, otherwise reframe around the technical reason.

**Catch-all**: If a comment only makes sense to someone who knows the code's
history, it is temporally contaminated -- even if it matches no category above.

## Subtle Cases

Same word, different verdict: detection needs semantic judgment, not keyword
matching.

| Comment                                | Verdict      | Reasoning                                        |
| -------------------------------------- | ------------ | ------------------------------------------------ |
| `// Now handles edge cases properly`   | Contaminated | "properly" implies it was improper before        |
| `// Now blocks until connection ready` | Clean        | "now" describes runtime moment, not code history |
| `// Fixed the null pointer issue`      | Contaminated | Describes a fix, not behavior                    |
| `// Returns null when key not found`   | Clean        | Describes behavior                               |
