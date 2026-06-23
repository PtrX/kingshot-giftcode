# Kingshot Gift Code Automation

Automatically scrapes new gift codes for the mobile game **Kingshot** and redeems them for one or more accounts — fully headless, runs daily via macOS launchd, and notifies you via Telegram.

## Why this exists

Gift codes are easy to miss and often expire quickly. This project turns a repetitive manual check into a small, auditable automation pipeline: discover codes, de-duplicate them, redeem them for configured accounts, and report the result.

## What it does

1. **Scrapes** new gift codes from multiple sources:
   - Reddit (`r/Kingshot`) via the public JSON API
   - Community aggregator websites via [Firecrawl](https://www.firecrawl.dev/)
   - Twitter/X search via Firecrawl
2. **Filters** out codes that have already been processed (tracked in `redeemed.json`)
3. **Redeems** each new code for all configured accounts using a headless Chromium browser (Playwright)
4. **Notifies** you via Telegram with the result for each account

## Requirements

- Python 3.12+
- macOS (launchd scheduling) — the scripts run manually on other platforms too
- A [Firecrawl](https://www.firecrawl.dev/) API key (optional — Reddit scraping works without it)
- A Telegram bot token and chat ID (optional — for notifications)

## Responsible use

Use this only for accounts you own or are explicitly allowed to manage. The automation keeps request volume low and is designed for personal convenience, not bulk abuse.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/PtrX/kingshot-giftcode.git
cd kingshot-giftcode
```

### 2. Create a virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure your accounts

Copy the example config and fill in your details:

```bash
cp config.example.json config.json
```

Edit `config.json`:

```json
{
  "accounts": [
    {"name": "Main", "game_id": "YOUR_GAME_ID"}
  ],
  "telegram": {
    "chat_id": "YOUR_TELEGRAM_CHAT_ID"
  },
  "scraper": {
    "subreddit": "Kingshot",
    "aggregator_urls": [
      "https://www.gameskeys.net/kingshot-gift-codes/",
      "https://www.eldorado.gg/blog/kingshot-codes",
      "https://kingshot.net/gift-codes",
      "https://kingshotwiki.com/giftcodes/",
      "https://www.gamsgo.com/blog/kingshot-gift-code",
      "https://kingshotmastery.com/guides/kingshot-gift-codes",
      "https://www.lootbar.com/blog/en/newest-kingshot-gift-codes.html",
      "https://www.gamesradar.com/games/strategy/kingshot-codes-gift/",
      "https://boostbot.org/blog/kingshot-gift-codes/"
    ],
    "twitter_query": "Kingshot gift code",
    "code_age_days": 30
  }
}
```

Your **Game ID** can be found in the Kingshot app under Settings → Account.
You can add multiple accounts to the `accounts` array.

### 4. Store secrets in the system keyring

API keys and tokens are stored securely in the macOS keyring — never in config files.

```bash
# Telegram bot token (from @BotFather)
python3 -c "import keyring; keyring.set_password('kingshot', 'telegram_token', 'YOUR_BOT_TOKEN')"

# Firecrawl API key (optional)
python3 -c "import keyring; keyring.set_password('kingshot', 'firecrawl_api_key', 'YOUR_API_KEY')"
```

### 5. Run manually

```bash
source .venv/bin/activate
python3 main.py
```

Or double-click `Kingshot Codes einlösen.command` in Finder.

## Automatic daily execution (macOS)

A launchd plist is included to run the script every day at 09:00.

1. Copy and adapt the example plist — replace the paths with your actual installation directory:

```bash
cp com.peter.kingshot.plist ~/Library/LaunchAgents/com.kingshot.plist
# Edit the file and update the paths to match your system
```

2. Load the agent:

```bash
launchctl load ~/Library/LaunchAgents/com.kingshot.plist
```

Logs are written to `~/Library/Logs/kingshot.log`.
Screenshots of failed redemptions are saved to `~/Library/Logs/kingshot-screenshots/`.
Each run logs a source heartbeat like `Scraper summary: reddit=0 firecrawl=3 candidates=3 new=1`.

## Project structure

```
├── main.py              # Orchestration: scrape → redeem → notify
├── scraper.py           # Code discovery (Reddit + Firecrawl)
├── redeemer.py          # Headless browser automation (Playwright)
├── notifier.py          # Telegram notifications
├── config.example.json  # Config template (copy to config.json)
├── redeemed.json        # State file — tracks processed codes (auto-created)
└── tests/               # Unit tests (pytest)
```

## Telegram notifications

You receive a message after each run with the result per account:

```
✅ Kingshot Codes eingelöst (27.03.2026)
Code: FIREFRIDAY
  • Main — ✅ Erfolg
  • Second — ✅ Erfolg
```

To create a Telegram bot: message [@BotFather](https://t.me/BotFather) on Telegram and follow the `/newbot` flow.
To get your chat ID: message [@userinfobot](https://t.me/userinfobot).

## Security Notes

- Real account IDs belong in `config.json`, which should stay local and uncommitted.
- API keys and Telegram tokens are read from the macOS keychain.
- Runtime files such as `redeemed.json`, logs, and screenshots should not be committed.

## Running tests

```bash
source .venv/bin/activate
pytest
```

## Lessons Learned

- Browser automation is more stable when each account starts from a clean session.
- Personal automation benefits from explicit state files; de-duplication makes retries safe.
- Notifications are more useful when they include both the discovered code and the per-account result.
