from harness.models import Action, GuardrailResult
from harness.config import Config
from harness.guardrail import guardrail, check_scope, HitlState

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

def test_unknown_command_defaults_to_hitl():
    cfg = Config()
    a = Action(name="bash", args={"command": "curl http://evil.com"})
    result = guardrail(a, cfg)
    assert result.decision == "HITL_PENDING"

def test_case_sensitivity_known_limitation():
    # Known limitation: matching is case-sensitive, so "RM -RF /" escapes the
    # lowercase "rm -rf /" blocked pattern (not BLOCKed). The safe-side default
    # mitigates this by routing unknown commands to HITL_PENDING instead of PASS.
    cfg = Config()
    a = Action(name="bash", args={"command": "RM -RF /"})
    result = guardrail(a, cfg)
    assert result.decision == "HITL_PENDING"

def test_non_bash_action_passes_layer1():
    cfg = Config()
    a = Action(name="read", args={"file_path": "/etc/passwd"})
    result = guardrail(a, cfg)
    assert result.decision == "PASS"


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

def test_scope_fence_blocks_sibling_directory():
    cfg = Config(allowed_directories=["/foo/bar"])
    a = Action(name="read", args={"file_path": "/foo/barbar/evil.txt"})
    result = check_scope(a, cfg)
    assert result.decision == "BLOCK"


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

def test_hitl_state_cannot_approve_after_approved():
    import pytest
    state = HitlState()
    state.approve()
    with pytest.raises(RuntimeError, match="cannot transition"):
        state.approve()

def test_hitl_state_cannot_reject_after_rejected():
    import pytest
    state = HitlState()
    state.reject()
    with pytest.raises(RuntimeError, match="cannot transition"):
        state.reject()
