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
