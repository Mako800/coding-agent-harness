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
