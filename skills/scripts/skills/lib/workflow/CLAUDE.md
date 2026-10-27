# workflow/

Workflow framework: types, discovery, prompt building blocks and AST-based XML generation.

## Architecture

Skills run one CLI step at a time:

```
main() -> format_output() -> print() -> LLM reads -> follows the next-step command
```

Workflow/StepDef are metadata for discovery and tests; nothing here executes them.

## Files

| File             | What                                                 | When to read                                         |
| ---------------- | ---------------------------------------------------- | ---------------------------------------------------- |
| `README.md`      | Discovery's reach; why the question relay is shaped as it is | Adding a skill to the tests; changing the question relay |
| `core.py`        | Workflow, StepDef, Arg (metadata only)               | Defining new skills, workflow structure              |
| `discovery.py`   | Workflow discovery via importlib scanning            | Troubleshooting discovery or an import failure       |
| `__init__.py`    | Public API exports                                   | Importing workflow types                             |
| `cli.py`         | CLI helpers for workflow entry points                | Adding CLI arguments, step output helpers            |
| `constants.py`   | Shared prompt constants: HITL batching, return budget, question relay | Adding new constants                    |
| `types.py`       | Domain types: Dispatch, AgentRole, routing, test domains | QR gates, sub-agent dispatch, test domains       |
| `quality_docs.py` | Parser for the code-quality convention docs' metadata comments and mode tags | Reading those docs from a skill  |

## Subdirectories

| Directory  | What                                                        | When to read                          |
| ---------- | ----------------------------------------------------------- | ------------------------------------- |
| `prompts/` | `format_step`, `format_file_content`, the three dispatch helpers | Building a step body or a dispatch |
| `ast/`     | AST nodes, builder, renderer                                | XML generation for step output        |

## Test

From `skills/scripts/`:

```bash
pytest tests/ -v
pytest tests/ -k incoherence -v
```
