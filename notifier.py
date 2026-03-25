# notifier.py
import keyring
import requests
from datetime import date


TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

STATUS_EMOJI = {
    "success": "✅ Erfolg",
    "already_redeemed": "❌ Bereits eingelöst",
    "invalid": "❌ Ungültig",
    "error": "❌ Fehler",
}


def _get_token() -> str:
    return keyring.get_password("kingshot", "telegram_token")


def _send(text: str, config: dict) -> None:
    token = _get_token()
    chat_id = config["telegram"]["chat_id"]
    url = TELEGRAM_API.format(token=token)
    response = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
    response.raise_for_status()


def send_success(results: dict, config: dict) -> None:
    """Send result summary. Silent if no results."""
    if not results:
        return

    today = date.today().strftime("%d.%m.%Y")
    messages = []

    for code, account_results in results.items():
        statuses = list(account_results.values())
        all_ok = all(s == "success" for s in statuses)
        prefix = "✅ Kingshot Codes eingelöst" if all_ok else "⚠️ Kingshot Code teilweise fehlgeschlagen"

        lines = [f"{prefix} ({today})", f"Code: <code>{code}</code>"]
        for account_name, status in account_results.items():
            lines.append(f"  • {account_name} — {STATUS_EMOJI.get(status, status)}")
        messages.append("\n".join(lines))

    _send("\n\n".join(messages), config)


def send_critical_error(message: str, config: dict) -> None:
    text = f"🚨 Kingshot Automation Fehler\nFehler: {message}\nDiagnose: ~/Library/Logs/kingshot.log"
    _send(text, config)
