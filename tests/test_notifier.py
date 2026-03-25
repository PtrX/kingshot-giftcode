# tests/test_notifier.py
import json
import pytest
from unittest.mock import patch, MagicMock
from notifier import send_success, send_critical_error


MOCK_TOKEN = "mock_token"
MOCK_CHAT_ID = "12345"


@pytest.fixture
def config():
    return {
        "telegram": {"chat_id": MOCK_CHAT_ID}
    }


def test_send_success_all_ok(config):
    results = {
        "SPRING2026": {
            "Account 1": "success",
            "Account 2": "success",
            "Account 3": "success",
        }
    }
    with patch("notifier.keyring.get_password", return_value=MOCK_TOKEN), \
         patch("notifier.requests.post") as mock_post:
        mock_post.return_value.ok = True
        send_success(results, config)
        assert mock_post.called
        body = mock_post.call_args[1]["json"]["text"]
        assert "SPRING2026" in body
        assert "✅" in body


def test_send_success_partial_failure(config):
    results = {
        "SPRING2026": {
            "Account 1": "success",
            "Account 2": "already_redeemed",
            "Account 3": "success",
        }
    }
    with patch("notifier.keyring.get_password", return_value=MOCK_TOKEN), \
         patch("notifier.requests.post") as mock_post:
        mock_post.return_value.ok = True
        send_success(results, config)
        body = mock_post.call_args[1]["json"]["text"]
        assert "⚠️" in body
        assert "❌" in body


def test_send_critical_error(config):
    with patch("notifier.keyring.get_password", return_value=MOCK_TOKEN), \
         patch("notifier.requests.post") as mock_post:
        mock_post.return_value.ok = True
        send_critical_error("Something went wrong", config)
        body = mock_post.call_args[1]["json"]["text"]
        assert "🚨" in body
        assert "Something went wrong" in body


def test_send_success_no_codes_does_nothing(config):
    with patch("notifier.keyring.get_password", return_value=MOCK_TOKEN), \
         patch("notifier.requests.post") as mock_post:
        send_success({}, config)
        assert not mock_post.called
