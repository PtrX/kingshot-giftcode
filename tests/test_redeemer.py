import pytest
from redeemer import parse_result_text, RedemptionResult


def test_parse_success():
    assert parse_result_text("Redeemed successfully") == RedemptionResult.SUCCESS


def test_parse_already_redeemed():
    assert parse_result_text("Code has been used") == RedemptionResult.ALREADY_REDEEMED


def test_parse_invalid():
    assert parse_result_text("Invalid code") == RedemptionResult.INVALID


def test_parse_unknown_falls_back_to_error():
    assert parse_result_text("Some unexpected message") == RedemptionResult.ERROR


def test_parse_is_case_insensitive():
    assert parse_result_text("redeemed successfully") == RedemptionResult.SUCCESS
    assert parse_result_text("INVALID CODE") == RedemptionResult.INVALID
