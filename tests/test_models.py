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
