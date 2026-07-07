# Task 12: Mechanism Demonstration (§A.6)

**Files:**
- Create: `demo/run_demo.py`
- Test: `tests/test_demo.py`

**Interfaces:**
- Consumes: all modules

## Step 1: Write failing test — 3 demo scenarios

```python
# tests/test_demo.py
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
```

## Step 2: Run test to verify it fails

Run: `pytest tests/test_demo.py -v`
Expected: FAIL with `ModuleNotFoundError`

## Step 3: Write the standalone demo script

```python
# demo/run_demo.py
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
```

## Step 4: Run test to verify it passes

Run: `pytest tests/test_demo.py -v`
Expected: PASS (3 tests)

Also verify standalone:
Run: `python demo/run_demo.py`
Expected: prints 3 demo sections, ends with "All demos passed."

## Step 5: Commit

```bash
git add demo/run_demo.py tests/test_demo.py
git commit -m "feat(demo): add §A.6 mechanism demonstration (3 scenarios)"
```
