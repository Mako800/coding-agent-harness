from .models import Action, GuardrailResult
from .config import Config
from pathlib import Path


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
    for allowed in config.allowed_commands:
        if allowed in command:
            return GuardrailResult(decision="PASS", reason=f"matched allowed command: {allowed}")
    return GuardrailResult(decision="HITL_PENDING", reason="unknown command, safe-side default")


def check_scope(action: Action, config: Config) -> GuardrailResult:
    if action.name not in ("read", "write", "glob", "grep"):
        return GuardrailResult(decision="PASS", reason="non-file action, scope not checked")
    path_key = "file_path" if "file_path" in action.args else "path"
    if path_key not in action.args:
        return GuardrailResult(decision="PASS", reason="no path argument")
    target = Path(action.args[path_key]).resolve()
    for allowed in config.allowed_directories:
        allowed_resolved = Path(allowed).expanduser().resolve()
        if target == allowed_resolved or allowed_resolved in target.parents:
            return GuardrailResult(decision="PASS", reason=f"path within allowed: {allowed}")
    return GuardrailResult(decision="BLOCK", reason=f"path outside allowed directories: {target}")


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
