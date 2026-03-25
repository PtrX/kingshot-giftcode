# main.py
import json
import logging
import sys
from pathlib import Path

from scraper import get_new_codes
from redeemer import redeem_code
from notifier import send_success, send_critical_error

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.json"
DEFAULT_STATE_PATH = Path(__file__).parent / "redeemed.json"


def load_config(config_path: str = str(DEFAULT_CONFIG_PATH)) -> dict:
    with open(config_path) as f:
        return json.load(f)


def load_state(state_path: str = str(DEFAULT_STATE_PATH)) -> dict:
    path = Path(state_path)
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def save_state(state: dict, state_path: str = str(DEFAULT_STATE_PATH)) -> None:
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)


def run(
    state_path: str = str(DEFAULT_STATE_PATH),
    config_path: str = str(DEFAULT_CONFIG_PATH),
) -> None:
    config = load_config(config_path)
    state = load_state(state_path)

    try:
        new_codes = get_new_codes(state, config)
    except Exception as e:
        logger.error(f"Scraper auth error: {e}")
        send_critical_error(str(e), config)
        return

    if not new_codes:
        logger.info("No new codes found.")
        return

    logger.info(f"Found {len(new_codes)} new code(s): {new_codes}")
    all_results = {}

    for code in new_codes:
        state.setdefault(code, {})

        def on_account_done(name: str, result: str) -> None:
            state[code][name] = result
            save_state(state, state_path)

        try:
            results = redeem_code(code, config["accounts"], on_account_done=on_account_done)
        except RuntimeError as e:
            logger.error(f"Page unreachable for code {code}: {e}")
            send_critical_error(str(e), config)
            return

        all_results[code] = results

    send_success(all_results, config)


if __name__ == "__main__":
    run()
