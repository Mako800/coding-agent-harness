# Task 7: Memory

**Files:**
- Create: `src/harness/memory.py`
- Test: `tests/test_memory.py`

**Interfaces:**
- Produces: `Memory(file_path: str)` with `store(key, value)`, `recall(key) -> str|None`, `summarize() -> str`

## Step 1: Write the failing test

```python
# tests/test_memory.py
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
```

## Step 2: Run test to verify it fails

Run: `pytest tests/test_memory.py -v`
Expected: FAIL with `ModuleNotFoundError`

## Step 3: Write minimal implementation

```python
# src/harness/memory.py
import json
import os
from pathlib import Path

class Memory:
    def __init__(self, file_path: str):
        self._path = Path(file_path).expanduser()
        self._data = self._load()

    def _load(self) -> dict:
        if not self._path.exists():
            return {}
        try:
            with open(self._path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            backup = self._path.with_suffix(self._path.suffix + ".bak")
            self._path.rename(backup)
            return {}

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def store(self, key: str, value: str):
        self._data[key] = value
        self._save()

    def recall(self, key: str) -> str | None:
        return self._data.get(key)

    def summarize(self) -> str:
        if not self._data:
            return ""
        lines = [f"- {k}: {v}" for k, v in self._data.items()]
        return "Project memory:\n" + "\n".join(lines)
```

## Step 4: Run test to verify it passes

Run: `pytest tests/test_memory.py -v`
Expected: PASS (5 tests)

## Step 5: Commit

```bash
git add src/harness/memory.py tests/test_memory.py
git commit -m "feat(memory): add JSON-backed key-value memory"
```
