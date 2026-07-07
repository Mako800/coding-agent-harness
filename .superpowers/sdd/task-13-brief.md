# Task 13: Packaging, CI, README

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `README.md`
- Create: `.github/workflows/ci.yml`
- Modify: `src/harness/__init__.py`

## Step 1: Write pyproject.toml

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

## Step 2: Write .gitignore

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

## Step 3: Write __init__.py

```python
# src/harness/__init__.py
"""Coding Agent Harness — a minimal harness with deep governance focus."""
__version__ = "0.1.0"
```

## Step 4: Write README.md

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

## Step 5: Write CI config

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

## Step 6: Verify full test suite passes

Run: `pytest -v`
Expected: All tests PASS

Run: `python demo/run_demo.py`
Expected: "All demos passed."

## Step 7: Commit

```bash
git add pyproject.toml .gitignore README.md .github/workflows/ci.yml src/harness/__init__.py
git commit -m "feat(packaging): add pyproject, CI, README, gitignore"
```
