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
