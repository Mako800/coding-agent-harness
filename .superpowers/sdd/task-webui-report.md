# Task Report: Add WebUI to Coding Agent Harness

**Status:** Complete
**Commit:** `0e3c4ca` — feat(webui): add Flask web interface with chat UI
**Date:** 2026-07-07

## Summary

Added a Flask web interface that wraps the existing Coding Agent Harness. The web UI exposes a chat endpoint backed by the same `AgentLoop` used by the CLI REPL, so all governance (guardrail, HITL, scope fence) and feedback behavior is reused unchanged.

## Files

### Created
- `src/harness/web.py` — Flask app factory `create_app(config_path, mock)` with three routes:
  - `GET /` — renders the chat UI
  - `POST /api/chat` — runs the agent loop on the posted `message`; supports `mock=True` for keyless testing
  - `GET /api/health` — liveness probe returning `{"status":"ok"}`
- `templates/index.html` — minimal chat UI (project root, as required). `template_folder` in `web.py` resolves to `<project>/templates` via `os.path.join(os.path.dirname(__file__), "..", "..", "templates")`.
- `tests/test_web.py` — 4 tests covering health, index page, mock chat, and empty-message 400.

### Modified
- `pyproject.toml` — added `flask>=3.0` to `dependencies`.
- `src/harness/cli.py` — added `--web` flag. When set, the CLI imports `create_app` and starts the Flask server on `0.0.0.0:5000` instead of entering the REPL. The flag composes with `--mock` and `--config`.

## Verification

### Web UI tests
```
python -m pytest tests/test_web.py -v
============================= 4 passed in 0.34s ==============================
```
- `test_health_endpoint` — 200, `status == "ok"`
- `test_index_page` — 200, page contains "Coding Agent Harness"
- `test_chat_mock_mode` — 200, response contains "mock mode"
- `test_chat_empty_message` — 400 for empty message

### Full suite
```
python -m pytest tests/ -v
============================= 66 passed in 2.64s =============================
```
All 62 pre-existing tests still pass; 4 new web tests added (62 → 66).

### CLI flag
`harness --help` now lists `--web  Start Flask web server instead of REPL`.

## Dependencies
- `flask` was already installed in the environment (3.1.2). Added to `pyproject.toml` so it is declared as a project dependency.

## Notes
- Only task-relevant files were committed. Pre-existing untracked files (`.gitlab-ci.yml`, `.superpowers/`, `AGENT_LOG.md`, `SPEC_PROCESS.md`) were left unstaged.
- The `templates/` folder lives at the project root as instructed; `web.py` points `template_folder` there explicitly rather than relying on Flask's default `templates/` next to the app module (which would be `src/harness/templates`).
- In non-mock mode, `/api/chat` returns HTTP 500 with a helpful message if no API key is configured, so the UI surfaces the same key-setup instruction as the CLI.
