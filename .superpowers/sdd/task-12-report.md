# Task 12 Report: Mechanism Demonstration (§A.6)

## Status
✅ COMPLETE

## Commits
- `5a0f45a` — feat(demo): add §A.6 mechanism demonstration (3 scenarios)

## Files Created
- `demo/run_demo.py` — standalone demo script (59 lines), verbatim from brief
- `tests/test_demo.py` — 3 demo scenario tests (54 lines), verbatim from brief

## Test Summary
```
tests/test_demo.py::test_demo_1_guardrail_blocks_dangerous_action PASSED [ 33%]
tests/test_demo.py::test_demo_2_feedback_drives_self_correction PASSED   [ 66%]
tests/test_demo.py::test_demo_3_hitl_state_machine PASSED                [100%]
============================== 3 passed in 0.08s ==============================
```

Full suite regression check: **62/62 passed** (no regressions).

Standalone execution (`python demo/run_demo.py`): prints all 3 demo sections, ends with "All demos passed."

## Scenarios Demonstrated
1. **Guardrail blocks dangerous action** — `rm -rf /` → `BLOCK` (matched blocked pattern). Shows layer-1 command detection.
2. **Feedback loop drives self-correction** — MockLLM first emits a `bash cat nonexistent.txt` action (nonzero exit → ERROR signal fed back), then a `read` of the real target file (success), then `FINAL_ANSWER`. Shows the feedback signal being appended to messages and the agent adapting its next action.
3. **HITL state machine** — `HitlState()` starts at `PENDING`, `approve()` transitions to `APPROVED`. Shows the deep-focus dimension state machine.

## TDD Process Note
The brief's Step 2 expected the test to fail with `ModuleNotFoundError`. In practice the test passed **green immediately** on first run because it only imports from `harness.*` modules, all of which were implemented in Tasks 1–11. The test is therefore an **integration test** of already-built mechanisms, not a unit test of newly-introduced code. The genuine "implementation" artifact for this task is the standalone `demo/run_demo.py` script, which is not imported by the test (it is verified separately via `python demo/run_demo.py`).

This is the expected outcome given the task ordering (Task 12 consumes all prior modules) and does not indicate a defect. The red→green transition is trivially satisfied because the consumed surface already exists and behaves correctly.

## Concerns
- **TDD red phase not observable** for this task (see note above). Inherent to a "demonstration" task that wires together existing modules; not fixable without artificially coupling the test to the demo script, which the brief deliberately avoids.
- **Git LF→CRLF warnings** on commit — normal on Windows, harmless, no action needed.
- **Demo 2 relies on `cat` being an allowed command** in the default `Config.allowed_commands` (it is: `"cat"` is listed). The first action returns exit code 1 (file not found) which the `bash` tool surfaces via `subprocess`, and `Feedback.parse` classifies as `FAILURE`. The feedback text is appended to messages, driving the MockLLM's next (pre-programmed) response. This correctly exercises the feedback→self-correction path.

## Report Path
`D:\Users Files\86189\Documents\New OpenCode Project\.superpowers\sdd\task-12-report.md`
