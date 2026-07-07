import os
import subprocess
import sys

_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "src"))


def _env():
    return {**os.environ, "PYTHONPATH": _SRC + os.pathsep + os.environ.get("PYTHONPATH", "")}


def test_cli_help_runs():
    result = subprocess.run([sys.executable, "-m", "harness", "--help"], capture_output=True, text=True, env=_env())
    assert result.returncode == 0
    assert "harness" in result.stdout.lower() or "usage" in result.stdout.lower()


def test_cli_config_subcommand():
    result = subprocess.run([sys.executable, "-m", "harness", "config", "show-key"], capture_output=True, text=True, env=_env())
    assert result.returncode == 0
