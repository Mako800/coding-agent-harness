from dataclasses import dataclass, field


@dataclass
class Config:
    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-chat"
    api_key_env: str = "DEEPSEEK_API_KEY"
    blocked_commands: list = field(default_factory=lambda: ["rm -rf /", "dd if=", "format", "mkfs", ":(){:|:&};:"])
    hitl_commands: list = field(default_factory=lambda: ["rm", "sudo", "DROP TABLE", "ALTER TABLE", "git push --force"])
    allowed_commands: list = field(default_factory=lambda: ["ls", "cat", "echo", "pwd", "pytest", "python", "pip", "git status", "git diff", "git log", "git add", "git commit"])
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
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return Config()
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
    if "allowed_commands" in g: cfg.allowed_commands = g["allowed_commands"]
    if "allowed_directories" in g: cfg.allowed_directories = g["allowed_directories"]
    m = data.get("memory", {})
    if "enabled" in m: cfg.memory_enabled = m["enabled"]
    if "file" in m: cfg.memory_file = m["file"]
    return cfg
