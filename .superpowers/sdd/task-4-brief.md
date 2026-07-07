# Task 4: Credential Manager

**Files:**
- Create: `src/harness/credentials.py`
- Test: `tests/test_credentials.py`

**Interfaces:**
- Consumes: `Config` from Task 3
- Produces: `CredentialManager` with methods `get_key() -> str|None`, `set_key(key: str)`, `clear_key()`, `has_key() -> bool`

## Step 1: Write the failing test

```python
# tests/test_credentials.py
import os
from unittest.mock import patch, MagicMock
from harness.credentials import CredentialManager

def test_get_key_from_env_first():
    with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "env-key"}):
        cm = CredentialManager(api_key_env="DEEPSEEK_API_KEY")
        assert cm.get_key() == "env-key"

def test_has_key_false_when_no_key():
    with patch.dict(os.environ, {}, clear=True):
        cm = CredentialManager(api_key_env="DEEPSEEK_API_KEY")
        assert cm.has_key() is False

def test_set_key_uses_keyring():
    with patch.dict(os.environ, {}, clear=True):
        with patch("harness.credentials.keyring") as mock_kr:
            mock_kr.get_password.return_value = None
            cm = CredentialManager(api_key_env="DEEPSEEK_API_KEY")
            cm.set_key("my-secret")
            mock_kr.set_password.assert_called_once_with("coding-agent-harness", "DEEPSEEK_API_KEY", "my-secret")

def test_get_key_falls_back_to_keyring():
    with patch.dict(os.environ, {}, clear=True):
        with patch("harness.credentials.keyring") as mock_kr:
            mock_kr.get_password.return_value = "stored-key"
            cm = CredentialManager(api_key_env="DEEPSEEK_API_KEY")
            assert cm.get_key() == "stored-key"

def test_clear_key_removes_from_keyring():
    with patch.dict(os.environ, {}, clear=True):
        with patch("harness.credentials.keyring") as mock_kr:
            cm = CredentialManager(api_key_env="DEEPSEEK_API_KEY")
            cm.clear_key()
            mock_kr.delete_password.assert_called_once_with("coding-agent-harness", "DEEPSEEK_API_KEY")
```

## Step 2: Run test to verify it fails

Run: `pytest tests/test_credentials.py -v`
Expected: FAIL with `ModuleNotFoundError`

## Step 3: Write minimal implementation

```python
# src/harness/credentials.py
import os
import keyring

SERVICE_NAME = "coding-agent-harness"

class CredentialManager:
    def __init__(self, api_key_env: str = "DEEPSEEK_API_KEY"):
        self._env_name = api_key_env

    def get_key(self) -> str | None:
        key = os.environ.get(self._env_name)
        if key:
            return key
        return keyring.get_password(SERVICE_NAME, self._env_name)

    def has_key(self) -> bool:
        return self.get_key() is not None

    def set_key(self, key: str):
        keyring.set_password(SERVICE_NAME, self._env_name, key)

    def clear_key(self):
        try:
            keyring.delete_password(SERVICE_NAME, self._env_name)
        except keyring.errors.PasswordDeleteError:
            pass
```

## Step 4: Run test to verify it passes

Run: `pytest tests/test_credentials.py -v`
Expected: PASS (5 tests)

## Step 5: Commit

```bash
git add src/harness/credentials.py tests/test_credentials.py
git commit -m "feat(credentials): add keyring+env credential manager"
```
