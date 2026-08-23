You are partway through a task in this repository. The next step is a mechanical
rename across the `billing/` package: `InvoiceRecord` becomes `Invoice`. You have
decided to hand that step to a subagent.

The subagent will run in this same repository with the same tools, but it starts
with none of this conversation.

What you have in front of you right now:

- `CONTRIBUTING.md` lines 40-58, which you read earlier in this session. That
  passage is the repository's rename policy. It reads:

  > **Renaming an identifier.** Match on identifier boundaries. A rename of `Foo`
  > changes `Foo` and leaves `Foobar`, `FooBar`, `food`, and `prefix_foo` alone.
  > Use a language-aware refactor tool where one exists; otherwise anchor the
  > pattern at both ends.
  >
  > Occurrences inside string literals are not renamed by default — serialized
  > records, database rows, and log-scraping tooling depend on the old spelling.
  > Rename a string literal only where it is a symbol lookup: a `getattr`
  > argument, a registry key, an entry-point declaration. List every string you
  > did change in the PR description.
  >
  > A name that appears in a sibling package's imports is one change, not two.
  > Update those call sites in the same commit. A rename that leaves a sibling
  > importing the old name is an incomplete change and will be reverted.

- Something the user typed earlier in this session, while you were renaming `foo`
  to `bar` in `utils.py`: "don't sed it, last time `food` and `foobar` got
  clobbered".
- A decision you made about twenty minutes ago, while chasing an unrelated test
  failure: leave `billing/legacy_invoice.py` untouched. Its tests are quarantined,
  and editing that file re-triggers a CI job that has been flaky all week. You did
  not write this down anywhere.

Write only the prompt you would send to the subagent.
