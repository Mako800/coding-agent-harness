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
