from flask import Flask, request, jsonify, render_template
from .config import load_config
from .credentials import CredentialManager
from .llm import DeepSeekLLM, MockLLM
from .tools import make_default_registry
from .memory import Memory
from .feedback import Feedback
from .agent_loop import AgentLoop
from .models import Action
from .guardrail import guardrail, check_scope
from pathlib import Path
import os

DEFAULT_CONFIG_PATH = str(Path.home() / ".harness" / "config.yaml")

def create_app(config_path=DEFAULT_CONFIG_PATH, mock=None):
    if mock is None:
        mock = os.environ.get("HARNESS_MOCK", "0") == "1"

    template_dir = os.path.join(os.path.dirname(__file__), "..", "..", "templates")
    if not os.path.exists(template_dir):
        template_dir = os.path.join(os.getcwd(), "templates")
    app = Flask(__name__, template_folder=template_dir)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/guardrail-check", methods=["POST"])
    def guardrail_check():
        data = request.json
        command = data.get("command", "")
        if not command:
            return jsonify({"error": "no command"}), 400
        cfg = load_config(config_path)
        action = Action(name="bash", args={"command": command})
        gr = guardrail(action, cfg)
        sr = check_scope(action, cfg)
        if gr.decision == "BLOCK":
            level = "dangerous"
        elif gr.decision == "HITL_PENDING":
            level = "dangerous"
        elif sr.decision == "BLOCK":
            level = "dangerous"
        else:
            level = "safe"
        return jsonify({
            "command": command,
            "decision": gr.decision,
            "scope": sr.decision,
            "level": level,
            "reason": gr.reason,
        })

    @app.route("/api/chat", methods=["POST"])
    def chat():
        data = request.json
        user_input = data.get("message", "")
        if not user_input:
            return jsonify({"error": "no message"}), 400

        cfg = load_config(config_path)
        steps = []

        if mock:
            llm = MockLLM(responses=[
                '<action name="bash" args=\'{"command": "echo Hello from agent tool"}\'/>',
                '<action name="bash" args=\'{"command": "rm -rf /"}\'/>',
                '<action name="bash" args=\'{"command": "echo corrected after block"}\'/>',
                '<FINAL_ANSWER>Agent loop complete. I executed 3 tool calls: echo (success), rm -rf / (blocked by guardrail), echo (success after self-correction).</FINAL_ANSWER>',
            ])
        else:
            key = os.environ.get(cfg.api_key_env, "")
            if not key:
                try:
                    cm = CredentialManager(api_key_env=cfg.api_key_env)
                    key = cm.get_key()
                except Exception:
                    key = None
            if not key:
                return jsonify({"error": "No API key configured. Set DEEPSEEK_API_KEY env var."}), 500
            llm = DeepSeekLLM(api_key=key, model=cfg.llm_model)

        reg = make_default_registry()
        mem = Memory(cfg.memory_file)
        loop = AgentLoop(
            llm=llm, registry=reg, config=cfg, memory=mem, feedback=Feedback(),
            hitl_input=lambda prompt: "n",
            step_callback=lambda step: steps.append(step),
        )
        result = loop.run(user_input)
        return jsonify({"response": result, "steps": steps})

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok"})

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))
