# Task 9 Report: Action Parser

## Status
COMPLETE

## Commits
- `979c1f0` — feat(parser): add LLM output action parser

## Files
- Created: `src/harness/parser.py` (16 lines)
- Created: `tests/test_parser.py` (28 lines, 4 tests)

## Interface
- `parse_actions(text: str) -> list[Action]` — parses `<action name="X" args='{"k":"v"}' />` tags into `Action` dataclass instances from `harness.models`.

## Implementation Summary
- Module-level compiled regex `_ACTION_RE` matches the self-closing `<action ... />` tag with `name` in double quotes and `args` JSON in single quotes.
- `parse_actions` iterates all matches via `finditer`, attempts `json.loads` on the args capture group, and skips any match whose args fail JSON decoding (returns empty for malformed input).
- Returns `[]` when no tags match (plain text input).

## TDD Process
1. Wrote `tests/test_parser.py` with the 4 tests from the brief.
2. Ran `pytest tests/test_parser.py -v` → FAIL with `ModuleNotFoundError: No module named 'harness.parser'` (expected).
3. Wrote `src/harness/parser.py` per the brief.
4. Ran `pytest tests/test_parser.py -v` → PASS (4 tests).
5. Ran full suite `pytest -v` → PASS (55 tests, no regressions).

## Test Summary
```
tests/test_parser.py::test_parse_single_action PASSED
tests/test_parser.py::test_parse_multiple_actions PASSED
tests/test_parser.py::test_parse_no_actions_returns_empty PASSED
tests/test_parser.py::test_parse_malformed_returns_empty PASSED
```
Full suite: 55 passed in 1.57s.

## Self-Review / Concerns
1. **Strict quote pairing**: The regex requires `name="..."` (double quotes) and `args='...'` (single quotes). If the LLM emits `args="..."` (double quotes around JSON, which would require escaping inner double quotes) or swaps the quote styles, the tag will not match and is silently dropped. This is per the brief's spec but is a fragility worth flagging for the prompt-engineering / integration tasks (Task 10+) — the system prompt must instruct the LLM to emit exactly this quote pairing.
2. **Malformed-test coverage gap**: The brief's `test_parse_malformed_returns_empty` uses `args={bad json}` (no surrounding single quotes), so it returns `[]` because the regex does not match at all — the `json.JSONDecodeError` exception branch is never exercised by this test. A more thorough test would use `args='{bad json}'` (valid regex match, invalid JSON) to exercise the exception path. I kept the test exactly as specified in the brief; flagging here as a test-coverage note.
3. **Empty args**: `args=''` would match the regex but `json.loads('')` raises `JSONDecodeError`, so the action is skipped. Reasonable behavior, but undocumented.
4. **No whitespace tolerance inside args**: The regex `args='([^']*)'` captures the raw JSON string including any leading/trailing whitespace, which `json.loads` tolerates, so this is fine.
5. **`list[Action]` type hint** requires Python 3.9+; environment is 3.13.9, so no issue.
6. No comments added (per codebase convention); style matches neighboring modules (e.g., `feedback.py`, `memory.py`).

## Report Path
D:\Users Files\86189\Documents\New OpenCode Project\.superpowers\sdd\task-9-report.md
