# Unified Diff Format for Plan Code Changes

This document is the authoritative specification for code changes in
implementation plans. A unified diff encodes **location** and **content** in one
structure, so comments need no location directives (e.g., "insert at line 42")
and anchoring survives line-number drift.

## Anatomy

```diff
--- a/path/to/file.py
+++ b/path/to/file.py
@@ -123,6 +123,15 @@ def existing_function(ctx):
    # Context lines (unchanged) serve as location anchors
    existing_code()

+   # NEW: Comments explain WHY - transcribed verbatim by Developer
+   # Guard against race condition when messages arrive out-of-order
+   new_code()

    # More context to anchor the insertion point
    more_existing_code()
```

| Component                                  | Authority                 | Purpose                                                    |
| ------------------------------------------ | ------------------------- | ---------------------------------------------------------- |
| File path (`--- a/path/to/file.py`)        | **AUTHORITATIVE**         | Exact target file                                          |
| Line numbers (`@@ -123,6 +123,15 @@`)      | **APPROXIMATE**           | May drift as earlier milestones modify the file            |
| Function context (`@@ ... @@ def func():`) | **SCOPE HINT**            | Function/method containing the change, as git emits it     |
| Context lines (unchanged)                  | **AUTHORITATIVE ANCHORS** | Developer matches these patterns to locate insertion point |
| `+` lines                                  | **NEW CODE**              | Code to add, including WHY comments                        |
| `-` lines                                  | **REMOVED CODE**          | Code to delete                                             |

When several milestones modify one file, earlier ones shift line numbers: the
`@@ -123` in Milestone 3 may be wrong after Milestones 1 and 2. Developer
searches the actual file for the unchanged context lines instead, so include
2-3 of them before and after each change.

## Prose Scope Hints

For a complex change, say before the diff where it goes conceptually (which
method, what operation precedes it), e.g. "Add validation after input
sanitization in `UserService.validate()`:"; the diff's context lines say where
exactly.

- Use one for files over 300 lines, several changes to one file in one
  milestone, nested structures where the function context alone is ambiguous,
  or when the surrounding logic matters for placement.
- Optional for small files with obvious structure, a single change with unique
  context lines, or when the `@@` function context gives enough scope.

## Comment Placement

Comments in `+` lines are transcribed verbatim by Developer. They explain
**WHY**, not **WHAT**, source their rationale from Planning Context (Decision
Log, Rejected Alternatives), use concrete terms without hidden baselines, and
must pass temporal contamination review (`.claude/conventions/temporal.md`).
Planning-time comments often carry change-relative language, baseline
references or location directives: @agent-technical-writer fixes these before
@agent-developer transcribes them.

| Wrong                                                         | Right                                                                              |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `# Poll the API every 30 seconds` (restates WHAT)             | `# Polling chosen over webhooks: 30% webhook delivery failures in third-party API` |
| `# Generous timeout for slow networks` (compared to what?)    | `# 60s accommodates 95th percentile upstream response times`                       |
| `# Insert this BEFORE the retry loop (line 716)` (goes stale) | No location comment: context lines such as `for tag in tags:` anchor it            |

## When to Use Diff Format

| Code Characteristic                                    | Use Diff? | Boundary Test                            |
| ------------------------------------------------------ | --------- | ---------------------------------------- |
| Conditionals, loops, error handling, state machines    | YES       | Has branching logic                      |
| Multiple insertions same file                          | YES       | >1 change location                       |
| Deletions or replacements                              | YES       | Removing/changing existing code          |
| Pure assignment/return (CRUD, getters)                 | NO        | Single statement, no branching           |
| Boilerplate from template                              | NO        | Developer can generate from pattern name |

The boundary test: "Does Developer need to see exact placement and context to
implement correctly?" YES -> diff format; NO (can implement from description
alone) -> prose is sufficient.

## Validation Checklist

Before finalizing code changes in a plan:

- [ ] File path is exact (not "auth files" but `src/auth/handler.py`)
- [ ] Context lines exist in target file (validate patterns match actual code)
- [ ] 2-3 context lines for reliable anchoring
- [ ] Comments explain WHY, not WHAT
- [ ] No location directives in comments
- [ ] No hidden baselines (test: "[adjective] compared to what?")
