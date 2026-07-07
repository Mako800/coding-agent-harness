# Task 8: ToolRegistry

**Files:**
- Create: `src/harness/tools.py`
- Test: `tests/test_tools.py`

**Interfaces:**
- Consumes: `Action`, `ToolResult` from Task 1
- Produces: `ToolRegistry` with `register(name, fn)`, `execute(action: Action) -> ToolResult`, `list_tools() -> list[str]`, `make_default_registry() -> ToolRegistry`

## Step 1: Write the failing test

```python
# tests/test_tools.py
from harness.models import Action, ToolResult
from harness.tools import ToolRegistry

def test_register_and_execute_read(tmp_path):
    reg = ToolRegistry()
    f = tmp_path / "hello.txt"
    f.write_text("hello world")
    reg.register("read", lambda args: ToolResult(stdout=f.read_text(), stderr="", exit_code=0))
    result = reg.execute(Action(name="read", args={"file_path": str(f)}))
    assert result.exit_code == 0
    assert "hello world" in result.stdout

def test_unknown_tool_returns_error():
    reg = ToolRegistry()
    result = reg.execute(Action(name="nonexistent", args={}))
    assert result.exit_code == -1
    assert "unknown tool" in result.stderr

def test_list_tools():
    reg = ToolRegistry()
    reg.register("read", lambda args: ToolResult(stdout="", stderr="", exit_code=0))
    reg.register("write", lambda args: ToolResult(stdout="", stderr="", exit_code=0))
    tools = reg.list_tools()
    assert "read" in tools
    assert "write" in tools

def test_bash_tool_executes_command(tmp_path):
    import subprocess
    reg = ToolRegistry()
    def bash(args):
        r = subprocess.run(args["command"], shell=True, capture_output=True, text=True, cwd=str(tmp_path))
        return ToolResult(stdout=r.stdout, stderr=r.stderr, exit_code=r.returncode)
    reg.register("bash", bash)
    result = reg.execute(Action(name="bash", args={"command": "echo hi"}))
    assert result.exit_code == 0
    assert "hi" in result.stdout
```

## Step 2: Run test to verify it fails

Run: `pytest tests/test_tools.py -v`
Expected: FAIL with `ModuleNotFoundError`

## Step 3: Write minimal implementation

```python
# src/harness/tools.py
import subprocess
import glob as globmod
import re
from pathlib import Path
from .models import Action, ToolResult

class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name: str, fn):
        self._tools[name] = fn

    def execute(self, action: Action) -> ToolResult:
        fn = self._tools.get(action.name)
        if fn is None:
            return ToolResult(stdout="", stderr=f"unknown tool: {action.name}", exit_code=-1)
        try:
            return fn(action.args)
        except Exception as e:
            return ToolResult(stdout="", stderr=str(e), exit_code=1)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

def make_default_registry() -> ToolRegistry:
    reg = ToolRegistry()

    def read_file(args):
        path = args["file_path"]
        try:
            return ToolResult(stdout=Path(path).read_text(), stderr="", exit_code=0)
        except Exception as e:
            return ToolResult(stdout="", stderr=str(e), exit_code=1)

    def write_file(args):
        path = args["file_path"]
        try:
            Path(path).write_text(args["content"])
            return ToolResult(stdout=f"wrote {path}", stderr="", exit_code=0)
        except Exception as e:
            return ToolResult(stdout="", stderr=str(e), exit_code=1)

    def bash(args):
        r = subprocess.run(args["command"], shell=True, capture_output=True, text=True)
        return ToolResult(stdout=r.stdout, stderr=r.stderr, exit_code=r.returncode)

    def glob_files(args):
        matches = globmod.glob(args["pattern"], recursive=True)
        return ToolResult(stdout="\n".join(matches), stderr="", exit_code=0)

    def grep_files(args):
        pattern = args["pattern"]
        path = args.get("path", ".")
        matches = []
        for p in Path(path).rglob("*"):
            if p.is_file():
                try:
                    for i, line in enumerate(p.read_text(errors="ignore").splitlines(), 1):
                        if re.search(pattern, line):
                            matches.append(f"{p}:{i}:{line}")
                except Exception:
                    pass
        return ToolResult(stdout="\n".join(matches), stderr="", exit_code=0)

    reg.register("read", read_file)
    reg.register("write", write_file)
    reg.register("bash", bash)
    reg.register("glob", glob_files)
    reg.register("grep", grep_files)
    return reg
```

## Step 4: Run test to verify it passes

Run: `pytest tests/test_tools.py -v`
Expected: PASS (4 tests)

## Step 5: Commit

```bash
git add src/harness/tools.py tests/test_tools.py
git commit -m "feat(tools): add ToolRegistry with 5 preset tools"
```
