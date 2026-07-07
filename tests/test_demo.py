from harness.models import Action
from harness.llm import MockLLM
from harness.config import Config
from harness.tools import make_default_registry
from harness.memory import Memory
from harness.feedback import Feedback
from harness.agent_loop import AgentLoop
from harness.guardrail import guardrail, HitlState

def test_demo_1_guardrail_blocks_dangerous_action():
    """Scenario 1: guardrail intercepts a dangerous action."""
    cfg = Config()
    action = Action(name="bash", args={"command": "rm -rf /"})
    result = guardrail(action, cfg)
    assert result.decision == "BLOCK"
    print(f"\n[Demo 1] Action: rm -rf / -> {result.decision}: {result.reason}")

def test_demo_2_feedback_drives_self_correction(tmp_path):
    """Scenario 2: feedback loop causes agent to change next action."""
    (tmp_path / "target.txt").write_text("hello")
    llm = MockLLM(responses=[
        '<action name="bash" args=\'{"command": "cat nonexistent.txt"}\' />',
        '<action name="read" args=\'{"file_path": "' + str(tmp_path / "target.txt").replace("\\", "\\\\") + '"}\' />',
        "<FINAL_ANSWER>found the file</FINAL_ANSWER>",
    ])
    cfg = Config(allowed_directories=[str(tmp_path)])
    reg = make_default_registry()
    mem = Memory(str(tmp_path / "memory.json"))
    loop = AgentLoop(llm=llm, registry=reg, config=cfg, memory=mem, feedback=Feedback())
    result = loop.run("read the target file")
    assert "found the file" in result
    print(f"\n[Demo 2] Agent failed first, got feedback, succeeded second: {result}")

def test_demo_3_hitl_state_machine():
    """Scenario 3: HITL state machine — deep focus dimension."""
    state = HitlState()
    assert state.current == "PENDING"
    state.approve()
    assert state.current == "APPROVED"
    print(f"\n[Demo 3] HITL state: PENDING -> APPROVED")
