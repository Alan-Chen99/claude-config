# Plan: Replace `output_type=str` with Structured Output + Reduce `cast()` Ceremony

## Context

Commit `99bd0bb3` added ~95 `cast()` calls to satisfy basedpyright strict mode. All 24 `call_simple_model_once` call sites use `output_type=str`, bypassing pydantic_ai's built-in structured output. Five call sites immediately parse JSON from the string output via `extract_first_json_object()` or `json.loads()`, followed by manual isinstance guards and cast ceremonies. This is the highest-ROI migration target.

The backlog item defines three tiers of work. This plan addresses all three.

---

## Tier 1: Use `output_type=BaseModel` (Highest ROI)

### Target call sites (5 of 24 use `output_type=str` then parse JSON)

| Call site | File | Line | Current pattern |
|-----------|------|------|-----------------|
| Options generation | `essay_wb/stages/create_and_cluster_outlines/pipeline.py` | 192 | `extract_first_json_object` → `parse_options()` |
| Grade/scoring | `essay_wb/stages/create_and_cluster_outlines/pipeline.py` | 393 | `extract_first_json_object` → `parse_grade_result()` |
| Clustering | `essay_wb/stages/create_and_cluster_outlines/pipeline.py` | 617 | `extract_first_json_object` → membership validation |
| Eval judge | `essay_wb/stages/eval_style_humanization/pipeline.py` | 279 | `_parse_judge_json()` → `_score_from_judge_output()` |

**NOT migrated** (correct as `output_type=str`):
- Features extraction (`create_and_cluster_outlines/pipeline.py:353`) — schema is freeform/dynamic (`predictions_direction_*`), not structurable
- All `outline_to_essay` calls — return free-form markdown, not JSON
- All `style_humanization` calls — return free-form text
- All `infra_tests` calls — test infrastructure

### New Pydantic models

Create `essay_wb/stages/create_and_cluster_outlines/models.py`:

```python
class OptionItem(BaseModel):
    id: str
    topic_framing: str
    stance_label: str
    title: str
    one_sentence_pitch: str
    thesis_paragraph: str
    key_sections: list[str]
    distinctiveness: list[str]
    predictions_1y: list[str]
    predictions_3y: list[str]

class OptionsOutput(BaseModel):
    options: list[OptionItem]
    meta_commentary: str = ""

class OutlineGrade(BaseModel):
    overall_score_0_100: int
    scores: dict[str, Any]
    summary: str
    top_strengths: list[str]
    top_issues: list[str]
    missing_evidence: list[str]
    suggested_revisions: list[str]

class ClusterEntry(BaseModel):
    name: str
    description: str
    members: list[str]

class ClusterAxes(BaseModel):
    topic_framing_notes: str = ""
    stance_notes: str = ""

class ClusterOutput(BaseModel):
    clusters: list[ClusterEntry]
    axes: ClusterAxes = ClusterAxes()
    notes: list[str] = []
```

Create `essay_wb/stages/eval_style_humanization/models.py`:

```python
class AiTell(BaseModel):
    pattern: str = ""
    evidence: str = ""
    severity: str = ""

class JudgeOutput(BaseModel):
    overall_score: float = 0.0
    subscores: dict[str, float] = {}
    ai_tells: list[AiTell] = []
    reasoning: str = ""
```

### Migration details per call site

**1. Options generation** (`create_and_cluster_outlines/pipeline.py:192`)
- Change `output_type=str` → `output_type=OptionsOutput`
- Keep outer retry loop (increases `max_tokens` on retry) but catch structured-output validation errors instead of checking `extract_first_json_object`
- Replace `parse_options(options_obj, expected_n=...)` with direct access to `res.output.options`. Move `expected_n` check + stance_label / key_sections validation to a simpler post-validation function that operates on `list[OptionItem]`
- Remove `extract_first_json_object` import if no longer needed
- Removes cast sites in `core.py:173,180` (parse_options simplified)

**2. Grade/scoring** (`create_and_cluster_outlines/pipeline.py:393`)
- Change `output_type=str` → `output_type=OutlineGrade`
- Keep outer retry loop (adds retry note to prompt) but catch validation errors
- `parse_grade_result()` in `core.py` can be simplified or removed — the Pydantic model enforces types
- The score coercion (`str→int`, `float→int`) can become a Pydantic validator on `overall_score_0_100`

**3. Clustering** (`create_and_cluster_outlines/pipeline.py:617`)
- Change `output_type=str` → `output_type=ClusterOutput`
- Keep outer retry loop for membership validation (semantic check can't be in schema)
- `_membership_errors_for` simplified: access `parsed.clusters[i].members` directly instead of isinstance+cast dance
- `render_cluster_report_markdown` in `outlines/cluster_report.py`: change to accept `ClusterOutput` model, eliminating ~5 cast sites. (Trace all callers first to confirm no raw-dict callers exist.)

**4. Eval judge** (`eval_style_humanization/pipeline.py:279`)
- Change `output_type=str` → `output_type=JudgeOutput`
- Remove `_parse_judge_json()` entirely
- Simplify `_score_from_judge_output()` to accept `JudgeOutput` instead of `dict[str, object]` — direct attribute access, no isinstance+cast needed. Removes cast sites at lines 95, 102, 105.

### Preflight compatibility

Update `_placeholder_for_output_type` in `essay_wb/stage_llm.py:88` to handle BaseModel subclasses:

```python
from pydantic import BaseModel as PydanticBaseModel

def _placeholder_for_output_type(output_type: type[_T]) -> _T:
    ...existing checks...
    if isinstance(output_type, type) and issubclass(output_type, PydanticBaseModel):
        return cast(_T, output_type.model_construct())
    try:
        return output_type()
    ...
```

### Meta commentary concern

Not an issue. All 4 migrated call sites use prompts that say "Return JSON only" / "Output ONLY valid JSON". They don't produce free-form meta commentary. The `split_meta_commentary` path (only active for `output_type=str`) is irrelevant for these calls. The `meta_commentary` field in the options JSON schema is a structured field within the JSON, not the free-form meta commentary that `split_meta_commentary` extracts.

---

## Tier 2: `checked_dict` / `checked_list` Utility

### New utility file: `essay_wb/utils/checked_types.py`

```python
def checked_dict(val: Any, msg: str = "") -> dict[str, Any]:
    if not isinstance(val, dict):
        raise TypeError(msg or f"Expected dict, got {type(val).__name__}")
    return cast(dict[str, Any], val)

def checked_list(val: Any, msg: str = "") -> list[Any]:
    if not isinstance(val, list):
        raise TypeError(msg or f"Expected list, got {type(val).__name__}")
    return cast(list[Any], val)
```

### Target sites (~20 remaining after Tier 1 removes some)

Replace the `isinstance(x, dict/list)` + `cast()` pattern at:

- `essay_wb/sources/external_sources.py` — lines 53, 60, 62, 68, 75
- `essay_wb/sources/transcribe_sources.py` — line 134
- `essay_wb/run/meta_aggregate_llm.py` — lines 75, 173, 175
- `essay_wb/run/suspicion_reports.py` — line 253
- `essay_wb/stages/outline_to_essay/core.py` — lines 124, 127
- `essay_wb/stage_llm.py` — line 52
- `essay_wb/stage_cli.py` — line 65
- `essay_wb/run/failure_triage.py` — line 166
- `essay_wb/run/preflight.py` — line 174
- `essay_wb/sources/source_catalog.py` — lines 949, 952, 955

### Skip (per backlog — inherently `Any`)

- `essay_wb/llm/llm_logging.py`
- `essay_wb/llm/reasoning_summary_probe.py`
- `essay_wb/utils/json_fmt.py`
- `essay_wb/utils/json_extract.py`

### Also skip (infrastructure type mechanics, not `isinstance+cast` ceremony)

- `stage_llm.py` generic `_T` casts (lines 79, 80, 90, 92, 94, 96, 150, 232, 245, 288, 295)
- Literal type narrowing casts in `failure_triage.py`, `meta_aggregate_llm.py`, `pipeline_spec.py`, `catalog_tools.py`

---

## Tier 3: Pydantic for Own-Data Parsing

### `essay_wb/run/pipeline_spec.py`

Add a `PipelineSpecJson` model for the `pipeline_spec.json` file schema:

```python
class PipelineSpecJson(BaseModel):
    pipeline_id: str
    spec_version: int
    required_artifacts: list[str] = []
    deterministic_transforms: list[str] = []
```

Replace the manual `json.loads` + isinstance + cast dance in `load_pipeline_spec()` with:
```python
parsed = PipelineSpecJson.model_validate_json(raw)
```

This removes cast sites at lines 60, 81, 86.

### `essay_wb/run/removal_queue.py`

Add a `RemovalEntry` model:

```python
class RemovalEntry(BaseModel):
    run_id: str
    reason: str
    added_by: str
    added_at: str
    commit_sha: str | None = None
```

Replace the manual list parsing with `TypeAdapter(list[RemovalEntry]).validate_json(raw)`. Removes the cast at line 62.

---

## Implementation Order

1. **Tier 2 first** — `checked_dict`/`checked_list` utility (small, isolated, no behavioral change)
2. **Tier 3** — Pydantic for pipeline_spec + removal_queue (small, isolated)
3. **Tier 1** — Structured output models (largest change, most impactful)
   - 1a. Create model files
   - 1b. Update `_placeholder_for_output_type` for BaseModel preflight
   - 1c. Migrate eval_style_humanization judge (simplest — single call, no retry loop)
   - 1d. Migrate create_and_cluster_outlines options, grade, cluster calls
   - 1e. Update cluster_report.py to accept typed ClusterOutput
   - 1f. Clean up removed code (unused parse functions, imports)

## Verification

1. `uv run basedpyright` — type check must pass
2. `uv run python -m pytest essay_wb/tests/` — existing unit tests
3. `uv run python scripts/run_infra_tests.py --help` — verify script still works
4. `uv run python scripts/test_all_pipelines.py --help` — verify pipeline scripts parse
5. For any pipeline with preflight support: run preflight to verify `_placeholder_for_output_type` works with BaseModel subclasses

## Files Modified (Summary)

| File | Change |
|------|--------|
| `essay_wb/utils/checked_types.py` | **NEW** — `checked_dict`, `checked_list` |
| `essay_wb/stages/create_and_cluster_outlines/models.py` | **NEW** — `OptionsOutput`, `OutlineGrade`, `ClusterOutput` |
| `essay_wb/stages/eval_style_humanization/models.py` | **NEW** — `JudgeOutput`, `AiTell` |
| `essay_wb/stage_llm.py` | Update `_placeholder_for_output_type` for BaseModel; Tier 2 checked_dict |
| `essay_wb/stages/create_and_cluster_outlines/pipeline.py` | Migrate 3 call sites to structured output |
| `essay_wb/stages/create_and_cluster_outlines/core.py` | Simplify `parse_options`, `parse_grade_result` |
| `essay_wb/stages/eval_style_humanization/pipeline.py` | Migrate judge call; remove `_parse_judge_json`, simplify `_score_from_judge_output` |
| `essay_wb/outlines/cluster_report.py` | Accept `ClusterOutput` model |
| `essay_wb/run/pipeline_spec.py` | Pydantic model for spec JSON |
| `essay_wb/run/removal_queue.py` | Pydantic model for removal entry |
| ~10 more files | Tier 2 `checked_dict`/`checked_list` replacements |
