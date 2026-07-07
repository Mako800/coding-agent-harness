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
