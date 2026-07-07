# Task 3 Report: Config Loader

## Status
COMPLETE

## Commits
- `a7293cd` feat(config): add YAML config loader with defaults

## Files
- Created: `src/harness/config.py`
- Created: `tests/test_config.py`

## Test Summary
```
python -m pytest tests/test_config.py -v
3 passed in 0.09s

  tests/test_config.py::test_load_config_from_yaml PASSED
  tests/test_config.py::test_load_config_missing_file_uses_defaults PASSED
  tests/test_config.py::test_load_config_invalid_yaml_uses_defaults PASSED
```
Full suite regression check: 11 passed (3 new + 8 existing), 0 failures.

## TDD Process Followed
1. Wrote `tests/test_config.py` first (3 tests, verbatim from brief).
2. Ran pytest → failed with `ModuleNotFoundError: No module named 'harness.config'` (expected).
3. Wrote `src/harness/config.py` per brief.
4. Ran pytest → 2 passed, 1 FAILED (`test_load_config_invalid_yaml_uses_defaults`).
5. Root-caused the failure (see below), applied minimal fix.
6. Ran pytest → 3 passed. Full suite → 11 passed.
7. Committed.

## Bug Found & Fixed (deviation from brief's exact code)
The brief's `load_config` used:
```python
data = yaml.safe_load(f) or {}
```
This assumes `yaml.safe_load` either returns a dict or raises. It does neither for the test input `":::not valid yaml:::["` — PyYAML parses it as a valid YAML **scalar string** (`':::not valid yaml:::['`, truthy), so `or {}` keeps the string and `data.get("llm", {})` raises `AttributeError: 'str' object has no attribute 'get'`.

**Root cause** (verified via `python -c "import yaml; ..."` → `type: str`, `truthy: True`): YAML is a superset that happily parses scalars; "invalid config" is not the same as "invalid YAML".

**Fix** (single change, root-cause addressed):
```python
data = yaml.safe_load(f)
if not isinstance(data, dict):
    return Config()
```
This is strictly more robust than `or {}`: it falls back to defaults for `None` (empty file), strings, lists, numbers, or any other non-mapping scalar — exactly the "use defaults on bad input" contract the test asserts.

## Self-Review
- **Interface:** `Config` dataclass has all 8 required fields; `load_config(path: str) -> Config` signature matches brief.
- **Defaults:** All fields have sensible defaults (deepseek provider/model, destructive-command blocklist, `["."]` allowed dirs, memory enabled).
- **Conventions:** Matches existing `models.py`/`llm.py` style — dataclasses, bare `list`/`dict` hints, 4-space indent, no comments. Lazy `import yaml`/`import os` kept inside function per brief (yaml treated as optional runtime dep).
- **Mutable defaults:** Uses `field(default_factory=lambda: [...])` — avoids the mutable-default pitfall.
- **No regressions:** Full suite green.

## Concerns
1. **Brief's reference implementation was buggy.** The provided `or {}` pattern fails the brief's own third test. Fixed with `isinstance(data, dict)` guard. Flagging in case downstream tasks copied the same anti-pattern.
2. **Lazy imports** (`os`, `yaml` inside `load_config`) are intentional per brief but slightly unusual; kept as-is for spec fidelity. If preferred, `os` could move to module top (it's always available); `yaml` staying lazy is reasonable since it's an optional dependency.
3. **Unparameterized `list` type hints** (`list` vs `list[str]`) — matches brief and existing `models.py` (`dict`). Consistent within project; not changed.
4. **No validation of list element types** — if a user puts `blocked_commands: 123` (a non-list), it's accepted as-is. Out of scope for this task's tests; noting for a future hardening pass if needed.

## Report Path
D:\Users Files\86189\Documents\New OpenCode Project\.superpowers\sdd\task-3-report.md
