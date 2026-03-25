import pytest
from scraper import extract_codes, fetch_reddit_codes, get_new_codes


def test_extract_codes_finds_code_near_keyword():
    text = "New gift code available: KINGSHOT2026 — redeem now!"
    codes = extract_codes(text)
    assert "KINGSHOT2026" in codes


def test_extract_codes_ignores_code_far_from_keyword():
    # UUID-like token with no context keyword nearby
    text = "A" * 200 + "ABCDEF123456" + "B" * 200
    codes = extract_codes(text)
    assert "ABCDEF123456" not in codes


def test_extract_codes_rejects_short_tokens():
    text = "code: AB123"
    codes = extract_codes(text)
    assert "AB123" not in codes


def test_extract_codes_deduplicates():
    text = "gift code SPRING2026 and also SPRING2026 again"
    codes = extract_codes(text)
    assert codes.count("SPRING2026") == 1


def test_extract_codes_only_uppercase():
    text = "code: spring2026"  # lowercase
    codes = extract_codes(text)
    assert "spring2026" not in codes
    assert "SPRING2026" not in codes


def test_get_new_codes_filters_already_redeemed():
    redeemed = {"OLDCODE": {"Account 1": "success"}}
    import scraper
    from unittest.mock import patch
    with patch.object(scraper, "fetch_reddit_codes", return_value=["OLDCODE", "NEWCODE"]), \
         patch.object(scraper, "fetch_firecrawl_codes", return_value=[]):
        result = get_new_codes(redeemed, config={})
    assert "NEWCODE" in result
    assert "OLDCODE" not in result
