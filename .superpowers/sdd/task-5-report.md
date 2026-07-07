# Task 5 Report: Guardrail — Governance Core

## Status
✅ Complete

## Commits
- `5b09886` — feat(guardrail): layer 1 command detection
- `76500cd` — feat(guardrail): layer 3 scope fence
- `023c306` — feat(guardrail): layer 2 HITL state machine

## Files Created
- `src/harness/guardrail.py` (53 lines)
- `tests/test_guardrail.py` (16 tests)

## TDD Process
Three independent red-green-commit cycles, one per layer (order follows the brief: Layer 1 → Layer 3 → Layer 2).

### Layer 1: Command Detection
1. **Red**: Wrote 7 tests in `tests/test_guardrail.py`. Ran `pytest` → failed with `ModuleNotFoundError: No module named 'harness.guardrail'` (expected).
2. **Green**: Wrote `guardrail(action, config)` minimal implementation. Ran `pytest` → 7/7 passed.
3. **Commit**: `5b09886`.

### Layer 3: Scope Fence
1. **Red**: Appended 4 tests + `check_scope` import. Ran `pytest tests/test_guardrail.py::test_scope_fence_blocks_outside_directory` → failed with `ImportError: cannot import name 'check_scope'` (expected).
2. **Green**: Appended `check_scope(action, config)` implementation. Ran `pytest` → 11/11 passed.
3. **Commit**: `76500cd`.

### Layer 2: HITL State Machine
1. **Red**: Appended 5 tests + `HitlState` import. Ran `pytest tests/test_guardrail.py::test_hitl_state_starts_pending` → failed with `ImportError: cannot import name 'HitlState'` (expected).
2. **Green**: Appended `HitlState` class. Ran `pytest` → 16/16 passed.
3. **Commit**: `023c306`.

## Test Summary
```
tests/test_guardrail.py::test_blocked_command_rm_rf_root PASSED          [  6%]
tests/test_guardrail.py::test_blocked_command_dd PASSED                  [ 12%]
tests/test_guardrail.py::test_hitl_command_rm_file PASSED                [ 18%]
tests/test_guardrail.py::test_hitl_command_sudo PASSED                   [ 25%]
tests/test_guardrail.py::test_pass_command_ls PASSED                     [ 31%]
tests/test_guardrail.py::test_pass_command_pytest PASSED                 [ 37%]
tests/test_guardrail.py::test_non_bash_action_passes_layer1 PASSED       [ 43%]
tests/test_guardrail.py::test_scope_fence_blocks_outside_directory PASSED [ 50%]
tests/test_guardrail.py::test_scope_fence_allows_inside_directory PASSED [ 56%]
tests/test_guardrail.py::test_scope_fence_write_blocked_outside PASSED   [ 62%]
tests/test_guardrail.py::test_scope_fence_bash_not_checked PASSED        [ 68%]
tests/test_guardrail.py::test_hitl_state_starts_pending PASSED           [ 75%]
tests/test_guardrail.py::test_hitl_state_approve_transition PASSED       [ 81%]
tests/test_guardrail.py::test_hitl_state_reject_transition PASSED        [ 87%]
tests/test_guardrail.py::test_hitl_state_cannot_approve_after_rejected PASSED [ 93%]
tests/test_guardrail.py::test_hitl_state_cannot_reject_after_approved PASSED [100%]
============================== 16 passed in 0.08s ==============================
```

Full suite regression check: **32/32 passed** (16 new guardrail + 16 existing across tasks 1-4, no regressions).

## Implementation Notes
- `guardrail()` inspects only `bash` actions; non-bash actions short-circuit to PASS at layer 1 (scope fence handles file actions separately).
- Blocked patterns are checked before HITL patterns, so `rm -rf /` (blocked) takes precedence over `rm` (HITL).
- `check_scope()` only applies to file-touching actions (`read`/`write`/`glob`/`grep`); `bash` and others bypass it.
- `HitlState` is a strict PENDING → {APPROVED, REJECTED} state machine; both terminal states reject further transitions with `RuntimeError("cannot transition ...")`.
- All three layers consume `Action`/`GuardrailResult` (Task 1) and `Config` (Task 3) as specified.

## Concerns
- **Scope fence path containment uses `str.startswith`** (per brief Step 8 verbatim). This is a known weakness: an allowed dir `/foo` would incorrectly match a target `/foobar/baz`. The robust check would be `target == allowed_resolved or allowed_resolved in target.parents`. All current tests pass because they use distinct sibling paths, but this should be hardened before production use. Left as-is to match the brief's TDD spec exactly.
- **No lint/typecheck configured**: project has no `ruff`/`mypy`/`pyproject.toml`; `pytest` is the only verification tool. Ran it as the verification step.
- **Minor**: Git emitted LF→CRLF warnings on Windows; harmless, files committed with LF.

## Report Path
`D:\Users Files\86189\Documents\New OpenCode Project\.superpowers\sdd\task-5-report.md`
