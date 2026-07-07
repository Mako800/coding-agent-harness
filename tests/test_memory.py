import json
from harness.memory import Memory

def test_store_and_recall(tmp_path):
    mem = Memory(str(tmp_path / "memory.json"))
    mem.store("test_framework", "pytest")
    assert mem.recall("test_framework") == "pytest"

def test_recall_missing_key_returns_none(tmp_path):
    mem = Memory(str(tmp_path / "memory.json"))
    assert mem.recall("nonexistent") is None

def test_store_creates_file_if_missing(tmp_path):
    path = tmp_path / "memory.json"
    mem = Memory(str(path))
    mem.store("k", "v")
    assert path.exists()

def test_summarize_includes_all_keys(tmp_path):
    mem = Memory(str(tmp_path / "memory.json"))
    mem.store("lang", "Python")
    mem.store("test", "pytest")
    summary = mem.summarize()
    assert "lang" in summary
    assert "Python" in summary
    assert "test" in summary
    assert "pytest" in summary

def test_corrupt_file_backed_up_and_rebuilt(tmp_path):
    path = tmp_path / "memory.json"
    path.write_text("NOT VALID JSON{{{")
    mem = Memory(str(path))
    mem.store("new", "value")
    assert mem.recall("new") == "value"
    assert (tmp_path / "memory.json.bak").exists()
