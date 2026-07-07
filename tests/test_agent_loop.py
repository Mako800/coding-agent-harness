from harness.models import Message
from harness.llm import MockLLM
from harness.config import Config
from harness.tools import make_default_registry
from harness.memory import Memory
from harness.feedback import Feedback
from harness.agent_loop import AgentLoop

def test_loop_returns_final_answer(tmp_path):
    llm = MockLLM(responses=["<FINAL_ANSWER>done</FINAL_ANSWER>"])
    cfg = Config(allowed_directories=[str(tmp_path)])
    reg = make_default_registry()
    mem = Memory(str(tmp_path / "memory.json"))
    loop = AgentLoop(llm=llm, registry=reg, config=cfg, memory=mem, feedback=Feedback())
    result = loop.run("hello")
    assert "done" in result

def test_loop_executes_tool_then_answers(tmp_path):
    (tmp_path / "test.txt").write_text("file content")
    llm = MockLLM(responses=[
        '<action name="read" args=\'{"file_path": "' + str(tmp_path / "test.txt").replace("\\", "\\\\") + '"}\' />',
        "<FINAL_ANSWER>read the file</FINAL_ANSWER>",
    ])
    cfg = Config(allowed_directories=[str(tmp_path)])
    reg = make_default_registry()
    mem = Memory(str(tmp_path / "memory.json"))
    loop = AgentLoop(llm=llm, registry=reg, config=cfg, memory=mem, feedback=Feedback())
    result = loop.run("read the file")
    assert "read the file" in result
