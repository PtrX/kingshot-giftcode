# tests/test_main.py
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import main


@pytest.fixture
def tmp_state(tmp_path):
    state_file = tmp_path / "redeemed.json"
    state_file.write_text("{}")
    return state_file


@pytest.fixture
def sample_config():
    return {
        "accounts": [
            {"name": "Account 1", "game_id": "111"},
            {"name": "Account 2", "game_id": "222"},
        ],
        "telegram": {"chat_id": "99999"},
        "scraper": {"subreddit": "Kingshot", "aggregator_urls": [], "twitter_query": "Kingshot gift code", "code_age_days": 30}
    }


def test_load_state_returns_empty_dict_when_file_empty(tmp_path):
    state_file = tmp_path / "redeemed.json"
    state_file.write_text("{}")
    state = main.load_state(str(state_file))
    assert state == {}


def test_save_and_reload_state(tmp_state):
    data = {"TESTCODE": {"Account 1": "success"}}
    main.save_state(data, str(tmp_state))
    loaded = main.load_state(str(tmp_state))
    assert loaded == data


def test_run_redeems_new_code(tmp_state, sample_config):
    redeem_result = {"Account 1": "success", "Account 2": "success"}
    with patch("main.load_config", return_value=sample_config), \
         patch("main.load_state", return_value={}), \
         patch("main.get_new_codes", return_value=["NEWCODE"]), \
         patch("main.redeem_code", return_value=redeem_result) as mock_redeem, \
         patch("main.send_success") as mock_notify:
        main.run(state_path=str(tmp_state), config_path="irrelevant")
        assert mock_redeem.call_args[0] == ("NEWCODE", sample_config["accounts"])
        assert "on_account_done" in mock_redeem.call_args[1]
        mock_notify.assert_called_once()


def test_run_silent_when_no_new_codes(tmp_state, sample_config):
    with patch("main.load_config", return_value=sample_config), \
         patch("main.load_state", return_value={}), \
         patch("main.get_new_codes", return_value=[]), \
         patch("main.redeem_code") as mock_redeem, \
         patch("main.send_success") as mock_notify:
        main.run(state_path=str(tmp_state), config_path="irrelevant")
        mock_redeem.assert_not_called()
        mock_notify.assert_not_called()


def test_run_sends_critical_error_on_page_unreachable(tmp_state, sample_config):
    with patch("main.load_config", return_value=sample_config), \
         patch("main.load_state", return_value={}), \
         patch("main.get_new_codes", return_value=["NEWCODE"]), \
         patch("main.redeem_code", side_effect=RuntimeError("Page unreachable")), \
         patch("main.send_critical_error") as mock_error:
        main.run(state_path=str(tmp_state), config_path="irrelevant")
        mock_error.assert_called_once()


def test_run_sends_critical_error_on_firecrawl_auth_failure(tmp_state, sample_config):
    """Firecrawl 401/403 bubbles up from get_new_codes and triggers a Telegram alert."""
    auth_error = Exception("401 Unauthorized")
    with patch("main.load_config", return_value=sample_config), \
         patch("main.load_state", return_value={}), \
         patch("main.get_new_codes", side_effect=auth_error), \
         patch("main.send_critical_error") as mock_error:
        main.run(state_path=str(tmp_state), config_path="irrelevant")
        mock_error.assert_called_once()
        assert "401" in mock_error.call_args[0][0]
