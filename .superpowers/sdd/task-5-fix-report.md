# Task 5 Fix Report — Guardrail (deep focus)

## Status
Complete. All reviewer issues fixed, all tests green, committed.

## Commits
- `27b20d9` — `fix(guardrail): safe-side default, path containment, edge tests`
  - `src/harness/config.py`, `src/harness/guardrail.py`, `tests/test_guardrail.py`
  - 3 files changed, 42 insertions(+), 2 deletions(-)

Note: committed only the three intended source/test files. The untracked
`.superpowers/` directory (SDD workflow artifacts: briefs/reports/diffs) was
intentionally left out of the fix commit.

## Test Summary
- `python -m pytest tests/test_guardrail.py -v` → **21 passed**
- `python -m pytest tests/ -v` → **37 passed** (no regressions)

New tests added (5):
- `test_unknown_command_defaults_to_hitl` — `curl http://evil.com` → HITL_PENDING
- `test_scope_fence_blocks_sibling_directory` — `/foo/barbar/evil.txt` blocked when allowed is `/foo/bar`
- `test_hitl_state_cannot_approve_after_approved` — double-approve raises RuntimeError
- `test_hitl_state_cannot_reject_after_rejected` — double-reject raises RuntimeError
- `test_case_sensitivity_known_limitation` — documents case-sensitive matching limitation

Existing `test_pass_command_ls` / `test_pass_command_pytest` still PASS (both
are in `allowed_commands`).

## Fixes Applied

### Critical Fix 1 — Unknown bash commands default to HITL_PENDING
- `config.py`: added `allowed_commands` field with safe defaults
  (`ls`, `cat`, `echo`, `pwd`, `pytest`, `python`, `pip`, `git status`,
  `git diff`, `git log`, `git add`, `git commit`). Also wired into
  `load_config` YAML loader (`guardrail.allowed_commands`).
- `guardrail.py`: `guardrail()` logic is now:
  1. match `blocked_commands` → BLOCK
  2. match `hitl_commands` → HITL_PENDING
  3. match `allowed_commands` → PASS
  4. everything else → HITL_PENDING (safe-side default)

### Important Fix 2 — Path containment check
- `guardrail.py`: `check_scope()` replaced exploitable
  `str(target).startswith(str(allowed_resolved))` with proper containment:
  `target == allowed_resolved or allowed_resolved in target.parents`.
  This blocks sibling-directory escape (e.g. allowed `/foo/bar` no longer
  admits `/foo/barbar/evil.txt`). Verified on Windows: old `startswith`
  admitted the sibling; new check correctly blocks it.

### Important Fix 3 — Edge-case tests
- Added the 5 new tests listed above.

## Design Decision / Reconciliation

The reviewer's Important Fix 3 specified `test_case_sensitivity_known_limitation`
as "document that `RM -RF /` passes". This conflicts with Critical Fix 1's
safe-side default: `RM -RF /` does not match the lowercase `rm -rf /` blocked
pattern (case-sensitive), is not in `hitl_commands` or `allowed_commands`, so
under the new safe-side default it routes to **HITL_PENDING**, not PASS.

Resolution: Critical Fix 1 (security: safe-side default) takes priority over
documenting the pre-fix PASS behavior. The test therefore asserts
`HITL_PENDING` and documents (via comment) that case-sensitive matching lets
`RM -RF /` escape the BLOCK check — a known limitation now mitigated by the
safe-side default. Asserting PASS would have failed under the required
safe-side default, so this is the only consistent choice.

If the intent was instead to assert literal PASS, the safe-side default
(Critical Fix 1) would need to be relaxed — not recommended for a guardrail.
