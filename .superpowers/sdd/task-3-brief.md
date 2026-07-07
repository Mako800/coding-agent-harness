# Task 3: Config Loader

**Files:**
- Create: `src/harness/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `Config` dataclass with fields: `llm_provider`, `llm_model`, `api_key_env`, `blocked_commands`, `hitl_commands`, `allowed_directories`, `memory_enabled`, `memory_file`. `load_config(path: str) -> Config`

## Step 1: Write the failing test

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

## Step 2: Run test to verify it fails

Run: `pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError`

## Step 3: Write minimal implementation

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

## Step 4: Run test to verify it passes

Run: `pytest tests/test_config.py -v`
Expected: PASS (3 tests)

## Step 5: Commit

```bash
git add src/harness/config.py tests/test_config.py
git commit -m "feat(config): add YAML config loader with defaults"
```
