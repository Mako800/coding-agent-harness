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
