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
