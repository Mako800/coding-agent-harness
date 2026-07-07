# Task 10: Agent Loop

**Files:**
- Create: `src/harness/agent_loop.py`
- Test: `tests/test_agent_loop.py`

**Interfaces:**
- Consumes: `LLM` (Task 2), `ToolRegistry` (Task 8), `Config` (Task 3), `guardrail`/`HitlState`/`check_scope` (Task 5), `Feedback` (Task 6), `Memory` (Task 7), `parse_actions` (Task 9)
- Produces: `AgentLoop` class with `run(user_input: str) -> str`

## Step 1: Write failing test — basic loop with MockLLM

```python
# tests/test_agent_loop.py
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
```

## Step 2: Run test to verify it fails

Run: `pytest tests/test_agent_loop.py -v`
Expected: FAIL with `ModuleNotFoundError`

## Step 3: Write minimal implementation

```python
# src/harness/agent_loop.py
import re
from .models import Message, Action
from .llm import LLM
from .tools import ToolRegistry
from .config import Config
from .guardrail import guardrail, check_scope, HitlState
from .feedback import Feedback
from .memory import Memory
from .parser import parse_actions

FINAL_ANSWER_RE = re.compile(r"<FINAL_ANSWER>(.*?)</FINAL_ANSWER>", re.DOTALL)

class AgentLoop:
    def __init__(self, llm: LLM, registry: ToolRegistry, config: Config, memory: Memory, feedback: Feedback, hitl_input=None):
        self._llm = llm
        self._registry = registry
        self._config = config
        self._memory = memory
        self._feedback = feedback
        self._hitl_input = hitl_input or (lambda prompt: input(prompt))
        self._messages = []

    def run(self, user_input: str) -> str:
        system = self._build_system_prompt()
        self._messages = [Message(role="system", content=system)]
        self._messages.append(Message(role="user", content=user_input))
        for step in range(20):
            response = self._llm.ask(self._messages)
            self._messages.append(Message(role="assistant", content=response))
            final = FINAL_ANSWER_RE.search(response)
            if final:
                return final.group(1).strip()
            actions = parse_actions(response)
            if not actions:
                return response
            for action in actions:
                result = self._execute_with_guardrail(action)
                signal = self._feedback.parse(result)
                feedback_text = self._feedback.format(signal)
                self._messages.append(Message(role="tool", content=feedback_text))
        return "Reached max tool calls (20)."

    def _build_system_prompt(self) -> str:
        parts = ["You are a coding agent. Use <action> tags to call tools."]
        parts.append(f"Available tools: {', '.join(self._registry.list_tools())}")
        mem_summary = self._memory.summarize()
        if mem_summary:
            parts.append(mem_summary)
        parts.append("End with <FINAL_ANSWER>your answer</FINAL_ANSWER>.")
        return "\n\n".join(parts)

    def _execute_with_guardrail(self, action: Action):
        gr = guardrail(action, self._config)
        if gr.decision == "BLOCK":
            from .models import ToolResult
            return ToolResult(stdout="", stderr=f"BLOCKED: {gr.reason}", exit_code=-1)
        if gr.decision == "HITL_PENDING":
            state = HitlState()
            print(f"[HITL] Action needs approval: {action.name} {action.args}")
            print(f"  Reason: {gr.reason}")
            answer = self._hitl_input("Approve? [y/N]: ")
            if answer.strip().lower() == "y":
                state.approve()
            else:
                state.reject()
                from .models import ToolResult
                return ToolResult(stdout="", stderr=f"REJECTED by user: {gr.reason}", exit_code=-1)
        sr = check_scope(action, self._config)
        if sr.decision == "BLOCK":
            from .models import ToolResult
            return ToolResult(stdout="", stderr=f"SCOPE BLOCKED: {sr.reason}", exit_code=-1)
        return self._registry.execute(action)
```

## Step 4: Run test to verify it passes

Run: `pytest tests/test_agent_loop.py -v`
Expected: PASS (2 tests)

## Step 5: Commit

```bash
git add src/harness/agent_loop.py tests/test_agent_loop.py
git commit -m "feat(agent-loop): add main loop with guardrail integration"
```
