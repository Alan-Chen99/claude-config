# quality_reviewer/

QR scripts, one decompose and one verify per phase (`plan_design`, `plan_code`, `plan_docs`, `impl_code`, `impl_docs`). The QR protocol, `qr-{phase}.json` and the 8-step decomposition are in the planner skill's `INTENT.md`, "QR Workflow".

## Files

| File                    | What                                                         | When to read                                  |
| ----------------------- | ------------------------------------------------------------ | --------------------------------------------- |
| `<phase>_qr_decompose.py` | The phase's decomposition into the `qr-{phase}.json` items | Changing what a phase checks |
| `<phase>_qr_verify.py`  | The phase's verification of the items it is given (repeated `--qr-item`) | Changing how a phase verifies |
| `qr_verify_base.py`     | Base class the verify scripts share: item loading, CLI, output format | Changing every phase's verify at once |
| `exec_reconcile.py`     | Whether a milestone's acceptance criteria already hold in the codebase, for resumed execution | Modifying reconciliation logic |

## Subdirectories

| Directory  | What                                                        | When to read                             |
| ---------- | ----------------------------------------------------------- | ---------------------------------------- |
| `prompts/` | `decompose.py`: the decomposition prompts identical across all five phases | Changing a decomposition step for every phase |
