# Planner Executor: Test Verification Reporting Analysis

**Date**: 2026-02-17
**Subject**: Preventing Incorrect Verification Status Reporting in Planner Executor
**Status**: Analysis Complete, Recommendations Ready for Implementation
**Confidence**: HIGH

---

## Executive Summary

### The Problem

The planner executor incorrectly reported acceptance criteria as "✅ verified" when functional tests could not be executed due to environmental constraints (missing dependencies). This creates false confidence in implementation completeness.

**Specific incident**: Execution of PLAN.md for PR #137 bug fix:
- Test code was written and code-reviewed (structure validated)
- Functional tests could NOT run (missing `tree-sitter-langs` dependency)
- Retrospective reported milestone as "✅ COMPLETE" without distinguishing code review from functional testing

### Root Cause

Code examination of `/root/.claude/skills/scripts/skills/planner/orchestrator/executor.py` revealed three coupled failures:

1. **No test enforcement** (line 369): Test execution is **guidance text** shown to LLM, not enforced by code
2. **No verification tracking**: No mechanism records what verification was actually performed
3. **Retrospective data gap** (lines 173-187): Step 9 template has no data source for verification status

**Result**: LLM orchestrator can report "COMPLETE" without verifying tests ran, because no code prevents it and retrospective has no data to contradict.

### Recommended Solution

**Three modifications** to `executor.py` (in priority order):

1. **Enhanced verification tracking** (lines 369-374): Require step 3 to record verification status to `verification-status.md`
2. **Honest retrospective reporting** (lines 173-187): Step 9 reads and reports actual verification status
3. **Optional enforcement gate** (step 5): Block progression if verification not recorded (defer until 1-2 tested)

**Expected outcome**: Honest reporting that distinguishes "code reviewed" from "functionally tested" from "skipped", preventing false confidence.

**Key limitation**: Planner uses LLM orchestration, so enhanced guidance improves but doesn't guarantee compliance. True automation would require architectural changes (pytest/jest integration).

---

## Problem Statement

### Context

The planner executor orchestrates complex software development tasks through a 9-step workflow:
1. Execution Planning
2. Reconciliation (optional)
3. **Implementation** ← Tests should run here
4. Code QR (quality review)
5. Code QR Gate
6. Documentation
7. Doc QR
8. Doc QR Gate
9. **Retrospective** ← Reports verification status

Each step provides **guidance** to the LLM orchestrator, which delegates to specialized agents (developers, QR reviewers, technical writers).

### The Incident

**Plan**: Add reproduction test for PR #137 (evil-textobj-tree-sitter)
**Acceptance Criteria**:
- ✅ ERT test passes on fixed branch
- ✅ ERT test fails when fix reverted
- ✅ reply.md explains bug

**What happened**:
1. Developer agent wrote test code (structure valid)
2. Code QR verified test structure and documentation
3. Test execution attempted: `emacs --batch -l test.el ...`
4. **Execution failed**: `Cannot open load file: tree-sitter-langs`
5. Retrospective reported: "✅ ERT test passes" (INCORRECT)

**Actual status**: CODE-COMPLETE, FUNCTIONALLY UNVERIFIED

**Why this matters**:
- User believes tests were verified when they weren't
- PR maintainer may merge without functional validation
- Future regressions may not be caught
- Erodes trust in planner verification claims

---

## Root Cause Analysis

### Code Examination

**File examined**: `/root/.claude/skills/scripts/skills/planner/orchestrator/executor.py`
**Key findings**:

#### Finding 1: Test Execution is Guidance, Not Code (Lines 369-372)

**Location**: Step 3 (Implementation) template

```python
# executor.py lines 356-372 (step 3 normal mode)
"FOR EACH WAVE:",
"  1. Dispatch developer agents for ALL milestones in wave:",
"     Task(developer): Milestone N",
"     Task(developer): Milestone M  (if parallel)",
"",
"  2. Each prompt must include:",
"     - Plan file: $PLAN_FILE",
"     - Milestone: [number and name]",
"     - Files: [exact paths to create/modify]",
"     - Acceptance criteria: [from plan]",
"",
"  3. Wait for ALL agents in wave to complete",
"",
"  4. Run tests: pytest / tsc / go test -race",     # ← GUIDANCE TEXT
"     Pass criteria: 100% tests pass, zero warnings",  # ← NOT ENFORCED
"",
"  5. Proceed to next wave (repeat 1-4)",
```

**Analysis**: This is **instruction text displayed to LLM**, not executable Python code. The orchestrator SUGGESTS running tests but doesn't enforce it or track the result.

**Evidence**: When test execution failed with dependency error, workflow proceeded to step 4 (Code QR) without recording the failure.

#### Finding 2: No Verification State Tracking

**Observation**: Nowhere in executor.py does code:
- Record test execution results
- Distinguish "code reviewed" from "functionally tested"
- Store verification status for later steps

**STATE_DIR reference** (line 130): Executor mentions `STATE_DIR (if available)` for QA integration, but:
- STATE_DIR is optional context, not guaranteed infrastructure
- No code writes verification results to STATE_DIR
- No standard format for verification tracking exists

**Implication**: Even if LLM attempts tests, results are lost. Retrospective has no data source.

#### Finding 3: Retrospective Has No Data Source (Lines 173-187)

**Location**: Step 9 (Retrospective) template

```python
# executor.py lines 171-187 (step 9)
9: {
    "title": "Retrospective",
    "actions": [
        "PRESENT retrospective to user (do not write to file):",
        "",
        "EXECUTION RETROSPECTIVE",
        "=======================",
        "Plan: [path]",
        "Status: COMPLETED | BLOCKED | ABORTED",
        "",
        "Milestone Outcomes: | Milestone | Status | Notes |",
        "Reconciliation Summary: [if run]",
        "Plan Accuracy Issues: [if any]",
        "Deviations from Plan: [if any]",
        "Quality Review Summary: [counts by category]",
        "Feedback for Future Plans: [actionable suggestions]",
    ],
},
```

**Analysis**: Template is **static text** with placeholders. No instructions to:
- Read verification status from previous steps
- Distinguish verification methods (code review vs testing)
- Report skipped verifications with reasons

**Result**: LLM fills placeholders based on memory/assumption, not data. Can report "COMPLETED" without evidence.

### The Failure Chain

1. **Step 3**: Developer completes code → LLM sees "Run tests" guidance → attempts test execution → fails with dependency error → **NO RECORD CREATED**

2. **Step 4**: Code QR reviews structure, documentation, patterns → returns PASS → **"PASS" conflated with full verification**

3. **Step 9**: Retrospective asks for "Status" → LLM recalls code was written and QR passed → reports "✅ COMPLETED" → **No data contradicts this claim**

**Root cause summary**: Guidance-based workflow without state tracking or enforcement allows verification steps to be skipped or forgotten without penalty.

---

## Recommended Solutions

### Design Principles

Based on first principles and CI/CD analogies:

1. **Fail-Safe Principle**: Unknown verification status should default to "unverified", not "passed"
2. **Transparency Over Perfection**: Honest reporting of "SKIPPED" beats false "VERIFIED"
3. **Separation of Concerns**: Code review verifies structure; functional testing verifies behavior (different confidence levels)
4. **Explicit Over Implicit**: Status should be recorded explicitly, not inferred from memory

### Option A: Enhanced Verification Tracking (Priority 1)

**File**: `executor.py`
**Lines**: 369-374 (within STEPS[3] normal mode template)
**Impact**: Minimal (guidance text only)
**Effectiveness**: Moderate (improves expectations, relies on LLM compliance)

#### Modification

**Current**:
```python
"  4. Run tests: pytest / tsc / go test -race",
"     Pass criteria: 100% tests pass, zero warnings",
"",
"  5. Proceed to next wave (repeat 1-4)",
```

**Proposed**:
```python
"  4. REQUIRED: Track verification status:",
"     ",
"     a. Determine verification requirements:",
"        - Read acceptance criteria from PLAN.md",
"        - Identify which require functional testing vs code review",
"     ",
"     b. Attempt verification per criterion type:",
"        - TEST_EXECUTION: Run pytest / emacs --batch / npm test / go test",
"        - CODE_REVIEW: Performed by QR step (step 4)",
"        - DOCUMENTATION: File existence and content check",
"     ",
"     c. Record outcomes:",
"        - PASSED: Verification succeeded",
"        - FAILED: Verification ran but found issues",
"        - SKIPPED: Could not perform (state reason clearly)",
"          Examples: 'missing tree-sitter-langs'",
"                   'emacs not available in environment'",
"                   'timeout exceeded (300s)'",
"        - NOT_ATTEMPTED: Verification not performed (state why)",
"     ",
"     d. Write verification-status.md to plan directory:",
"        ",
"        FORMAT:",
"        ```markdown",
"        # Verification Status Report",
"        ",
"        ## Milestone M-001: [Milestone Name]",
"        ",
"        ### Acceptance Criteria Verification",
"        ",
"        1. **ERT test passes on fixed branch**",
"           - Method: TEST_EXECUTION",
"           - Command: `emacs --batch -l test.el -f ert-run-tests-batch`",
"           - Status: SKIPPED",
"           - Reason: Missing dependency 'tree-sitter-langs'",
"           - Timestamp: 2026-02-17T10:30:00Z",
"        ",
"        2. **reply.md explains bug**",
"           - Method: CODE_REVIEW",
"           - Status: VERIFIED",
"           - Reviewer: QR agent (step 4)",
"        ",
"        ### Summary",
"        - Code Quality: REVIEWED (QR PASS)",
"        - Functional Tests: SKIPPED (1/2 criteria)",
"        - Documentation: VERIFIED",
"        - **Overall**: PARTIAL",
"        ```",
"     ",
"     e. CRITICAL: Do NOT mark milestone complete without writing status file",
"     f. If tests FAIL: dispatch debugger or AskUserQuestion before proceeding",
"     ",
"  5. Verify verification-status.md was created before proceeding to next wave",
"     ",
"  6. Proceed to next wave (repeat 1-5)",
```

#### Rationale

- **Makes expectations explicit**: "REQUIRED" signals mandatory step
- **Provides template**: Shows exact format for status file
- **Defines status categories**: Clear taxonomy prevents ambiguity
- **Creates audit trail**: verification-status.md persists between steps
- **Enables retrospective reporting**: Step 9 can read this file

#### Limitations

- **Relies on LLM compliance**: LLM could still skip despite "REQUIRED"
- **No code enforcement**: Nothing prevents proceeding without status file
- **Parsing complexity**: Acceptance criteria are natural language, may be ambiguous

### Option C: Honest Retrospective Reporting (Priority 2)

**File**: `executor.py`
**Lines**: 173-187 (STEPS[9] template)
**Impact**: Minimal (guidance text only)
**Effectiveness**: High for transparency (reports truth even if tracking failed)

#### Modification

**Current**:
```python
9: {
    "title": "Retrospective",
    "actions": [
        "PRESENT retrospective to user (do not write to file):",
        "",
        "EXECUTION RETROSPECTIVE",
        "=======================",
        "Plan: [path]",
        "Status: COMPLETED | BLOCKED | ABORTED",
        "",
        "Milestone Outcomes: | Milestone | Status | Notes |",
        ...
    ],
},
```

**Proposed**:
```python
9: {
    "title": "Retrospective",
    "actions": [
        "CRITICAL: Read verification data before reporting",
        "",
        "1. Check plan directory for verification-status.md",
        "2. If found:",
        "   - Parse verification data",
        "   - Extract status for each criterion",
        "   - Determine overall milestone status:",
        "     * COMPLETE: All criteria VERIFIED or PASSED",
        "     * PARTIAL: Some SKIPPED or NOT_ATTEMPTED",
        "     * BLOCKED: Any FAILED",
        "3. If NOT found:",
        "   - Status = UNKNOWN",
        "   - Include warning in retrospective",
        "",
        "PRESENT retrospective to user (do not write to file):",
        "",
        "EXECUTION RETROSPECTIVE",
        "=======================",
        "Plan: [path]",
        "Status: COMPLETED | PARTIAL | BLOCKED | UNKNOWN",
        "",
        "### Verification Summary",
        "",
        "| Criterion | Method | Status | Details |",
        "|-----------|--------|--------|---------|",
        "| [criterion text] | [TEST_EXECUTION/CODE_REVIEW/etc] | [VERIFIED/SKIPPED/etc] | [reason if skipped] |",
        "",
        "Example:",
        "| ERT test passes | TEST_EXECUTION | SKIPPED | missing tree-sitter-langs |",
        "| reply.md exists | CODE_REVIEW | VERIFIED | QR approved |",
        "",
        "### Milestone Outcomes",
        "",
        "| Milestone | Code QR | Functional Tests | Documentation | Overall | Notes |",
        "|-----------|---------|------------------|---------------|---------|-------|",
        "| M-001     | PASS    | SKIPPED          | VERIFIED      | PARTIAL | See verification details |",
        "",
        "(If verification-status.md NOT found:)",
        "",
        "⚠️  **WARNING**: Verification status was not tracked during execution.",
        "    Cannot confirm functional testing was performed.",
        "    Code quality review (QR) was completed in step 4.",
        "    ",
        "    **Recommendation**: Manually verify acceptance criteria before",
        "    considering this implementation complete.",
        "",
        "Reconciliation Summary: [if run]",
        "Plan Accuracy Issues: [if any]",
        "Deviations from Plan: [if any]",
        "Quality Review Summary: [counts by category]",
        "",
        "### Recommended Next Steps (if PARTIAL or SKIPPED items exist)",
        "",
        "For each SKIPPED criterion, list remediation:",
        "- Install missing dependencies",
        "- Run specific test commands",
        "- Verification procedures",
        "",
        "Feedback for Future Plans: [actionable suggestions]",
    ],
},
```

#### Rationale

- **Enforces data-driven reporting**: Must read verification file, not rely on memory
- **Clear status taxonomy**: COMPLETE/PARTIAL/BLOCKED/UNKNOWN (no ambiguity)
- **Graceful degradation**: If verification-status.md missing, shows WARNING
- **Actionable guidance**: Tells user what to do for SKIPPED items
- **Distinguishes verification types**: Separate columns for Code QR vs Functional Tests

#### Benefits

- **Prevents false confidence**: "PARTIAL" status visible at top of retrospective
- **Transparency**: User sees exactly what was/wasn't verified and why
- **Actionable**: Provides next steps for completing verification
- **Audit trail**: Verification summary preserved in conversation

### Option B: Enforcement Gate (Priority 3 - Optional)

**File**: `executor.py`
**Location**: Step 5 (Code QR Gate) or new verification gate before step 4
**Impact**: Moderate (requires code logic, not just guidance)
**Effectiveness**: High (actually enforces verification recording)

#### Concept

Add code check that **blocks progression** if verification-status.md doesn't exist.

**Pseudo-code**:
```python
# At step 5 gate (or new step 3.5)
def check_verification_gate(plan_dir: Path) -> GateResult:
    """Enforce that verification status was recorded."""
    status_file = plan_dir / "verification-status.md"

    if not status_file.exists():
        return GateResult.BLOCKED(
            message="Verification status not recorded. Cannot proceed to QR.",
            remediation="Complete step 3 verification tracking before QR."
        )

    # Optional: Parse and check for NOT_ATTEMPTED without reason
    content = status_file.read_text()
    if "NOT_ATTEMPTED" in content and "Reason:" not in content:
        return GateResult.BLOCKED(
            message="Verification shows NOT_ATTEMPTED without explanation.",
            remediation="Provide reason for skipped verification."
        )

    return GateResult.PASS
```

#### Defer This Option

**Why defer**:
- Requires understanding gate implementation details (not fully documented)
- More invasive change than Options A+C
- May break existing plans without test requirements
- Needs edge case handling (what if plan has no testable criteria?)

**When to implement**:
- After testing Options A+C in practice
- If LLM proves unreliable at following enhanced guidance
- If misreporting continues despite clear instructions

---

## Implementation Guidance

### Phase 1: Enhanced Guidance (Weeks 1-2)

**Objectives**:
- Improve verification tracking through enhanced guidance
- Make retrospective reporting honest and data-driven
- Minimal disruption to existing workflow

**Steps**:

1. **Backup current executor.py**:
   ```bash
   cp executor.py executor.py.backup
   ```

2. **Apply Option A**: Modify lines 369-374 per specification above

3. **Apply Option C**: Modify lines 173-187 per specification above

4. **Test with sample plan**:
   - Create test plan with mix of testable and non-testable criteria
   - Run planner executor
   - Verify verification-status.md is created
   - Verify retrospective shows accurate status

5. **Test edge cases**:
   - Plan with no test requirements → verification-status.md should note "No functional tests required"
   - Plan where tests fail → status FAILED, retrospective shows BLOCKED
   - Plan where tests skipped → status SKIPPED with reason, retrospective shows PARTIAL

6. **Monitor LLM compliance**:
   - Track how often LLM creates verification-status.md
   - Track how often retrospective reads it correctly
   - If compliance <80%, proceed to Phase 2

### Phase 2: Enforcement (If Needed)

**Trigger**: LLM compliance with Phase 1 guidance <80% in practice

**Steps**:

1. **Design enforcement gate**:
   - Decide location: step 5 (existing gate) or new step 3.5
   - Define gate logic: block if verification-status.md missing
   - Handle edge cases: plans without tests, manual verification override

2. **Implement gate check**:
   - Add verification file existence check
   - Provide clear error message with remediation steps
   - Allow manual override with explicit user confirmation

3. **Test enforcement**:
   - Verify gate blocks when status file missing
   - Verify gate passes when status file exists and valid
   - Verify error messages are actionable

4. **Gradual rollout**:
   - Enable for new plans first
   - Monitor for false blocks (plans where blocking is inappropriate)
   - Refine gate logic based on feedback

### Testing Strategy

**Unit Testing** (if implementing Option B enforcement):
```python
def test_verification_gate_blocks_missing_status():
    plan_dir = Path("/tmp/test-plan")
    plan_dir.mkdir()
    # Don't create verification-status.md

    result = check_verification_gate(plan_dir)
    assert result.status == GateStatus.BLOCKED
    assert "not recorded" in result.message

def test_verification_gate_passes_with_status():
    plan_dir = Path("/tmp/test-plan")
    plan_dir.mkdir()
    (plan_dir / "verification-status.md").write_text("## M-001\nStatus: VERIFIED")

    result = check_verification_gate(plan_dir)
    assert result.status == GateStatus.PASS
```

**Integration Testing**:
```bash
# Test plan with failing tests
cd ~/.claude/skills/scripts
python3 -m skills.planner.orchestrator.executor \
    --plan test-plans/failing-tests-plan.md

# Expected: verification-status.md shows FAILED
# Expected: Retrospective shows BLOCKED

# Test plan with missing dependencies
python3 -m skills.planner.orchestrator.executor \
    --plan test-plans/missing-deps-plan.md

# Expected: verification-status.md shows SKIPPED with reason
# Expected: Retrospective shows PARTIAL
```

### Rollback Plan

If modifications cause issues:

1. **Immediate rollback**:
   ```bash
   mv executor.py.backup executor.py
   ```

2. **Partial rollback**:
   - Keep Option C (retrospective transparency)
   - Revert Option A (verification tracking) if causing failures

3. **Gradual revert**:
   - Soften "REQUIRED" language to "RECOMMENDED"
   - Make verification-status.md optional in retrospective
   - Keep status taxonomy for manual use

---

## Limitations and Trade-offs

### Fundamental Architectural Constraint

**The planner uses LLM orchestration, not code automation.**

This means:
- Steps are **guidance templates** shown to LLM, not executable scripts
- LLM interprets and executes instructions using available tools
- Enhanced guidance improves clarity but doesn't **guarantee** compliance

**Implication**: Even with Option A+C, LLM could theoretically:
- Forget to create verification-status.md
- Create it with incomplete data
- Skip reading it in retrospective

**Mitigation**: Option B (enforcement gate) adds code-level checking, but even this can't force tests to RUN, only force status to be RECORDED.

### What These Solutions DO vs DON'T DO

**✅ DO**:
- Make verification expectations explicit and mandatory-sounding
- Create persistent audit trail (verification-status.md file)
- Distinguish "code reviewed" from "functionally tested"
- Report honestly in retrospective (show SKIPPED/PARTIAL, not false VERIFIED)
- Warn users when verification tracking failed
- Provide remediation guidance (what to do about SKIPPED items)

**❌ DON'T**:
- Force tests to run (environmental constraints may prevent execution)
- Guarantee LLM follows enhanced guidance (it's instructions, not code control)
- Handle all edge cases (novel plan structures may confuse parser)
- Solve upstream problems (missing dependencies, broken test frameworks)

### True Test Automation Would Require

**Major architectural changes**:

1. **Test framework integration**:
   - Pytest runner subprocess management
   - Jest/Mocha/Tap node test execution
   - Emacs batch mode test orchestration
   - Language-specific test discovery

2. **Dependency management**:
   - Virtual environment setup (Python venv, npm install, etc.)
   - Dependency resolution before test execution
   - Graceful handling of missing system dependencies

3. **Result parsing**:
   - Parse test framework output (JUnit XML, TAP, custom formats)
   - Extract pass/fail/skip counts
   - Capture stack traces and error messages

4. **Timeout and resource management**:
   - Test execution timeouts
   - Memory limits
   - Parallel test execution

**Scope**: This is a major feature addition (weeks/months of development), not a bug fix.

**Current approach**: Honest reporting of SKIPPED tests is better than false reporting of VERIFIED tests. Users can manually verify as needed.

### Accepted Trade-offs

| Trade-off | Decision | Rationale |
|-----------|----------|-----------|
| **Guidance vs Enforcement** | Start with guidance (Option A+C), add enforcement (Option B) only if needed | CI/CD best practice: visibility before blocking. Less disruptive. |
| **Automation vs Transparency** | Prioritize transparent reporting over automated testing | Planner's LLM architecture makes automation difficult; transparency is achievable and valuable. |
| **Strictness vs Flexibility** | Allow SKIPPED status (don't force tests to pass) | Environmental constraints are real; honest SKIPPED better than blocked workflow. |
| **Simplicity vs Completeness** | Simple file format (Markdown) over structured data (JSON/YAML) | LLM can parse Markdown easily; human-readable; lower implementation cost. |

---

## Appendices

### Appendix A: verification-status.md Format Specification

**File Location**: `{plan_directory}/verification-status.md`
**Format**: Markdown with specific structure
**Created By**: Step 3 (Implementation) after each milestone
**Read By**: Step 9 (Retrospective) for final reporting

**Template**:

```markdown
# Verification Status Report

Generated: {ISO-8601 timestamp}
Plan: {path to PLAN.md}

---

## Milestone M-001: {Milestone Name}

### Acceptance Criteria Verification

#### 1. {Criterion description from PLAN.md}

- **Method**: TEST_EXECUTION | CODE_REVIEW | FILE_CHECK | MANUAL
- **Command** (if TEST_EXECUTION): `{actual command run}`
- **Status**: PASSED | FAILED | SKIPPED | NOT_ATTEMPTED
- **Reason** (if SKIPPED/NOT_ATTEMPTED): {clear explanation}
- **Output** (if FAILED):
  ```
  {relevant error output, first 50 lines}
  ```
- **Timestamp**: {ISO-8601 when verification attempted}

#### 2. {Next criterion}

...

### Summary

- **Code Quality**: REVIEWED | NOT_REVIEWED
  - QR Step: PASS | ISSUES
  - Iteration count: {number}

- **Functional Tests**: VERIFIED | PARTIAL | SKIPPED | NOT_ATTEMPTED
  - Passed: {count}
  - Failed: {count}
  - Skipped: {count}

- **Documentation**: VERIFIED | SKIPPED | NOT_ATTEMPTED

- **Overall Status**: COMPLETE | PARTIAL | BLOCKED
  - COMPLETE: All criteria verified
  - PARTIAL: Some criteria skipped but code quality OK
  - BLOCKED: Critical criteria failed

### Recommendations

(If PARTIAL or BLOCKED):

For SKIPPED items:
- Install missing dependencies: {list}
- Run commands: {list}

For FAILED items:
- Review error output above
- {specific remediation steps if known}
```

**Parsing Rules** for Step 9:

1. Check file existence in plan directory
2. If missing: status = UNKNOWN, show WARNING
3. If exists:
   - Extract "Overall Status" line
   - Extract criterion statuses for table
   - Extract recommendations for next steps

### Appendix B: Status Taxonomy Reference

**Verification Status Values** (for individual criteria):

| Status | Meaning | When to Use | Reporting Color |
|--------|---------|-------------|-----------------|
| **PASSED** | Verification performed and succeeded | Tests ran, all passed | ✅ Green |
| **FAILED** | Verification performed but found issues | Tests ran, some failed | ❌ Red |
| **SKIPPED** | Verification not performed due to constraint | Missing deps, timeout, env issue | ⏭️ Yellow |
| **NOT_ATTEMPTED** | Verification was not tried | No test found, unclear requirement | ⚠️ Orange |
| **VERIFIED** | Manual or code review verification succeeded | QR approved, file exists | ✅ Green |

**Milestone Status Values** (for overall milestone):

| Status | Meaning | Criteria |
|--------|---------|----------|
| **COMPLETE** | All acceptance criteria met | All: PASSED or VERIFIED |
| **PARTIAL** | Some criteria not verified but work complete | Some: SKIPPED or NOT_ATTEMPTED; None: FAILED |
| **BLOCKED** | Critical criteria failed | Any: FAILED |
| **UNKNOWN** | Verification status not tracked | verification-status.md missing |

**Verification Method Values**:

| Method | Description | Example |
|--------|-------------|---------|
| **TEST_EXECUTION** | Automated test framework run | pytest, jest, emacs batch |
| **CODE_REVIEW** | QR agent structural review | Step 4 QR verification |
| **FILE_CHECK** | File existence and content | Documentation files |
| **MANUAL** | Human verification required | UX review, deployment check |

### Appendix C: Example Scenarios

#### Scenario 1: All Tests Pass

**verification-status.md**:
```markdown
## Milestone M-001: Add user authentication

1. **Unit tests pass**
   - Method: TEST_EXECUTION
   - Command: `pytest tests/auth/test_login.py -v`
   - Status: PASSED
   - Timestamp: 2026-02-17T10:30:00Z

2. **Integration tests pass**
   - Method: TEST_EXECUTION
   - Command: `pytest tests/integration/test_auth_flow.py -v`
   - Status: PASSED
   - Timestamp: 2026-02-17T10:31:15Z

Overall Status: COMPLETE
```

**Retrospective Output**:
```
Status: COMPLETED

Verification Summary:
| Criterion | Method | Status | Details |
|-----------|--------|--------|---------|
| Unit tests pass | TEST_EXECUTION | PASSED | pytest 24/24 passed |
| Integration tests pass | TEST_EXECUTION | PASSED | pytest 8/8 passed |

Milestone Outcomes:
| Milestone | Code QR | Tests | Overall |
|-----------|---------|-------|---------|
| M-001 | PASS | PASSED | COMPLETE |
```

#### Scenario 2: Tests Skipped (Missing Dependency)

**verification-status.md**:
```markdown
## Milestone M-001: Add data export feature

1. **Export functionality works**
   - Method: TEST_EXECUTION
   - Command: `pytest tests/test_export.py`
   - Status: SKIPPED
   - Reason: Missing dependency 'pandas>=2.0.0'. Install with: pip install pandas
   - Timestamp: 2026-02-17T10:30:00Z

2. **Documentation updated**
   - Method: CODE_REVIEW
   - Status: VERIFIED
   - Timestamp: 2026-02-17T10:28:00Z

Overall Status: PARTIAL
```

**Retrospective Output**:
```
Status: PARTIAL (functional verification incomplete)

Verification Summary:
| Criterion | Method | Status | Details |
|-----------|--------|--------|---------|
| Export works | TEST_EXECUTION | SKIPPED | missing pandas>=2.0.0 |
| Docs updated | CODE_REVIEW | VERIFIED | QR approved |

Milestone Outcomes:
| Milestone | Code QR | Tests | Overall |
|-----------|---------|-------|---------|
| M-001 | PASS | SKIPPED | PARTIAL |

Recommended Next Steps:
- Install pandas: pip install 'pandas>=2.0.0'
- Run tests: pytest tests/test_export.py
- Verify export functionality manually if tests still fail
```

#### Scenario 3: Tests Failed

**verification-status.md**:
```markdown
## Milestone M-001: Fix authentication bug

1. **Login tests pass**
   - Method: TEST_EXECUTION
   - Command: `npm test -- auth.test.js`
   - Status: FAILED
   - Output:
     ```
     FAIL tests/auth.test.js
       ✓ should hash passwords (12ms)
       ✕ should validate tokens (45ms)
         Expected token to be valid
         Received: invalid signature
     ```
   - Timestamp: 2026-02-17T10:30:00Z

Overall Status: BLOCKED
```

**Retrospective Output**:
```
Status: BLOCKED (tests failing)

Verification Summary:
| Criterion | Method | Status | Details |
|-----------|--------|--------|---------|
| Login tests pass | TEST_EXECUTION | FAILED | token validation failing |

Milestone Outcomes:
| Milestone | Code QR | Tests | Overall |
|-----------|---------|-------|---------|
| M-001 | PASS | FAILED | BLOCKED |

⚠️  CRITICAL: Tests are failing. Review error output in verification-status.md
and fix issues before considering this milestone complete.
```

#### Scenario 4: Verification Not Tracked (Current Problem)

**verification-status.md**: *(file does not exist)*

**Retrospective Output**:
```
Status: UNKNOWN (verification not tracked)

⚠️  WARNING: Verification status was not tracked during execution.
    Cannot confirm functional testing was performed.
    Code quality review (QR) was completed in step 4.

    Recommendation: Manually verify acceptance criteria before
    considering this implementation complete.

Milestone Outcomes:
| Milestone | Code QR | Tests | Overall |
|-----------|---------|-------|---------|
| M-001 | PASS | UNKNOWN | UNKNOWN |
```

---

## Conclusion

### Summary of Recommendations

1. **Immediate**: Implement Option A (enhanced step 3 guidance) and Option C (honest retrospective reporting)
2. **Monitor**: Track LLM compliance with verification tracking over 2-4 weeks
3. **Optional**: Add Option B (enforcement gate) if compliance proves insufficient

### Expected Outcomes

**Short term** (Weeks 1-4):
- Verification status explicitly tracked in verification-status.md
- Retrospectives honestly report PARTIAL when tests skipped
- Users aware of verification gaps, can act accordingly
- False confidence eliminated

**Medium term** (Months 2-3):
- LLM learns pattern, consistently creates verification-status.md
- Quality of verification tracking improves (more detail, clearer reasons)
- Fewer edge cases require manual intervention

**Long term** (Months 4-6):
- Consider Option B enforcement if compliance still <80%
- Gather data on common skip reasons, improve dependency handling
- Potentially evolve toward test automation (if architecture allows)

### Success Metrics

- **Primary**: Zero instances of "✅ VERIFIED" when tests didn't run
- **Secondary**: verification-status.md created in >90% of executions
- **Tertiary**: User satisfaction with transparency of reporting

### Next Steps for Maintainers

1. Review this analysis and approve approach
2. Create feature branch for modifications
3. Implement Option A (lines 369-374) and Option C (lines 173-187)
4. Test with 3-5 sample plans covering edge cases
5. Deploy to test environment, monitor for 2 weeks
6. Review compliance metrics, decide on Option B
7. Document changes in planner CLAUDE.md

### Next Steps for Users (This Execution)

Since this execution's tests were not verified:

```bash
# Manual verification required
cd /root/.emacs.d/elpaca_new/repos/evil-textobj-tree-sitter

# 1. Install dependency (if using Emacs with tree-sitter)
# Follow emacs-tree-sitter installation guide

# 2. Run the test
emacs --batch -l evil-textobj-tree-sitter-test.el -f ert-run-tests-batch-and-exit

# 3. Verify test catches the bug:
# a. Temporarily revert the fix
#    Edit evil-textobj-tree-sitter-core.el line 163
#    Change: (abs (- byte-pos (car (last y))))
#    To:     (abs (- byte-pos (car (last x))))  [bug]
#
# b. Re-run test (should FAIL)
#    emacs --batch -l evil-textobj-tree-sitter-test.el -f ert-run-tests-batch-and-exit
#
# c. Restore the fix
#    Change back: (abs (- byte-pos (car (last y))))

# 4. If all tests pass, implementation is COMPLETE
```

---

**Document Status**: FINAL
**Confidence**: HIGH
**Recommendations**: READY FOR IMPLEMENTATION

