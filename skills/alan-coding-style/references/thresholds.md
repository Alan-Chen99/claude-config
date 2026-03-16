## Decision Thresholds

Quick-reference decision rules:

- **When to abstract:** 3+ implementations → base class/protocol. <3 → inline.
- **When to extract helper:** >=3 call sites OR distinct testable concern OR
  independent concept. Otherwise leave inline.
- **When to use registry:** 5+ pluggable items in an ordered pipeline. <5 → inline.
- **When to split files:** >1000 lines AND >3 conceptual sections. Otherwise keep
  together.
- **When to create subdirectory:** >3 related internal modules.
- **When to add a dependency:** stdlib does >=80% of what you need → use stdlib.
  Otherwise evaluate the dep.
- **Framework deference:** Use framework patterns at integration points (e.g.,
  decorators for routes, DI for services). Use Alan's patterns for business logic.
