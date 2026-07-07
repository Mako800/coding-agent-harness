# Task 10 Report: Agent Loop

## Status
COMPLETE

## Summary
Implemented `AgentLoop` — the integration layer that wires together LLM, ToolRegistry, Config, Guardrail (layer 1 command detection + layer 2 HITL + layer 3 scope fence), Feedback, Memory, and the action parser into a single agentic loop. Followed strict TDD: wrote the failing test first, confirmed `ModuleNotFoundError`, wrote the minimal implementation, confirmed green.

## Files
- Created: `src/harness/agent_loop.py` (87 lines)
- Created: `tests/test_agent_loop.py` (30 lines, 2 tests)

## TDD Cycle
1. **RED** — wrote `tests/test_agent_loop.py` verbatim from brief. Ran `pytest tests/test_agent_loop.py -v` → failed with `ModuleNotFoundError: No module named 'harness.agent_loop'` (expected: feature missing).
2. **GREEN** — wrote `src/harness/agent_loop.py` verbatim from brief. Ran `pytest tests/test_agent_loop.py -v` → 2 passed.
3. **Regression** — ran full suite `pytest -q` → 57 passed (2 new + 55 existing), no regressions.

## Commit
- `d59f478` — `feat(agent-loop): add main loop with guardrail integration`
- 2 files changed, 101 insertions(+)

## Test Summary
```
tests/test_agent_loop.py::test_loop_returns_final_answer PASSED
tests/test_agent_loop.py::test_loop_executes_tool_then_answers PASSED
============================== 2 passed in 0.07s ==============================
```
Full suite: `57 passed in 1.62s`

## Design Notes
- `run(user_input)` builds a system prompt (tool list + memory summary + final-answer instruction), appends the user message, then loops up to 20 steps.
- Each step: ask LLM → check for `<FINAL_ANSWER>` → else parse `<action>` tags → execute each through the guardrail stack → feed formatted `Signal` back as a `tool` message.
- `_execute_with_guardrail` enforces the three-layer fence: BLOCK → return error `ToolResult`; HITL_PENDING → prompt via injectable `hitl_input` (defaults to `input()`), reject returns error `ToolResult`; then `check_scope` BLOCK → error `ToolResult`; else `registry.execute(action)`.
- `hitl_input` is constructor-injectable, so HITL paths are testable without monkeypatching `input`.

## Concerns
1. **`HitlState` is side-effect only.** In the HITL branch a `HitlState` is instantiated and `approve()`/`reject()` called, but the object is then discarded — its only purpose is to validate the transition (raising on illegal transitions). This matches the brief exactly but the state is never persisted or inspected downstream. Acceptable for now; a future task may want to record the decision.
2. **Hardcoded step cap.** The 20-iteration limit is a magic number. Fine for a harness scaffold; could be moved to `Config` later.
3. **No explicit return type on `_execute_with_guardrail`.** All branches return `ToolResult` (the registry's `execute` also returns `ToolResult`), so it is consistent in practice, but the signature lacks an annotation. Matches brief.
4. **Raw-response fallback.** If the LLM returns text with neither `<FINAL_ANSWER>` nor parseable `<action>` tags, `run` returns the raw response. This is a sensible non-hanging fallback but means a malformed LLM output short-circuits the loop without a tool round-trip.
5. **Line-ending warnings.** Git emitted `LF will be replaced by CRLF` notices on commit (Windows). Cosmetic only; files were committed correctly.

## Report Path
`D:\Users Files\86189\Documents\New OpenCode Project\.superpowers\sdd\task-10-report.md`
