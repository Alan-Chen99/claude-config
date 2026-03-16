## Testing Patterns

### Universal Preferences

**Module-level functions, no test classes** (unless a framework requires them).

**Integration/E2E style over heavy mocking.** Test real behavior end-to-end.
Mock only external services and I/O boundaries.

**`pytest-subtests` over `parametrize`** for iterating over cases:
```python
def test_examples(subtests: SubTests):
    for f in examples_dir.iterdir():
        with subtests.test(msg=f.name):
            ...
```

**Shared utilities in `test_utils.py`**, not `conftest.py` (conftest only for
autouse setup fixtures).

**Output comparison via golden files.** Test output files written to
`tests/outputs/` for comparison.

