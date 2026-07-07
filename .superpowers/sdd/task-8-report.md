# Task 8 Report: ToolRegistry

## Status
COMPLETE

## Commits
- `b970831` — feat(tools): add ToolRegistry with 5 preset tools
  - `src/harness/tools.py` (71 lines, new)
  - `tests/test_tools.py` (36 lines, new)

## Files
- Created: `src/harness/tools.py`
- Created: `tests/test_tools.py`

## TDD Flow
1. Wrote `tests/test_tools.py` (4 tests) per brief.
2. Ran `python -m pytest tests/test_tools.py -v` → FAIL with `ModuleNotFoundError: No module named 'harness.tools'` (expected).
3. Wrote `src/harness/tools.py` (minimal implementation per brief).
4. Ran `python -m pytest tests/test_tools.py -v` → **4 passed in 0.09s**.
5. Full suite: `python -m pytest -q` → **51 passed in 1.56s** (no regressions).

## Test Summary
| Test | Result |
|------|--------|
| `test_register_and_execute_read` | PASSED |
| `test_unknown_tool_returns_error` | PASSED |
| `test_list_tools` | PASSED |
| `test_bash_tool_executes_command` | PASSED |

## Interfaces
- **Consumes:** `Action`, `ToolResult` from `harness.models` (Task 1) ✓
- **Produces:** `ToolRegistry` class with:
  - `register(name: str, fn)` ✓
  - `execute(action: Action) -> ToolResult` ✓
  - `list_tools() -> list[str]` ✓
  - `make_default_registry() -> ToolRegistry` ✓
- **5 preset tools:** `read`, `write`, `bash`, `glob`, `grep` ✓

## Self-Review
- Implementation and tests match the task brief verbatim.
- `execute` handles unknown tools (exit_code=-1, stderr message) and wraps exceptions (exit_code=1) defensively.
- All 4 specified tests pass; full 51-test suite passes with no regressions.
- Code follows existing project conventions (dataclasses from `models.py`, relative import `from .models import ...`).

## Concerns
1. **`bash` tool uses `shell=True`** — command-injection risk in production, but matches the brief's spec for this learning harness.
2. **`read_file` does not pass `errors="ignore"`** (unlike `grep_files`), so reading binary files may raise `UnicodeDecodeError`; caught by the try/except and returned as exit_code=1. Minor inconsistency, but per brief.
3. **`grep_files` recursively scans all files** — could be slow on large trees; acceptable for harness scope.
4. **Git line-ending warning** (LF→CRLF on Windows) — cosmetic only.

## Report Path
`D:\Users Files\86189\Documents\New OpenCode Project\.superpowers\sdd\task-8-report.md`
