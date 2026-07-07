# Task: Add WebUI to Coding Agent Harness

**Files:**
- Create: `src/harness/web.py` — Flask web app
- Create: `templates/index.html` — Chat UI
- Create: `tests/test_web.py` — Web UI tests
- Modify: `src/harness/cli.py` — Add `--web` flag
- Modify: `pyproject.toml` — Add flask dependency

## Implementation

### src/harness/web.py

```python
from flask import Flask, request, jsonify, render_template
from .config import load_config
from .credentials import CredentialManager
from .llm import DeepSeekLLM, MockLLM
from .tools import make_default_registry
from .memory import Memory
from .feedback import Feedback
from .agent_loop import AgentLoop
from pathlib import Path
import os

DEFAULT_CONFIG_PATH = str(Path.home() / ".harness" / "config.yaml")

def create_app(config_path=DEFAULT_CONFIG_PATH, mock=False):
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "..", "..", "templates"))
    
    @app.route("/")
    def index():
        return render_template("index.html")
    
    @app.route("/api/chat", methods=["POST"])
    def chat():
        data = request.json
        user_input = data.get("message", "")
        if not user_input:
            return jsonify({"error": "no message"}), 400
        
        cfg = load_config(config_path)
        if mock:
            llm = MockLLM(responses=["<FINAL_ANSWER>mock mode: " + user_input + "</FINAL_ANSWER>"])
        else:
            cm = CredentialManager(api_key_env=cfg.api_key_env)
            key = cm.get_key()
            if not key:
                return jsonify({"error": "No API key configured. Run: harness config set-key"}), 500
            llm = DeepSeekLLM(api_key=key, model=cfg.llm_model)
        
        reg = make_default_registry()
        mem = Memory(cfg.memory_file)
        loop = AgentLoop(llm=llm, registry=reg, config=cfg, memory=mem, feedback=Feedback())
        result = loop.run(user_input)
        return jsonify({"response": result})
    
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok"})
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
```

### templates/index.html

```html
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coding Agent Harness</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .chat { border: 1px solid #ccc; border-radius: 8px; padding: 20px; height: 400px; overflow-y: auto; margin-bottom: 10px; }
        .msg { margin: 8px 0; padding: 8px 12px; border-radius: 4px; }
        .user { background: #e3f2fd; text-align: right; }
        .agent { background: #f5f5f5; }
        .input { display: flex; gap: 10px; }
        .input input { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
        .input button { padding: 10px 20px; background: #1976d2; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .input button:hover { background: #1565c0; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>Coding Agent Harness</h1>
    <p>治理优先的编码智能体 — 危险命令自动拦截，可疑操作人工确认</p>
    <div class="chat" id="chat"></div>
    <div class="input">
        <input id="msg" placeholder="输入消息..." onkeydown="if(event.key==='Enter')send()">
        <button onclick="send()">发送</button>
    </div>
    <script>
        const chat = document.getElementById('chat');
        const msg = document.getElementById('msg');
        async function send() {
            const text = msg.value.trim();
            if (!text) return;
            chat.innerHTML += `<div class="msg user">${text}</div>`;
            msg.value = '';
            chat.innerHTML += `<div class="msg agent" id="loading">思考中...</div>`;
            chat.scrollTop = chat.scrollHeight;
            try {
                const r = await fetch('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:text})});
                const d = await r.json();
                document.getElementById('loading').remove();
                chat.innerHTML += `<div class="msg agent">${d.response||d.error}</div>`;
            } catch(e) {
                document.getElementById('loading').remove();
                chat.innerHTML += `<div class="msg agent">错误: ${e}</div>`;
            }
            chat.scrollTop = chat.scrollHeight;
        }
    </script>
</body>
</html>
```

### tests/test_web.py

```python
import pytest
from harness.web import create_app

def test_health_endpoint():
    app = create_app(mock=True)
    client = app.test_client()
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json["status"] == "ok"

def test_index_page():
    app = create_app(mock=True)
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Coding Agent Harness" in resp.data

def test_chat_mock_mode():
    app = create_app(mock=True)
    client = app.test_client()
    resp = client.post("/api/chat", json={"message": "hello"})
    assert resp.status_code == 200
    assert "mock mode" in resp.json["response"]

def test_chat_empty_message():
    app = create_app(mock=True)
    client = app.test_client()
    resp = client.post("/api/chat", json={"message": ""})
    assert resp.status_code == 400
```
