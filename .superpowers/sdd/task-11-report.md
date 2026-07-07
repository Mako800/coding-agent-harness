# Task 11 Report: CLI Entry Point

## Status
COMPLETE — all tests passing, committed.

## Files Created
- `src/harness/cli.py` — argparse-based CLI with `config` subcommands (show-key/set-key/clear-key) and REPL loop wiring `AgentLoop`, `CredentialManager`, `load_config`, `DeepSeekLLM`/`MockLLM`.
- `src/harness/__main__.py` — enables `python -m harness`.
- `tests/test_cli.py` — 2 subprocess smoke tests.

## Commits
- `96db3f8` — feat(cli): add REPL entry point and config subcommands (3 files, +90 lines)

## Test Summary
- `tests/test_cli.py`: **2 passed** (`test_cli_help_runs`, `test_cli_config_subcommand`)
- Full suite: **59 passed** in 2.42s (57 pre-existing + 2 new, no regressions)

## TDD Process
1. Wrote `tests/test_cli.py` (failing) → ran → FAILED (module not found / no impl).
2. Wrote `src/harness/cli.py` and `src/harness/__main__.py` exactly per brief.
3. Ran tests → initially FAILED due to subprocess path issue (see Concern #1).
4. Applied minimal test fix → PASSED.

## Deviation from Brief
`tests/test_cli.py` deviates from the brief's verbatim test code. The brief's test uses `subprocess.run([sys.executable, "-m", "harness", ...])` with no path setup. The project uses a `src/`-layout with no install step (no `pyproject.toml`/`setup.py`); `conftest.py` only inserts `src` into the pytest process's `sys.path`, which does **not** propagate to spawned subprocesses. As written, the verbatim test fails with `No module named harness`.

To make the committed test self-contained and passing under bare `python -m pytest` (the brief's Step 4 intent), the test passes an `env` to `subprocess.run` that prepends the project's `src` directory to `PYTHONPATH` (resolved relative to the test file). `cli.py` and `__main__.py` are **exactly** as specified in the brief.

## Concerns
1. **Subprocess path discovery (resolved in test, root cause unaddressed).** The `src/`-layout package is not installed and `conftest.py`'s `sys.path` insert does not reach subprocesses. The robust project-level fix would be either (a) adding a `pyproject.toml` and `pip install -e .`, or (b) extending `conftest.py` to also set the `PYTHONPATH` env var for subprocesses. Both are out of this task's file scope, so the fix was localized to the test. Future subprocess-based tests will hit the same issue.
2. **`config show-key` uses default env name.** The `config` subcommand constructs `CredentialManager()` with the default `api_key_env="DEEPSEEK_API_KEY"` rather than reading `cfg.api_key_env` (no config is loaded in that branch). This matches the brief verbatim, but means `show-key`/`set-key`/`clear-key` always target `DEEPSEEK_API_KEY` regardless of config. Acceptable for now; flagged for consistency.
3. **REPL path is untested.** The interactive loop (lines 55–65 of `cli.py`) is not covered by the smoke tests, as it blocks on `input()`. Mock-LLM mode (`--mock`) and the no-key exit path (`sys.exit(1)`) are not exercised by automated tests.
4. **Windows line-ending warnings.** Git warned about LF→CRLF on commit; cosmetic only.

## Report Path
`D:\Users Files\86189\Documents\New OpenCode Project\.superpowers\sdd\task-11-report.md`
