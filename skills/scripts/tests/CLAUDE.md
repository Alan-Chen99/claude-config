# tests/

Test suite for skills workflow framework.

## Rules

All tests must live in `tests/` and run through pytest. No test files elsewhere in the codebase.

A new skill gets the import test only once its entry module is in `SKILL_MODULES` (`conftest.py`), and the step tests only if it defines a module-level `WORKFLOW` (`../skills/lib/workflow/README.md`, "Discovery").

## Files

| File                         | What                                                 | When to read                               |
| ---------------------------- | ---------------------------------------------------- | ------------------------------------------ |
| `conftest.py`                | `SKILL_MODULES`, `EXCLUDED`, the subprocess step runner | Modifying test setup, adding a skill to the tests |
| `test_workflow_import.py`    | Skill module import tests                            | Debugging import failures                  |
| `test_workflow_structure.py` | Workflow structural validation tests                 | Debugging validation failures              |
| `test_workflow_steps.py`     | Every step of every discovered workflow, run as a subprocess with each generated input | Running workflow tests, debugging failures |
| `test_domain_types.py`       | Unit tests for BoundedInt, ChoiceSet, Constant       | Testing domain type behavior               |
| `test_generation.py`         | Schema extraction and input generation for tests; why enumeration is exhaustive | Modifying test case generation |
| `test_ast.py`                | Property-based AST node and renderer tests           | Testing AST construction and rendering     |
| `test_qr_verify_routing.py`  | QR verify step arithmetic: context, analyze/confirm per item, summary | Changing the verify step layout |
| `test_alan_coding_style.py`  | Unit and behavioral tests for alan-coding-style workflow | Modifying alan-coding-style, debugging quality gate or threshold behavior |

## Test Execution

From `skills/scripts/`:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_workflow_steps.py -v

# Run tests for specific workflow
pytest tests/ -k incoherence -v
```
