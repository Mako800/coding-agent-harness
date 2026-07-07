# Coding Agent Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal but complete Coding Agent Harness in Python with a deep focus on governance (guardrails / HITL / scope fence).

**Architecture:** Monolithic single-process CLI. Six modules map to the six harness dimensions: AgentLoop (decision), ToolRegistry (tools), Guardrail (governance — deep focus), Feedback (feedback loop), Memory (memory), Config (configuration). LLM abstraction layer supports MockLLM (for deterministic unit tests) and DeepSeekLLM (real API, OpenAI-compatible).

**Tech Stack:** Python 3.10+, `openai` (DeepSeek API), `python-dotenv`, `keyring`, `pyyaml`, `pytest`

## Task Completion Status

| Task | Description | Status | Commit | Subagent |
|------|-------------|--------|--------|----------|
| 1 | Data Models | ✅ Done | `00fb570` | general #1 |
| 2 | LLM Abstraction | ✅ Done | `94cdbe6` | general #2 |
| 3 | Config Loader | ✅ Done | `a7293cd` | general #3 |
| 4 | Credential Manager | ✅ Done | `dff0019` | general #4 |
| 5 | Guardrail Layer 1 | ✅ Done | `5b09886` | general #5 |
| 5 | Guardrail Layer 3 | ✅ Done | `76500cd` | general #5 |
| 5 | Guardrail Layer 2 | ✅ Done | `023c306` | general #5 |
| 5 | Guardrail Fixes | ✅ Done | `27b20d9` | general #5-fix (reviewer-driven) |
| 6 | Feedback Parser | ✅ Done | `95face1` | general #6 |
| 7 | Memory | ✅ Done | `42cec93` | general #7 |
| 8 | ToolRegistry | ✅ Done | `b970831` | general #8 |
| 9 | Action Parser | ✅ Done | `979c1f0` | general #9 |
| 10 | Agent Loop | ✅ Done | `d59f478` | general #10 |
| 11 | CLI Entry Point | ✅ Done | `96db3f8` | general #11 |
| 12 | Mechanism Demo | ✅ Done | `5a0f45a` | general #12 |
| 13 | Packaging+CI | ✅ Done | `9cf5df6` | general #13 |
| — | WebUI | ✅ Done | `0e3c4ca` | general #webui |
| — | CI Fix (build-backend) | ✅ Done | `73e787e` | manual |
| — | CI Fix (NoKeyringError) | ✅ Done | `5d6694a` | manual |

**Total: 66 tests, all passing. Last CI: pass.**

## Global Constraints

- Python 3.10+ required
- All core mechanisms must be unit-testable with MockLLM (no network, no real LLM)
- TDD enforced: red → green → refactor, no implementation before tests
- API key never hardcoded, never committed to Git, never logged
- Distribution: PyPI package `coding-agent-harness`, entry point `harness`
- Single turn max 20 tool calls
- Guardrail defaults to safe side (unknown → HITL_PENDING)

---

## File Structure

```
coding-agent-harness/
├── pyproject.toml              # Package metadata, deps, entry point
├── README.md                   # Install, run, key config, limitations
├── .gitignore                  # .env, __pycache__, dist/, *.egg-info
├── src/
│   └── harness/
│       ├── __init__.py
│       ├── models.py           # Dataclasses: Message, Action, ToolResult, GuardrailResult, Signal
│       ├── llm.py              # LLM abstract base, MockLLM, DeepSeekLLM
│       ├── tools.py            # ToolRegistry + 5 preset tools (read/write/bash/glob/grep)
│       ├── guardrail.py        # guardrail() function + HITL state machine + scope fence (DEEP FOCUS)
│       ├── feedback.py         # Feedback.parse() + format()
│       ├── memory.py           # Memory class (JSON file store)
│       ├── config.py           # Config loader (YAML)
│       ├── credentials.py      # Credential manager (keyring + .env fallback)
│       ├── agent_loop.py       # AgentLoop: context → LLM → parse → guardrail → execute → feedback → loop
│       ├── parser.py           # Parse LLM text output into Action objects
│       └── cli.py              # CLI entry point, REPL
├── tests/
│   ├── conftest.py             # Shared fixtures (tmp config dir, mock actions)
│   ├── test_models.py
│   ├── test_llm.py
│   ├── test_tools.py
│   ├── test_guardrail.py       # Extensive: 3 layers + edge cases
│   ├── test_feedback.py
│   ├── test_memory.py
│   ├── test_config.py
│   ├── test_credentials.py
│   ├── test_parser.py
│   ├── test_agent_loop.py      # MockLLM-driven integration tests
│   └── test_demo.py            # §A.6 mechanism demonstration (3 scenarios)
├── demo/
│   └── run_demo.py             # Standalone mechanism demo script
└── .github/
    └── workflows/
        └── ci.yml              # GitHub Actions: unit-test job
```

---

## Task Dependency Graph

```
Task 1 (models) ─┬─→ Task 2 (llm) ──────────────────────────┐
                  ├─→ Task 3 (config) ─→ Task 4 (credentials)│
                  ├─→ Task 5 (guardrail) ★ deep focus        │
                  ├─→ Task 6 (feedback)                       │
                  ├─→ Task 7 (memory)                         │
                  └─→ Task 8 (tools) ────────────────────────┤
                                                              ▼
                                          Task 9 (parser) → Task 10 (agent_loop) → Task 11 (cli) → Task 12 (demo) → Task 13 (packaging+CI)
```

- Tasks 2-8 depend only on Task 1 (models) — **can be parallelized in worktrees**
- Task 9 (parser) depends on Task 1
- Task 10 (agent_loop) depends on all of 2-9
- Task 11 (cli) depends on Task 10
- Task 12 (demo) depends on Task 10
- Task 13 (packaging) depends on Task 11

---

### Task 1: Data Models

**Files:**
- Create: `src/harness/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Produces: `Message(role: str, content: str)`, `Action(name: str, args: dict)`, `ToolResult(stdout: str, stderr: str, exit_code: int)`, `GuardrailResult(decision: str, reason: str)`, `Signal(status: str, summary: str)`

- [ ] **Step 1: Write the failing test**

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

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'harness'`

- [ ] **Step 3: Write minimal implementation**

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

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add src/harness/models.py tests/test_models.py
git commit -m "feat(models): add core dataclasses for harness"
```

---

### Task 2: LLM Abstraction Layer

**Files:**
- Create: `src/harness/llm.py`
- Test: `tests/test_llm.py`

**Interfaces:**
- Consumes: `Message` from Task 1
- Produces: `LLM` (abstract base), `MockLLM(responses: list[str])`, `DeepSeekLLM(api_key: str, model: str)`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_llm.py
from harness.models import Message
from harness.llm import LLM, MockLLM

def test_mock_llm_returns_responses_in_order():
    llm = MockLLM(responses=["first", "second", "third"])
    msgs = [Message(role="user", content="hi")]
    assert llm.ask(msgs) == "first"
    assert llm.ask(msgs) == "second"
    assert llm.ask(msgs) == "third"

def test_mock_llm_raises_when_exhausted():
    import pytest
    llm = MockLLM(responses=["only"])
    llm.ask([Message(role="user", content="x")])
    with pytest.raises(IndexError):
        llm.ask([Message(role="user", content="x")])

def test_llm_is_abstract():
    import pytest
    with pytest.raises(TypeError):
        LLM()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/harness/llm.py
from abc import ABC, abstractmethod
from .models import Message

class LLM(ABC):
    @abstractmethod
    def ask(self, messages: list[Message]) -> str:
        ...

class MockLLM(LLM):
    def __init__(self, responses: list[str]):
        self._responses = responses
        self._index = 0

    def ask(self, messages: list[Message]) -> str:
        response = self._responses[self._index]
        self._index += 1
        return response

class DeepSeekLLM(LLM):
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self._api_key = api_key
        self._model = model

    def ask(self, messages: list[Message]) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=self._api_key, base_url="https://api.deepseek.com")
        resp = client.chat.completions.create(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        return resp.choices[0].message.content
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/harness/llm.py tests/test_llm.py
git commit -m "feat(llm): add LLM abstraction with MockLLM and DeepSeekLLM"
```

---

### Task 3: Config Loader

**Files:**
- Create: `src/harness/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `Config` dataclass with fields: `llm_provider`, `llm_model`, `api_key_env`, `blocked_commands`, `hitl_commands`, `allowed_directories`, `memory_enabled`, `memory_file`. `load_config(path: str) -> Config`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
import os
from harness.config import Config, load_config

def test_load_config_from_yaml(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("""
llm:
  provider: deepseek
  model: deepseek-chat
  api_key_env: DEEPSEEK_API_KEY
guardrail:
  blocked_commands: ["rm -rf /", "dd if="]
  hitl_commands: ["rm", "sudo"]
  allowed_directories: ["."]
memory:
  enabled: true
  file: ~/.harness/memory.json
""")
    cfg = load_config(str(cfg_file))
    assert cfg.llm_provider == "deepseek"
    assert cfg.llm_model == "deepseek-chat"
    assert "rm -rf /" in cfg.blocked_commands
    assert "rm" in cfg.hitl_commands
    assert cfg.memory_enabled is True

def test_load_config_missing_file_uses_defaults(tmp_path):
    cfg = load_config(str(tmp_path / "nonexistent.yaml"))
    assert cfg.llm_provider == "deepseek"
    assert cfg.memory_enabled is True
    assert "." in cfg.allowed_directories

def test_load_config_invalid_yaml_uses_defaults(tmp_path):
    cfg_file = tmp_path / "bad.yaml"
    cfg_file.write_text(":::not valid yaml:::[[")
    cfg = load_config(str(cfg_file))
    assert cfg.llm_provider == "deepseek"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/harness/config.py
from dataclasses import dataclass, field

@dataclass
class Config:
    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-chat"
    api_key_env: str = "DEEPSEEK_API_KEY"
    blocked_commands: list = field(default_factory=lambda: ["rm -rf /", "dd if=", "format", "mkfs", ":(){:|:&};:"])
    hitl_commands: list = field(default_factory=lambda: ["rm", "sudo", "DROP TABLE", "ALTER TABLE", "git push --force"])
    allowed_directories: list = field(default_factory=lambda: ["."])
    memory_enabled: bool = True
    memory_file: str = "~/.harness/memory.json"

def load_config(path: str) -> Config:
    import os
    if not os.path.exists(path):
        return Config()
    try:
        import yaml
        with open(path) as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        return Config()
    cfg = Config()
    llm = data.get("llm", {})
    if "provider" in llm: cfg.llm_provider = llm["provider"]
    if "model" in llm: cfg.llm_model = llm["model"]
    if "api_key_env" in llm: cfg.api_key_env = llm["api_key_env"]
    g = data.get("guardrail", {})
    if "blocked_commands" in g: cfg.blocked_commands = g["blocked_commands"]
    if "hitl_commands" in g: cfg.hitl_commands = g["hitl_commands"]
    if "allowed_directories" in g: cfg.allowed_directories = g["allowed_directories"]
    m = data.get("memory", {})
    if "enabled" in m: cfg.memory_enabled = m["enabled"]
    if "file" in m: cfg.memory_file = m["file"]
    return cfg
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/harness/config.py tests/test_config.py
git commit -m "feat(config): add YAML config loader with defaults"
```

---

### Task 4: Credential Manager

**Files:**
- Create: `src/harness/credentials.py`
- Test: `tests/test_credentials.py`

**Interfaces:**
- Consumes: `Config` from Task 3
- Produces: `CredentialManager` with methods `get_key() -> str|None`, `set_key(key: str)`, `clear_key()`, `has_key() -> bool`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_credentials.py
import os
from unittest.mock import patch, MagicMock
from harness.credentials import CredentialManager

def test_get_key_from_env_first():
    with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "env-key"}):
        cm = CredentialManager(api_key_env="DEEPSEEK_API_KEY")
        assert cm.get_key() == "env-key"

def test_has_key_false_when_no_key():
    with patch.dict(os.environ, {}, clear=True):
        cm = CredentialManager(api_key_env="DEEPSEEK_API_KEY")
        assert cm.has_key() is False

def test_set_key_uses_keyring():
    with patch.dict(os.environ, {}, clear=True):
        with patch("harness.credentials.keyring") as mock_kr:
            mock_kr.get_password.return_value = None
            cm = CredentialManager(api_key_env="DEEPSEEK_API_KEY")
            cm.set_key("my-secret")
            mock_kr.set_password.assert_called_once_with("coding-agent-harness", "DEEPSEEK_API_KEY", "my-secret")

def test_get_key_falls_back_to_keyring():
    with patch.dict(os.environ, {}, clear=True):
        with patch("harness.credentials.keyring") as mock_kr:
            mock_kr.get_password.return_value = "stored-key"
            cm = CredentialManager(api_key_env="DEEPSEEK_API_KEY")
            assert cm.get_key() == "stored-key"

def test_clear_key_removes_from_keyring():
    with patch.dict(os.environ, {}, clear=True):
        with patch("harness.credentials.keyring") as mock_kr:
            cm = CredentialManager(api_key_env="DEEPSEEK_API_KEY")
            cm.clear_key()
            mock_kr.delete_password.assert_called_once_with("coding-agent-harness", "DEEPSEEK_API_KEY")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_credentials.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/harness/credentials.py
import os
import keyring

SERVICE_NAME = "coding-agent-harness"

class CredentialManager:
    def __init__(self, api_key_env: str = "DEEPSEEK_API_KEY"):
        self._env_name = api_key_env

    def get_key(self) -> str | None:
        key = os.environ.get(self._env_name)
        if key:
            return key
        return keyring.get_password(SERVICE_NAME, self._env_name)

    def has_key(self) -> bool:
        return self.get_key() is not None

    def set_key(self, key: str):
        keyring.set_password(SERVICE_NAME, self._env_name, key)

    def clear_key(self):
        try:
            keyring.delete_password(SERVICE_NAME, self._env_name)
        except keyring.errors.PasswordDeleteError:
            pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_credentials.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add src/harness/credentials.py tests/test_credentials.py
git commit -m "feat(credentials): add keyring+env credential manager"
```

---

### Task 5: Guardrail — Governance Core (DEEP FOCUS)

**Files:**
- Create: `src/harness/guardrail.py`
- Test: `tests/test_guardrail.py`

**Interfaces:**
- Consumes: `Action`, `GuardrailResult` from Task 1; `Config` from Task 3
- Produces: `guardrail(action: Action, config: Config) -> GuardrailResult`, `HitlState` (state machine), `check_scope(action: Action, config: Config) -> GuardrailResult`

- [ ] **Step 1: Write failing tests — Layer 1: command detection**

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

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_guardrail.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation — Layer 1**

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

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_guardrail.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add src/harness/guardrail.py tests/test_guardrail.py
git commit -m "feat(guardrail): layer 1 command detection"
```

- [ ] **Step 6: Write failing tests — Layer 3: scope fence**

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

- [ ] **Step 7: Run test to verify it fails**

Run: `pytest tests/test_guardrail.py::test_scope_fence_blocks_outside_directory -v`
Expected: FAIL with `ImportError: cannot import name 'check_scope'`

- [ ] **Step 8: Write minimal implementation — Layer 3**

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

- [ ] **Step 9: Run test to verify it passes**

Run: `pytest tests/test_guardrail.py -v`
Expected: PASS (11 tests)

- [ ] **Step 10: Commit**

```bash
git add src/harness/guardrail.py tests/test_guardrail.py
git commit -m "feat(guardrail): layer 3 scope fence"
```

- [ ] **Step 11: Write failing tests — Layer 2: HITL state machine**

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

- [ ] **Step 12: Run test to verify it fails**

Run: `pytest tests/test_guardrail.py::test_hitl_state_starts_pending -v`
Expected: FAIL with `ImportError`

- [ ] **Step 13: Write minimal implementation — Layer 2**

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

- [ ] **Step 14: Run test to verify it passes**

Run: `pytest tests/test_guardrail.py -v`
Expected: PASS (16 tests)

- [ ] **Step 15: Commit**

```bash
git add src/harness/guardrail.py tests/test_guardrail.py
git commit -m "feat(guardrail): layer 2 HITL state machine"
```

---

### Task 6: Feedback Parser

**Files:**
- Create: `src/harness/feedback.py`
- Test: `tests/test_feedback.py`

**Interfaces:**
- Consumes: `ToolResult`, `Signal` from Task 1
- Produces: `Feedback` class with `parse(result: ToolResult) -> Signal`, `format(signal: Signal) -> str`

- [ ] **Step 1: Write the failing test**

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

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_feedback.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

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

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_feedback.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add src/harness/feedback.py tests/test_feedback.py
git commit -m "feat(feedback): add result parser and signal formatter"
```

---

### Task 7: Memory

**Files:**
- Create: `src/harness/memory.py`
- Test: `tests/test_memory.py`

**Interfaces:**
- Produces: `Memory(file_path: str)` with `store(key, value)`, `recall(key) -> str|None`, `summarize() -> str`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_memory.py
import json
from harness.memory import Memory

def test_store_and_recall(tmp_path):
    mem = Memory(str(tmp_path / "memory.json"))
    mem.store("test_framework", "pytest")
    assert mem.recall("test_framework") == "pytest"

def test_recall_missing_key_returns_none(tmp_path):
    mem = Memory(str(tmp_path / "memory.json"))
    assert mem.recall("nonexistent") is None

def test_store_creates_file_if_missing(tmp_path):
    path = tmp_path / "memory.json"
    mem = Memory(str(path))
    mem.store("k", "v")
    assert path.exists()

def test_summarize_includes_all_keys(tmp_path):
    mem = Memory(str(tmp_path / "memory.json"))
    mem.store("lang", "Python")
    mem.store("test", "pytest")
    summary = mem.summarize()
    assert "lang" in summary
    assert "Python" in summary
    assert "test" in summary
    assert "pytest" in summary

def test_corrupt_file_backed_up_and_rebuilt(tmp_path):
    path = tmp_path / "memory.json"
    path.write_text("NOT VALID JSON{{{")
    mem = Memory(str(path))
    mem.store("new", "value")
    assert mem.recall("new") == "value"
    assert (tmp_path / "memory.json.bak").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_memory.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/harness/memory.py
import json
import os
from pathlib import Path

class Memory:
    def __init__(self, file_path: str):
        self._path = Path(file_path).expanduser()
        self._data = self._load()

    def _load(self) -> dict:
        if not self._path.exists():
            return {}
        try:
            with open(self._path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            backup = self._path.with_suffix(self._path.suffix + ".bak")
            self._path.rename(backup)
            return {}

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def store(self, key: str, value: str):
        self._data[key] = value
        self._save()

    def recall(self, key: str) -> str | None:
        return self._data.get(key)

    def summarize(self) -> str:
        if not self._data:
            return ""
        lines = [f"- {k}: {v}" for k, v in self._data.items()]
        return "Project memory:\n" + "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_memory.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add src/harness/memory.py tests/test_memory.py
git commit -m "feat(memory): add JSON-backed key-value memory"
```

---

### Task 8: ToolRegistry

**Files:**
- Create: `src/harness/tools.py`
- Test: `tests/test_tools.py`

**Interfaces:**
- Consumes: `Action`, `ToolResult` from Task 1
- Produces: `ToolRegistry` with `register(name, fn)`, `execute(action: Action) -> ToolResult`, `list_tools() -> list[str]`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_tools.py
from harness.models import Action, ToolResult
from harness.tools import ToolRegistry

def test_register_and_execute_read(tmp_path):
    reg = ToolRegistry()
    f = tmp_path / "hello.txt"
    f.write_text("hello world")
    reg.register("read", lambda args: ToolResult(stdout=f.read_text(), stderr="", exit_code=0))
    result = reg.execute(Action(name="read", args={"file_path": str(f)}))
    assert result.exit_code == 0
    assert "hello world" in result.stdout

def test_unknown_tool_returns_error():
    reg = ToolRegistry()
    result = reg.execute(Action(name="nonexistent", args={}))
    assert result.exit_code == -1
    assert "unknown tool" in result.stderr

def test_list_tools():
    reg = ToolRegistry()
    reg.register("read", lambda args: ToolResult(stdout="", stderr="", exit_code=0))
    reg.register("write", lambda args: ToolResult(stdout="", stderr="", exit_code=0))
    tools = reg.list_tools()
    assert "read" in tools
    assert "write" in tools

def test_bash_tool_executes_command(tmp_path):
    import subprocess
    reg = ToolRegistry()
    def bash(args):
        r = subprocess.run(args["command"], shell=True, capture_output=True, text=True, cwd=str(tmp_path))
        return ToolResult(stdout=r.stdout, stderr=r.stderr, exit_code=r.returncode)
    reg.register("bash", bash)
    result = reg.execute(Action(name="bash", args={"command": "echo hi"}))
    assert result.exit_code == 0
    assert "hi" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tools.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/harness/tools.py
import subprocess
import glob as globmod
import re
from pathlib import Path
from .models import Action, ToolResult

class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name: str, fn):
        self._tools[name] = fn

    def execute(self, action: Action) -> ToolResult:
        fn = self._tools.get(action.name)
        if fn is None:
            return ToolResult(stdout="", stderr=f"unknown tool: {action.name}", exit_code=-1)
        try:
            return fn(action.args)
        except Exception as e:
            return ToolResult(stdout="", stderr=str(e), exit_code=1)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

def make_default_registry() -> ToolRegistry:
    reg = ToolRegistry()

    def read_file(args):
        path = args["file_path"]
        try:
            return ToolResult(stdout=Path(path).read_text(), stderr="", exit_code=0)
        except Exception as e:
            return ToolResult(stdout="", stderr=str(e), exit_code=1)

    def write_file(args):
        path = args["file_path"]
        try:
            Path(path).write_text(args["content"])
            return ToolResult(stdout=f"wrote {path}", stderr="", exit_code=0)
        except Exception as e:
            return ToolResult(stdout="", stderr=str(e), exit_code=1)

    def bash(args):
        r = subprocess.run(args["command"], shell=True, capture_output=True, text=True)
        return ToolResult(stdout=r.stdout, stderr=r.stderr, exit_code=r.returncode)

    def glob_files(args):
        matches = globmod.glob(args["pattern"], recursive=True)
        return ToolResult(stdout="\n".join(matches), stderr="", exit_code=0)

    def grep_files(args):
        pattern = args["pattern"]
        path = args.get("path", ".")
        matches = []
        for p in Path(path).rglob("*"):
            if p.is_file():
                try:
                    for i, line in enumerate(p.read_text(errors="ignore").splitlines(), 1):
                        if re.search(pattern, line):
                            matches.append(f"{p}:{i}:{line}")
                except Exception:
                    pass
        return ToolResult(stdout="\n".join(matches), stderr="", exit_code=0)

    reg.register("read", read_file)
    reg.register("write", write_file)
    reg.register("bash", bash)
    reg.register("glob", glob_files)
    reg.register("grep", grep_files)
    return reg
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_tools.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/harness/tools.py tests/test_tools.py
git commit -m "feat(tools): add ToolRegistry with 5 preset tools"
```

---

### Task 9: Action Parser

**Files:**
- Create: `src/harness/parser.py`
- Test: `tests/test_parser.py`

**Interfaces:**
- Produces: `parse_actions(text: str) -> list[Action]` — parses `<action name="X" args='{"k":"v"}' />` tags

- [ ] **Step 1: Write the failing test**

```python
# tests/test_parser.py
from harness.parser import parse_actions
from harness.models import Action

def test_parse_single_action():
    text = '<action name="bash" args=\'{"command": "ls"}\' />'
    actions = parse_actions(text)
    assert len(actions) == 1
    assert actions[0].name == "bash"
    assert actions[0].args["command"] == "ls"

def test_parse_multiple_actions():
    text = '<action name="read" args=\'{"file_path": "a.py"}\' />\n<action name="bash" args=\'{"command": "pytest"}\' />'
    actions = parse_actions(text)
    assert len(actions) == 2
    assert actions[0].name == "read"
    assert actions[1].name == "bash"

def test_parse_no_actions_returns_empty():
    actions = parse_actions("just plain text, no actions")
    assert actions == []

def test_parse_malformed_returns_empty():
    actions = parse_actions('<action name="bash" args={bad json} />')
    assert actions == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_parser.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/harness/parser.py
import re
import json
from .models import Action

_ACTION_RE = re.compile(r'<action\s+name="([^"]+)"\s+args=\'([^\']*)\'\s*/>')

def parse_actions(text: str) -> list[Action]:
    actions = []
    for m in _ACTION_RE.finditer(text):
        name = m.group(1)
        try:
            args = json.loads(m.group(2))
        except json.JSONDecodeError:
            continue
        actions.append(Action(name=name, args=args))
    return actions
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_parser.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/harness/parser.py tests/test_parser.py
git commit -m "feat(parser): add LLM output action parser"
```

---

### Task 10: Agent Loop

**Files:**
- Create: `src/harness/agent_loop.py`
- Test: `tests/test_agent_loop.py`

**Interfaces:**
- Consumes: `LLM` (Task 2), `ToolRegistry` (Task 8), `Config` (Task 3), `guardrail`/`HitlState`/`check_scope` (Task 5), `Feedback` (Task 6), `Memory` (Task 7), `parse_actions` (Task 9)
- Produces: `AgentLoop` class with `run(user_input: str) -> str`

- [ ] **Step 1: Write failing test — basic loop with MockLLM**

```python
# tests/test_agent_loop.py
from harness.models import Message
from harness.llm import MockLLM
from harness.config import Config
from harness.tools import make_default_registry
from harness.memory import Memory
from harness.feedback import Feedback
from harness.agent_loop import AgentLoop

def test_loop_returns_final_answer(tmp_path):
    llm = MockLLM(responses=["<FINAL_ANSWER>done</FINAL_ANSWER>"])
    cfg = Config(allowed_directories=[str(tmp_path)])
    reg = make_default_registry()
    mem = Memory(str(tmp_path / "memory.json"))
    loop = AgentLoop(llm=llm, registry=reg, config=cfg, memory=mem, feedback=Feedback())
    result = loop.run("hello")
    assert "done" in result

def test_loop_executes_tool_then_answers(tmp_path):
    (tmp_path / "test.txt").write_text("file content")
    llm = MockLLM(responses=[
        '<action name="read" args=\'{"file_path": "' + str(tmp_path / "test.txt").replace("\\", "\\\\") + '"}\' />',
        "<FINAL_ANSWER>read the file</FINAL_ANSWER>",
    ])
    cfg = Config(allowed_directories=[str(tmp_path)])
    reg = make_default_registry()
    mem = Memory(str(tmp_path / "memory.json"))
    loop = AgentLoop(llm=llm, registry=reg, config=cfg, memory=mem, feedback=Feedback())
    result = loop.run("read the file")
    assert "read the file" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_agent_loop.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/harness/agent_loop.py
import re
from .models import Message, Action
from .llm import LLM
from .tools import ToolRegistry
from .config import Config
from .guardrail import guardrail, check_scope, HitlState
from .feedback import Feedback
from .memory import Memory
from .parser import parse_actions

FINAL_ANSWER_RE = re.compile(r"<FINAL_ANSWER>(.*?)</FINAL_ANSWER>", re.DOTALL)

class AgentLoop:
    def __init__(self, llm: LLM, registry: ToolRegistry, config: Config, memory: Memory, feedback: Feedback, hitl_input=None):
        self._llm = llm
        self._registry = registry
        self._config = config
        self._memory = memory
        self._feedback = feedback
        self._hitl_input = hitl_input or (lambda prompt: input(prompt))
        self._messages = []

    def run(self, user_input: str) -> str:
        system = self._build_system_prompt()
        self._messages = [Message(role="system", content=system)]
        self._messages.append(Message(role="user", content=user_input))
        for step in range(20):
            response = self._llm.ask(self._messages)
            self._messages.append(Message(role="assistant", content=response))
            final = FINAL_ANSWER_RE.search(response)
            if final:
                return final.group(1).strip()
            actions = parse_actions(response)
            if not actions:
                return response
            for action in actions:
                result = self._execute_with_guardrail(action)
                signal = self._feedback.parse(result)
                feedback_text = self._feedback.format(signal)
                self._messages.append(Message(role="tool", content=feedback_text))
        return "Reached max tool calls (20)."

    def _build_system_prompt(self) -> str:
        parts = ["You are a coding agent. Use <action> tags to call tools."]
        parts.append(f"Available tools: {', '.join(self._registry.list_tools())}")
        mem_summary = self._memory.summarize()
        if mem_summary:
            parts.append(mem_summary)
        parts.append("End with <FINAL_ANSWER>your answer</FINAL_ANSWER>.")
        return "\n\n".join(parts)

    def _execute_with_guardrail(self, action: Action):
        gr = guardrail(action, self._config)
        if gr.decision == "BLOCK":
            from .models import ToolResult
            return ToolResult(stdout="", stderr=f"BLOCKED: {gr.reason}", exit_code=-1)
        if gr.decision == "HITL_PENDING":
            state = HitlState()
            print(f"[HITL] Action needs approval: {action.name} {action.args}")
            print(f"  Reason: {gr.reason}")
            answer = self._hitl_input("Approve? [y/N]: ")
            if answer.strip().lower() == "y":
                state.approve()
            else:
                state.reject()
                from .models import ToolResult
                return ToolResult(stdout="", stderr=f"REJECTED by user: {gr.reason}", exit_code=-1)
        sr = check_scope(action, self._config)
        if sr.decision == "BLOCK":
            from .models import ToolResult
            return ToolResult(stdout="", stderr=f"SCOPE BLOCKED: {sr.reason}", exit_code=-1)
        return self._registry.execute(action)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_agent_loop.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/harness/agent_loop.py tests/test_agent_loop.py
git commit -m "feat(agent-loop): add main loop with guardrail integration"
```

---

### Task 11: CLI Entry Point

**Files:**
- Create: `src/harness/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `AgentLoop` (Task 10), `CredentialManager` (Task 4), `load_config` (Task 3), `DeepSeekLLM` (Task 2)

- [ ] **Step 1: Write failing test — CLI smoke test**

```python
# tests/test_cli.py
import subprocess
import sys

def test_cli_help_runs():
    result = subprocess.run([sys.executable, "-m", "harness", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "harness" in result.stdout.lower() or "usage" in result.stdout.lower()

def test_cli_config_subcommand():
    result = subprocess.run([sys.executable, "-m", "harness", "config", "show-key"], capture_output=True, text=True)
    assert result.returncode == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# src/harness/cli.py
import argparse
import sys
from .config import load_config
from .credentials import CredentialManager
from .llm import DeepSeekLLM, MockLLM
from .tools import make_default_registry
from .memory import Memory
from .feedback import Feedback
from .agent_loop import AgentLoop
from pathlib import Path

DEFAULT_CONFIG_PATH = str(Path.home() / ".harness" / "config.yaml")

def main():
    parser = argparse.ArgumentParser(prog="harness", description="Coding Agent Harness")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("config", help="Configuration")
    config_sub = sub.add_parser("config")
    config_sub_sub = config_sub.add_subparsers(dest="config_command")
    config_sub_sub.add_parser("show-key")
    config_sub_sub.add_parser("set-key")
    config_sub_sub.add_parser("clear-key")
    parser.add_argument("--mock", action="store_true", help="Use MockLLM")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()

    if args.command == "config":
        cm = CredentialManager()
        if args.config_command == "show-key":
            print("API key: configured" if cm.has_key() else "API key: not configured")
        elif args.config_command == "set-key":
            import getpass
            key = getpass.getpass("Enter API key: ")
            cm.set_key(key)
            print("API key stored.")
        elif args.config_command == "clear-key":
            cm.clear_key()
            print("API key cleared.")
        return

    cfg = load_config(args.config)
    cm = CredentialManager(api_key_env=cfg.api_key_env)
    if args.mock:
        llm = MockLLM(responses=["<FINAL_ANSWER>mock mode</FINAL_ANSWER>"])
    else:
        key = cm.get_key()
        if not key:
            print("No API key found. Run: harness config set-key")
            sys.exit(1)
        llm = DeepSeekLLM(api_key=key, model=cfg.llm_model)

    reg = make_default_registry()
    mem = Memory(cfg.memory_file)
    loop = AgentLoop(llm=llm, registry=reg, config=cfg, memory=mem, feedback=Feedback())

    print("harness> type 'exit' to quit")
    while True:
        try:
            user_input = input("harness> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if user_input.strip().lower() in ("exit", "quit"):
            break
        result = loop.run(user_input)
        print(result)

if __name__ == "__main__":
    main()
```

Also add `__main__.py`:

```python
# src/harness/__main__.py
from .cli import main
main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/harness/cli.py src/harness/__main__.py tests/test_cli.py
git commit -m "feat(cli): add REPL entry point and config subcommands"
```

---

### Task 12: Mechanism Demonstration (§A.6)

**Files:**
- Create: `demo/run_demo.py`
- Test: `tests/test_demo.py`

**Interfaces:**
- Consumes: all modules

- [ ] **Step 1: Write failing test — 3 demo scenarios**

```python
# tests/test_demo.py
from harness.models import Action
from harness.llm import MockLLM
from harness.config import Config
from harness.tools import make_default_registry
from harness.memory import Memory
from harness.feedback import Feedback
from harness.agent_loop import AgentLoop
from harness.guardrail import guardrail, HitlState

def test_demo_1_guardrail_blocks_dangerous_action():
    """Scenario 1: guardrail intercepts a dangerous action."""
    cfg = Config()
    action = Action(name="bash", args={"command": "rm -rf /"})
    result = guardrail(action, cfg)
    assert result.decision == "BLOCK"
    print(f"\n[Demo 1] Action: rm -rf / -> {result.decision}: {result.reason}")

def test_demo_2_feedback_drives_self_correction(tmp_path):
    """Scenario 2: feedback loop causes agent to change next action."""
    (tmp_path / "target.txt").write_text("hello")
    llm = MockLLM(responses=[
        '<action name="bash" args=\'{"command": "cat nonexistent.txt"}\' />',
        '<action name="read" args=\'{"file_path": "' + str(tmp_path / "target.txt").replace("\\", "\\\\") + '"}\' />',
        "<FINAL_ANSWER>found the file</FINAL_ANSWER>",
    ])
    cfg = Config(allowed_directories=[str(tmp_path)])
    reg = make_default_registry()
    mem = Memory(str(tmp_path / "memory.json"))
    loop = AgentLoop(llm=llm, registry=reg, config=cfg, memory=mem, feedback=Feedback())
    result = loop.run("read the target file")
    assert "found the file" in result
    print(f"\n[Demo 2] Agent failed first, got feedback, succeeded second: {result}")

def test_demo_3_hitl_state_machine():
    """Scenario 3: HITL state machine — deep focus dimension."""
    state = HitlState()
    assert state.current == "PENDING"
    state.approve()
    assert state.current == "APPROVED"
    print(f"\n[Demo 3] HITL state: PENDING -> APPROVED")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_demo.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the standalone demo script**

```python
# demo/run_demo.py
"""Mechanism demonstration for §A.6 — run with: python demo/run_demo.py"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from harness.models import Action
from harness.config import Config
from harness.guardrail import guardrail, HitlState
from harness.llm import MockLLM
from harness.tools import make_default_registry
from harness.memory import Memory
from harness.feedback import Feedback
from harness.agent_loop import AgentLoop
import tempfile
from pathlib import Path

def demo_1():
    print("=== Demo 1: Guardrail blocks dangerous action ===")
    cfg = Config()
    action = Action(name="bash", args={"command": "rm -rf /"})
    result = guardrail(action, cfg)
    print(f"Action: {action.args['command']}")
    print(f"Decision: {result.decision}")
    print(f"Reason: {result.reason}")
    assert result.decision == "BLOCK"
    print("PASS: dangerous action blocked\n")

def demo_2():
    print("=== Demo 2: Feedback loop drives self-correction ===")
    with tempfile.TemporaryDirectory() as td:
        Path(td, "target.txt").write_text("hello")
        llm = MockLLM(responses=[
            '<action name="bash" args=\'{"command": "cat nonexistent.txt"}\' />',
            '<action name="read" args=\'{"file_path": "' + str(Path(td, "target.txt")).replace("\\", "\\\\") + '"}\' />',
            "<FINAL_ANSWER>found the file</FINAL_ANSWER>",
        ])
        cfg = Config(allowed_directories=[td])
        reg = make_default_registry()
        mem = Memory(str(Path(td, "memory.json")))
        loop = AgentLoop(llm=llm, registry=reg, config=cfg, memory=mem, feedback=Feedback())
        result = loop.run("read the target file")
        print(f"Final answer: {result}")
        assert "found the file" in result
        print("PASS: agent self-corrected after feedback\n")

def demo_3():
    print("=== Demo 3: HITL state machine (deep focus) ===")
    state = HitlState()
    print(f"Initial state: {state.current}")
    state.approve()
    print(f"After approve(): {state.current}")
    assert state.current == "APPROVED"
    print("PASS: HITL state transition correct\n")

if __name__ == "__main__":
    demo_1()
    demo_2()
    demo_3()
    print("All demos passed.")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_demo.py -v`
Expected: PASS (3 tests)

Also verify standalone:
Run: `python demo/run_demo.py`
Expected: prints 3 demo sections, ends with "All demos passed."

- [ ] **Step 5: Commit**

```bash
git add demo/run_demo.py tests/test_demo.py
git commit -m "feat(demo): add §A.6 mechanism demonstration (3 scenarios)"
```

---

### Task 13: Packaging, CI, README

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `README.md`
- Create: `.github/workflows/ci.yml`
- Modify: `src/harness/__init__.py`

- [ ] **Step 1: Write pyproject.toml**

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "coding-agent-harness"
version = "0.1.0"
description = "A minimal Coding Agent Harness with deep governance focus"
requires-python = ">=3.10"
dependencies = [
    "openai>=1.0",
    "python-dotenv>=1.0",
    "keyring>=24.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0"]

[project.scripts]
harness = "harness.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Write .gitignore**

```
# .gitignore
.env
__pycache__/
*.pyc
dist/
*.egg-info/
.pytest_cache/
~/.harness/
```

- [ ] **Step 3: Write __init__.py**

```python
# src/harness/__init__.py
"""Coding Agent Harness — a minimal harness with deep governance focus."""
__version__ = "0.1.0"
```

- [ ] **Step 4: Write README.md**

````markdown
# Coding Agent Harness

A minimal but complete Coding Agent Harness built from scratch in Python, with a deep focus on **governance** (guardrails / HITL state machine / scope fence).

## Install

```bash
pip install coding-agent-harness
```

## Configure API Key

First-time setup — store your DeepSeek API key securely in the OS keyring:

```bash
harness config set-key
# prompts for key (hidden input), stores in keyring
```

Check if configured (does not reveal the key):

```bash
harness config show-key
```

Remove the key:

```bash
harness config clear-key
```

Alternatively, set `DEEPSEEK_API_KEY` environment variable via a `.env` file (plaintext — see Security below).

## Run

```bash
harness            # start REPL
harness --mock     # mock LLM mode (no API needed, for testing)
```

## Security

- API key is stored in the OS keyring (Windows Credential Manager / macOS Keychain / Linux Secret Service) — never in plaintext config.
- `.env` fallback is plaintext; process environment is visible to other processes on shared hosts. Keyring is recommended.
- Key is never logged, never committed to Git. `.env` is in `.gitignore`.
- Guardrail blocks dangerous commands (`rm -rf /`, `dd`, `format`) and requires approval for risky ones (`rm`, `sudo`).
- Scope fence restricts file operations to configured directories.

## Limitations

- Python 3.10+ required
- Single-process, no parallelism
- LLM action protocol uses `<action>` XML tags
- Max 20 tool calls per user turn

## Development

```bash
git clone <repo>
cd coding-agent-harness
pip install -e ".[dev]"
pytest -v
python demo/run_demo.py
```

## License

MIT
````

- [ ] **Step 5: Write CI config**

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  unit-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - run: pip install -e ".[dev]"
      - run: pytest -v
      - run: python demo/run_demo.py
```

- [ ] **Step 6: Verify full test suite passes**

Run: `pytest -v`
Expected: All tests PASS

Run: `python demo/run_demo.py`
Expected: "All demos passed."

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml .gitignore README.md .github/workflows/ci.yml src/harness/__init__.py
git commit -m "feat(packaging): add pyproject, CI, README, gitignore"
```

---

## Self-Review Notes

**Spec coverage check:**
- ✅ Agent Loop (§3.1) → Task 10
- ✅ LLM abstraction (§3.2) → Task 2
- ✅ ToolRegistry (§3.3) → Task 8
- ✅ Guardrail 3 layers (§3.4) → Task 5 (deep focus, 16 tests)
- ✅ Feedback (§3.5) → Task 6
- ✅ Memory (§3.6) → Task 7
- ✅ Config (§3.7) → Task 3
- ✅ Credentials (§4.2) → Task 4
- ✅ Distribution PyPI (§7.2) → Task 13
- ✅ Mechanism demo (§A.6) → Task 12
- ✅ CI unit-test job (§4.8) → Task 13

**Type consistency check:**
- `Action(name, args)` consistent across Tasks 1, 5, 8, 9, 10, 12 ✓
- `guardrail(action, config) -> GuardrailResult` consistent across Tasks 5, 10, 12 ✓
- `HitlState.approve()/reject()` consistent across Tasks 5, 10, 12 ✓
- `check_scope(action, config) -> GuardrailResult` consistent across Tasks 5, 10 ✓
- `AgentLoop(llm, registry, config, memory, feedback)` consistent across Tasks 10, 11, 12 ✓
