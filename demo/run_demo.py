"""Mechanism demonstration for §A.6 — run with: python demo/run_demo.py"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from harness.models import Action
from harness.config import Config
from harness.guardrail import guardrail, HitlState
from harness.llm import MockLLM
from harness.tools import make_default_registry
from harness.memory import Memory
from harness.feedback import Feedback
from harness.agent_loop import AgentLoop
import tempfile
from pathlib import Path

def demo_1():
    print("=== Demo 1: Guardrail blocks dangerous action ===")
    cfg = Config()
    action = Action(name="bash", args={"command": "rm -rf /"})
    result = guardrail(action, cfg)
    print(f"Action: {action.args['command']}")
    print(f"Decision: {result.decision}")
    print(f"Reason: {result.reason}")
    assert result.decision == "BLOCK"
    print("PASS: dangerous action blocked\n")

def demo_2():
    print("=== Demo 2: Feedback loop drives self-correction ===")
    with tempfile.TemporaryDirectory() as td:
        Path(td, "target.txt").write_text("hello")
        llm = MockLLM(responses=[
            '<action name="bash" args=\'{"command": "cat nonexistent.txt"}\' />',
            '<action name="read" args=\'{"file_path": "' + str(Path(td, "target.txt")).replace("\\", "\\\\") + '"}\' />',
            "<FINAL_ANSWER>found the file</FINAL_ANSWER>",
        ])
        cfg = Config(allowed_directories=[td])
        reg = make_default_registry()
        mem = Memory(str(Path(td, "memory.json")))
        loop = AgentLoop(llm=llm, registry=reg, config=cfg, memory=mem, feedback=Feedback())
        result = loop.run("read the target file")
        print(f"Final answer: {result}")
        assert "found the file" in result
        print("PASS: agent self-corrected after feedback\n")

def demo_3():
    print("=== Demo 3: HITL state machine (deep focus) ===")
    state = HitlState()
    print(f"Initial state: {state.current}")
    state.approve()
    print(f"After approve(): {state.current}")
    assert state.current == "APPROVED"
    print("PASS: HITL state transition correct\n")

if __name__ == "__main__":
    demo_1()
    demo_2()
    demo_3()
    print("All demos passed.")
