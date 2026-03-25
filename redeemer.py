import logging
import time
from enum import Enum
from pathlib import Path
from datetime import datetime

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)

REDEMPTION_URL = "https://ks-giftcode.centurygame.com"
SCREENSHOT_DIR = Path.home() / "Library" / "Logs" / "kingshot-screenshots"


class RedemptionResult(str, Enum):
    SUCCESS = "success"
    ALREADY_REDEEMED = "already_redeemed"
    INVALID = "invalid"
    ERROR = "error"


def parse_result_text(text: str) -> RedemptionResult:
    """Parse the redemption page response text into a result enum."""
    text_lower = text.lower()
    if "redeemed successfully" in text_lower:
        return RedemptionResult.SUCCESS
    if "code has been used" in text_lower or "already" in text_lower:
        return RedemptionResult.ALREADY_REDEEMED
    if "invalid" in text_lower:
        return RedemptionResult.INVALID
    return RedemptionResult.ERROR


def _save_screenshot(page, label: str) -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SCREENSHOT_DIR / f"{ts}_{label}.png"
    page.screenshot(path=str(path))
    logger.info(f"Screenshot saved: {path}")


def redeem_code(code: str, accounts: list[dict], on_account_done=None) -> dict[str, str]:
    """
    Redeem a code for each account on the Kingshot redemption page.
    Returns dict mapping account name to RedemptionResult value.

    `on_account_done(name, result)` is called after each account attempt —
    use this to write state immediately for crash safety.

    Integration note: verify during testing that:
    - The form resets cleanly between account submissions (no reload needed)
    - No session-based throttling is triggered by rapid submissions
    - The result modal/toast selector is correct
    """
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate with one retry on failure
        for attempt in range(2):
            try:
                page.goto(REDEMPTION_URL, timeout=15000)
                page.wait_for_load_state("networkidle", timeout=15000)
                break
            except PlaywrightTimeout as e:
                if attempt == 0:
                    logger.warning("Page load timed out, retrying in 10s...")
                    time.sleep(10)
                else:
                    _save_screenshot(page, "load_failed")
                    browser.close()
                    raise RuntimeError(f"Redemption page unreachable after retry: {e}")

        for account in accounts:
            name = account["name"]
            game_id = account["game_id"]
            try:
                # Fill code field
                page.fill('input[name="code"], input[placeholder*="code" i]', code)
                # Fill UID field
                page.fill('input[name="uid"], input[placeholder*="uid" i], input[placeholder*="id" i]', game_id)
                # Submit
                page.click('button[type="submit"], button:has-text("Confirm"), button:has-text("Redeem")')
                # Wait for result modal/toast
                result_el = page.wait_for_selector(
                    '.result-message, .toast, .modal-body, [class*="result"], [class*="message"]',
                    timeout=8000
                )
                result_text = result_el.inner_text()
                result = parse_result_text(result_text)
                logger.info(f"Code {code} | {name}: {result.value}")
                results[name] = result.value

                # Dismiss modal if present
                try:
                    page.click('button:has-text("OK"), button:has-text("Close"), .modal button', timeout=2000)
                except Exception:
                    pass

            except PlaywrightTimeout as e:
                _save_screenshot(page, f"timeout_{name.replace(' ', '_')}")
                logger.error(f"Timeout for {name}: {e}")
                results[name] = RedemptionResult.ERROR.value
            except Exception as e:
                logger.error(f"Error for {name}: {e}")
                results[name] = RedemptionResult.ERROR.value

            # Write state after each account attempt (crash safety)
            if on_account_done:
                on_account_done(name, results[name])

        browser.close()

    return results
