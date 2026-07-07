# Task 1: Data Models

**Files:**
- Create: `src/harness/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Produces: `Message(role: str, content: str)`, `Action(name: str, args: dict)`, `ToolResult(stdout: str, stderr: str, exit_code: int)`, `GuardrailResult(decision: str, reason: str)`, `Signal(status: str, summary: str)`

## Step 1: Write the failing test

```python
# tests/test_models.py
from harness.models import Message, Action, ToolResult, GuardrailResult, Signal

def test_message_creation():
    m = Message(role="user", content="hello")
    assert m.role == "user"
    assert m.content == "hello"

def test_action_creation():
    a = Action(name="bash", args={"command": "ls"})
    assert a.name == "bash"
    assert a.args["command"] == "ls"

def test_tool_result_fields():
    r = ToolResult(stdout="out", stderr="err", exit_code=0)
    assert r.stdout == "out"
    assert r.stderr == "err"
    assert r.exit_code == 0

def test_guardrail_result_decisions():
    for decision in ("PASS", "BLOCK", "HITL_PENDING"):
        g = GuardrailResult(decision=decision, reason="test")
        assert g.decision == decision

def test_signal_statuses():
    for status in ("SUCCESS", "FAILURE", "ERROR"):
        s = Signal(status=status, summary="test")
        assert s.status == status
```

## Step 2: Run test to verify it fails

Run: `pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'harness'`

## Step 3: Write minimal implementation

```python
# src/harness/models.py
from dataclasses import dataclass

@dataclass
class Message:
    role: str
    content: str

@dataclass
class Action:
    name: str
    args: dict

@dataclass
class ToolResult:
    stdout: str
    stderr: str
    exit_code: int

@dataclass
class GuardrailResult:
    decision: str
    reason: str

@dataclass
class Signal:
    status: str
    summary: str
```

## Step 4: Run test to verify it passes

Run: `pytest tests/test_models.py -v`
Expected: PASS (5 tests)

## Step 5: Commit

```bash
git add src/harness/models.py tests/test_models.py
git commit -m "feat(models): add core dataclasses for harness"
```
