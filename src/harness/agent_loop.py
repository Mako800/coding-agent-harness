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
    def __init__(self, llm: LLM, registry: ToolRegistry, config: Config, memory: Memory, feedback: Feedback, hitl_input=None, step_callback=None):
        self._llm = llm
        self._registry = registry
        self._config = config
        self._memory = memory
        self._feedback = feedback
        self._hitl_input = hitl_input or (lambda prompt: input(prompt))
        self._step_callback = step_callback or (lambda step: None)
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
                answer = final.group(1).strip()
                self._step_callback({"type": "final_answer", "content": answer})
                return answer
            actions = parse_actions(response)
            if not actions:
                self._step_callback({"type": "response", "content": response})
                return response
            self._step_callback({"type": "llm_response", "content": response, "actions": [{"name": a.name, "args": a.args} for a in actions]})
            for action in actions:
                result, gr_decision, gr_reason = self._execute_with_guardrail(action)
                signal = self._feedback.parse(result)
                feedback_text = self._feedback.format(signal)
                self._messages.append(Message(role="tool", content=feedback_text))
                self._step_callback({
                    "type": "tool_result",
                    "action": {"name": action.name, "args": action.args},
                    "guardrail": {"decision": gr_decision, "reason": gr_reason},
                    "result": {"stdout": result.stdout[:500], "stderr": result.stderr[:500], "exit_code": result.exit_code},
                    "signal": {"status": signal.status, "summary": signal.summary},
                })
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
            return ToolResult(stdout="", stderr=f"BLOCKED: {gr.reason}", exit_code=-1), gr.decision, gr.reason
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
                return ToolResult(stdout="", stderr=f"REJECTED by user: {gr.reason}", exit_code=-1), gr.decision, gr.reason
        sr = check_scope(action, self._config)
        if sr.decision == "BLOCK":
            from .models import ToolResult
            return ToolResult(stdout="", stderr=f"SCOPE BLOCKED: {sr.reason}", exit_code=-1), sr.decision, sr.reason
        return self._registry.execute(action), gr.decision, gr.reason
