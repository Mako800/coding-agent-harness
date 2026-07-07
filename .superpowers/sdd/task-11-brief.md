# Task 11: CLI Entry Point

**Files:**
- Create: `src/harness/cli.py`
- Create: `src/harness/__main__.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `AgentLoop` (Task 10), `CredentialManager` (Task 4), `load_config` (Task 3), `DeepSeekLLM` (Task 2)

## Step 1: Write failing test — CLI smoke test

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

## Step 2: Run test to verify it fails

Run: `pytest tests/test_cli.py -v`
Expected: FAIL

## Step 3: Write minimal implementation

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
    config_sub = sub.add_parser("config", help="Configuration")
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

Also create:
```python
# src/harness/__main__.py
from .cli import main
main()
```

## Step 4: Run test to verify it passes

Run: `pytest tests/test_cli.py -v`
Expected: PASS (2 tests)

## Step 5: Commit

```bash
git add src/harness/cli.py src/harness/__main__.py tests/test_cli.py
git commit -m "feat(cli): add REPL entry point and config subcommands"
```
