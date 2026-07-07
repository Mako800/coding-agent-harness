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
