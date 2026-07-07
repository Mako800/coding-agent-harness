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
