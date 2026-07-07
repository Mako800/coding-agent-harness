from .models import ToolResult, Signal


class Feedback:
    def parse(self, result: ToolResult) -> Signal:
        if result.exit_code == 0:
            return Signal(status="SUCCESS", summary=f"exit 0: {result.stdout[:200]}")
        if result.exit_code < 0:
            return Signal(status="ERROR", summary=f"exit {result.exit_code}: {result.stderr[:200]}")
        return Signal(status="FAILURE", summary=f"exit {result.exit_code}: {result.stderr[:200]}")

    def format(self, signal: Signal) -> str:
        return f"[{signal.status}] {signal.summary}"
