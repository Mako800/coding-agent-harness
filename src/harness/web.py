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
