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
