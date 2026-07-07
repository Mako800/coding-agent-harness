---
title: Coding Agent Harness
emoji: 🛡️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

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

## Directory Structure

```
coding-agent-harness/
├── src/harness/
│   ├── __init__.py          # Package metadata
│   ├── __main__.py          # python -m harness entry
│   ├── models.py            # Dataclasses: Message, Action, ToolResult, GuardrailResult, Signal
│   ├── llm.py               # LLM abstract base, MockLLM, DeepSeekLLM
│   ├── tools.py             # ToolRegistry + 5 preset tools (read/write/bash/glob/grep)
│   ├── guardrail.py         # Governance core: 3 layers (detection/HITL/scope fence) [DEEP FOCUS]
│   ├── feedback.py          # Result parser: ToolResult → Signal
│   ├── memory.py            # JSON-backed cross-session memory
│   ├── config.py            # YAML config loader with defaults
│   ├── credentials.py       # Keyring + env credential manager
│   ├── parser.py            # Parse LLM output into Action objects
│   ├── agent_loop.py        # Main loop: context → LLM → parse → guardrail → execute → feedback
│   ├── cli.py               # CLI REPL + config subcommands
│   └── web.py               # Flask web UI
├── templates/
│   └── index.html           # Chat UI page
├── tests/                   # 66 unit tests (all MockLLM-driven, no network)
├── demo/
│   └── run_demo.py          # §A.6 mechanism demonstration (3 scenarios)
├── pyproject.toml           # Package metadata, deps, entry point
├── .gitlab-ci.yml           # CI config with unit-test job
├── SPEC.md                  # Design document
├── PLAN.md                  # Implementation plan (13 tasks)
├── SPEC_PROCESS.md          # Brainstorming process + cold-start verification
├── AGENT_LOG.md             # Agent work log
└── REFLECTION.md            # Reflection report
```

## Deployment

The WebUI is deployed to [Render](https://render.com) as a free web service:

- **URL**: (see below, deployed at render.com)
- **Platform**: Render free tier
- **Build**: `pip install -e ".[dev]" && gunicorn harness.web:app`
- **Start command**: `gunicorn harness.web:create_app() --factory`
- **CI/CD**: GitHub Actions runs tests on every push; Render auto-deploys on push to master
- **Key configuration on target machine**: Set `DEEPSEEK_API_KEY` as an environment variable in Render dashboard

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
