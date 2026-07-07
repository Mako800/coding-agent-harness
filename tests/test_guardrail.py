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
