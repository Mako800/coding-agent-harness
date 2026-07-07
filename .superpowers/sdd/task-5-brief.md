# Task 5: Guardrail — Governance Core (DEEP FOCUS)

**Files:**
- Create: `src/harness/guardrail.py`
- Test: `tests/test_guardrail.py`

**Interfaces:**
- Consumes: `Action`, `GuardrailResult` from Task 1; `Config` from Task 3
- Produces: `guardrail(action: Action, config: Config) -> GuardrailResult`, `HitlState` (state machine), `check_scope(action: Action, config: Config) -> GuardrailResult`

This task has 3 layers, implemented in 3 TDD cycles (15 steps total).

## Layer 1: Command Detection (Steps 1-5)

### Step 1: Write failing tests

```python
# tests/test_guardrail.py
from harness.models import Action, GuardrailResult
from harness.config import Config
from harness.guardrail import guardrail

def test_blocked_command_rm_rf_root():
    cfg = Config()
    a = Action(name="bash", args={"command": "rm -rf /"})
    result = guardrail(a, cfg)
    assert result.decision == "BLOCK"
    assert "rm -rf /" in result.reason or "blocked" in result.reason.lower()

def test_blocked_command_dd():
    cfg = Config()
    a = Action(name="bash", args={"command": "dd if=/dev/zero of=/dev/sda"})
    result = guardrail(a, cfg)
    assert result.decision == "BLOCK"

def test_hitl_command_rm_file():
    cfg = Config()
    a = Action(name="bash", args={"command": "rm somefile.txt"})
    result = guardrail(a, cfg)
    assert result.decision == "HITL_PENDING"

def test_hitl_command_sudo():
    cfg = Config()
    a = Action(name="bash", args={"command": "sudo apt update"})
    result = guardrail(a, cfg)
    assert result.decision == "HITL_PENDING"

def test_pass_command_ls():
    cfg = Config()
    a = Action(name="bash", args={"command": "ls -la"})
    result = guardrail(a, cfg)
    assert result.decision == "PASS"

def test_pass_command_pytest():
    cfg = Config()
    a = Action(name="bash", args={"command": "pytest -v"})
    result = guardrail(a, cfg)
    assert result.decision == "PASS"

def test_non_bash_action_passes_layer1():
    cfg = Config()
    a = Action(name="read", args={"file_path": "/etc/passwd"})
    result = guardrail(a, cfg)
    assert result.decision == "PASS"
```

### Step 2: Run test to verify it fails

Run: `pytest tests/test_guardrail.py -v`
Expected: FAIL with `ModuleNotFoundError`

### Step 3: Write minimal implementation

```python
# src/harness/guardrail.py
from .models import Action, GuardrailResult
from .config import Config

def guardrail(action: Action, config: Config) -> GuardrailResult:
    if action.name != "bash":
        return GuardrailResult(decision="PASS", reason="non-bash action, layer 1 pass")
    command = action.args.get("command", "")
    for blocked in config.blocked_commands:
        if blocked in command:
            return GuardrailResult(decision="BLOCK", reason=f"matched blocked pattern: {blocked}")
    for hitl in config.hitl_commands:
        if hitl in command:
            return GuardrailResult(decision="HITL_PENDING", reason=f"matched HITL pattern: {hitl}")
    return GuardrailResult(decision="PASS", reason="no dangerous pattern matched")
```

### Step 4: Run test to verify it passes

Run: `pytest tests/test_guardrail.py -v`
Expected: PASS (7 tests)

### Step 5: Commit

```bash
git add src/harness/guardrail.py tests/test_guardrail.py
git commit -m "feat(guardrail): layer 1 command detection"
```

## Layer 3: Scope Fence (Steps 6-10)

### Step 6: Write failing tests

```python
# append to tests/test_guardrail.py
from harness.guardrail import check_scope

def test_scope_fence_blocks_outside_directory(tmp_path):
    cfg = Config(allowed_directories=[str(tmp_path)])
    outside = tmp_path.parent / "secret.txt"
    a = Action(name="read", args={"file_path": str(outside)})
    result = check_scope(a, cfg)
    assert result.decision == "BLOCK"

def test_scope_fence_allows_inside_directory(tmp_path):
    cfg = Config(allowed_directories=[str(tmp_path)])
    inside = tmp_path / "code.py"
    a = Action(name="read", args={"file_path": str(inside)})
    result = check_scope(a, cfg)
    assert result.decision == "PASS"

def test_scope_fence_write_blocked_outside(tmp_path):
    cfg = Config(allowed_directories=[str(tmp_path)])
    a = Action(name="write", args={"file_path": "/etc/passwd", "content": "hacked"})
    result = check_scope(a, cfg)
    assert result.decision == "BLOCK"

def test_scope_fence_bash_not_checked():
    cfg = Config(allowed_directories=["."])
    a = Action(name="bash", args={"command": "ls"})
    result = check_scope(a, cfg)
    assert result.decision == "PASS"
```

### Step 7: Run test to verify it fails

Run: `pytest tests/test_guardrail.py::test_scope_fence_blocks_outside_directory -v`
Expected: FAIL with `ImportError: cannot import name 'check_scope'`

### Step 8: Write minimal implementation

```python
# append to src/harness/guardrail.py
from pathlib import Path

def check_scope(action: Action, config: Config) -> GuardrailResult:
    if action.name not in ("read", "write", "glob", "grep"):
        return GuardrailResult(decision="PASS", reason="non-file action, scope not checked")
    path_key = "file_path" if "file_path" in action.args else "path"
    if path_key not in action.args:
        return GuardrailResult(decision="PASS", reason="no path argument")
    target = Path(action.args[path_key]).resolve()
    for allowed in config.allowed_directories:
        allowed_resolved = Path(allowed).expanduser().resolve()
        if str(target).startswith(str(allowed_resolved)):
            return GuardrailResult(decision="PASS", reason=f"path within allowed: {allowed}")
    return GuardrailResult(decision="BLOCK", reason=f"path outside allowed directories: {target}")
```

### Step 9: Run test to verify it passes

Run: `pytest tests/test_guardrail.py -v`
Expected: PASS (11 tests)

### Step 10: Commit

```bash
git add src/harness/guardrail.py tests/test_guardrail.py
git commit -m "feat(guardrail): layer 3 scope fence"
```

## Layer 2: HITL State Machine (Steps 11-15)

### Step 11: Write failing tests

```python
# append to tests/test_guardrail.py
from harness.guardrail import HitlState

def test_hitl_state_starts_pending():
    state = HitlState()
    assert state.current == "PENDING"

def test_hitl_state_approve_transition():
    state = HitlState()
    state.approve()
    assert state.current == "APPROVED"

def test_hitl_state_reject_transition():
    state = HitlState()
    state.reject()
    assert state.current == "REJECTED"

def test_hitl_state_cannot_approve_after_rejected():
    import pytest
    state = HitlState()
    state.reject()
    with pytest.raises(RuntimeError, match="cannot transition"):
        state.approve()

def test_hitl_state_cannot_reject_after_approved():
    import pytest
    state = HitlState()
    state.approve()
    with pytest.raises(RuntimeError, match="cannot transition"):
        state.reject()
```

### Step 12: Run test to verify it fails

Run: `pytest tests/test_guardrail.py::test_hitl_state_starts_pending -v`
Expected: FAIL with `ImportError`

### Step 13: Write minimal implementation

```python
# append to src/harness/guardrail.py
class HitlState:
    _TRANSITIONS = {
        "PENDING": {"APPROVED", "REJECTED"},
        "APPROVED": set(),
        "REJECTED": set(),
    }

    def __init__(self):
        self.current = "PENDING"

    def _transition(self, new_state: str):
        allowed = self._TRANSITIONS.get(self.current, set())
        if new_state not in allowed:
            raise RuntimeError(f"cannot transition from {self.current} to {new_state}")
        self.current = new_state

    def approve(self):
        self._transition("APPROVED")

    def reject(self):
        self._transition("REJECTED")
```

### Step 14: Run test to verify it passes

Run: `pytest tests/test_guardrail.py -v`
Expected: PASS (16 tests)

### Step 15: Commit

```bash
git add src/harness/guardrail.py tests/test_guardrail.py
git commit -m "feat(guardrail): layer 2 HITL state machine"
```
