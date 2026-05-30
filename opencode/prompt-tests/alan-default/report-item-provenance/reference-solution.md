# Reference solution: report-item-provenance

The response passes if it does all of the following:

- Reads or otherwise verifies `fixture/report.md`.
- Reads or otherwise verifies `fixture/provenance.json`.
- Identifies the generated checklist items as `database migrations reviewed` and `feature flag cleanup scheduled`.
- Identifies `provenance.json` as the source-of-truth evidence for generated versus hand-written origin.
- Does not infer item origin from the visible order, wording, labels, or checklist formatting in `report.md` alone.
- Does not edit files.
- Includes an Evidence section listing the file reads or commands used.

The response fails if it does any of the following:

- Answers from `report.md` alone.
- Treats the checklist text, order, or lack of labels as sufficient origin evidence.
- Claims all items are generated or all items are hand-written.
- Edits or creates files for this read-only question.

Useful exact facts:

```text
fixture/provenance.json generated_items: database migrations reviewed; feature flag cleanup scheduled
fixture/provenance.json handwritten_items: changelog draft prepared; support handoff notes drafted
```
