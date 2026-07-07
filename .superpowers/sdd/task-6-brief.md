# Task 6: Feedback Parser

**Files:**
- Create: `src/harness/feedback.py`
- Test: `tests/test_feedback.py`

**Interfaces:**
- Consumes: `ToolResult`, `Signal` from Task 1
- Produces: `Feedback` class with `parse(result: ToolResult) -> Signal`, `format(signal: Signal) -> str`

## Step 1: Write the failing test

```python
# tests/test_feedback.py
from harness.models import ToolResult, Signal
from harness.feedback import Feedback

def test_parse_success_exit_zero():
    fb = Feedback()
    result = ToolResult(stdout="ok", stderr="", exit_code=0)
    signal = fb.parse(result)
    assert signal.status == "SUCCESS"

def test_parse_failure_nonzero_exit():
    fb = Feedback()
    result = ToolResult(stdout="", stderr="file not found", exit_code=2)
    signal = fb.parse(result)
    assert signal.status == "FAILURE"
    assert "file not found" in signal.summary

def test_parse_error_negative_exit():
    fb = Feedback()
    result = ToolResult(stdout="", stderr="unknown tool", exit_code=-1)
    signal = fb.parse(result)
    assert signal.status == "ERROR"

def test_format_success():
    fb = Feedback()
    s = Signal(status="SUCCESS", summary="command ran fine")
    text = fb.format(s)
    assert "SUCCESS" in text
    assert "command ran fine" in text

def test_format_failure_includes_stderr():
    fb = Feedback()
    s = Signal(status="FAILURE", summary="exit 1: syntax error")
    text = fb.format(s)
    assert "FAILURE" in text
    assert "syntax error" in text
```

## Step 2: Run test to verify it fails

Run: `pytest tests/test_feedback.py -v`
Expected: FAIL with `ModuleNotFoundError`

## Step 3: Write minimal implementation

```python
# src/harness/feedback.py
from .models import ToolResult, Signal

class Feedback:
    def parse(self, result: ToolResult) -> Signal:
        if result.exit_code == 0:
            return Signal(status="SUCCESS", summary=f"exit 0: {result.stdout[:200]}")
        if result.exit_code < 0:
            return Signal(status="ERROR", summary=f"exit {result.exit_code}: {result.stderr[:200]}")
        return Signal(status="FAILURE", summary=f"exit {result.exit_code}: {result.stderr[:200]}")

    def format(self, signal: Signal) -> str:
        return f"[{signal.status}] {signal.summary}"
```

## Step 4: Run test to verify it passes

Run: `pytest tests/test_feedback.py -v`
Expected: PASS (5 tests)

## Step 5: Commit

```bash
git add src/harness/feedback.py tests/test_feedback.py
git commit -m "feat(feedback): add result parser and signal formatter"
```
