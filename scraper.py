import re
import logging
import keyring
import requests
from datetime import datetime, timedelta, timezone

try:
    from firecrawl import FirecrawlApp
except ImportError:
    FirecrawlApp = None

logger = logging.getLogger(__name__)

# Kingshot gift code pattern: uppercase alphanumeric, 6-20 chars
CODE_PATTERN = re.compile(r'\b([A-Z0-9]{6,20})\b')
CONTEXT_KEYWORDS = re.compile(r'(code|gift|redeem|kingshot)', re.IGNORECASE)
CONTEXT_WINDOW = 100  # characters around a match to check for keywords


def extract_codes(text: str) -> list[str]:
    """Extract gift codes from text using regex + keyword context filter."""
    seen = set()
    results = []
    for match in CODE_PATTERN.finditer(text):
        code = match.group(1)
        if code in seen:
            continue
        start = max(0, match.start() - CONTEXT_WINDOW)
        end = min(len(text), match.end() + CONTEXT_WINDOW)
        context = text[start:end]
        if CONTEXT_KEYWORDS.search(context):
            seen.add(code)
            results.append(code)
    return results


def fetch_reddit_codes(subreddit: str, days: int = 30) -> list[str]:
    """Fetch codes from Reddit's open JSON API."""
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {"q": "gift code", "sort": "new", "limit": 50, "restrict_sr": True}
    headers = {"User-Agent": "kingshot-code-bot/1.0"}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.warning(f"Reddit fetch failed: {e}")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    codes = []
    for post in data.get("data", {}).get("children", []):
        post_data = post.get("data", {})
        created = datetime.fromtimestamp(post_data.get("created_utc", 0), tz=timezone.utc)
        if created < cutoff:
            continue
        text = f"{post_data.get('title', '')} {post_data.get('selftext', '')}"
        codes.extend(extract_codes(text))
    return codes


def fetch_firecrawl_codes(query: str, urls: list[str], days: int = 30) -> list[str]:
    """Fetch codes from Twitter/X search and aggregator URLs via Firecrawl."""
    api_key = keyring.get_password("kingshot", "firecrawl_api_key")
    if not api_key or FirecrawlApp is None:
        logger.warning("Firecrawl not available (no API key or package not installed)")
        return []

    app = FirecrawlApp(api_key=api_key)
    codes = []

    # Twitter/X search
    try:
        result = app.search(query, {"limit": 10})
        for item in result.get("data", []):
            content = item.get("markdown", "") + " " + item.get("title", "")
            codes.extend(extract_codes(content))
    except Exception as e:
        status = getattr(getattr(e, "response", None), "status_code", None)
        if status in (401, 403):
            raise  # Auth error — bubble up for Telegram alert
        logger.warning(f"Firecrawl search failed (transient): {e}")

    # Aggregator URLs
    for url in urls:
        try:
            result = app.scrape_url(url, {"formats": ["markdown"]})
            content = result.get("markdown", "")
            codes.extend(extract_codes(content))
        except Exception as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status in (401, 403):
                raise
            logger.warning(f"Firecrawl scrape failed for {url} (transient): {e}")

    return codes


def get_new_codes(redeemed: dict, config: dict) -> list[str]:
    """Fetch all sources, deduplicate, filter already-redeemed codes."""
    days = config.get("scraper", {}).get("code_age_days", 30)
    subreddit = config.get("scraper", {}).get("subreddit", "Kingshot")
    query = config.get("scraper", {}).get("twitter_query", "Kingshot gift code")
    agg_urls = config.get("scraper", {}).get("aggregator_urls", [])

    all_codes = []
    all_codes.extend(fetch_reddit_codes(subreddit, days))
    all_codes.extend(fetch_firecrawl_codes(query, agg_urls, days))

    seen = set()
    new_codes = []
    for code in all_codes:
        if code not in seen and code not in redeemed:
            seen.add(code)
            new_codes.append(code)

    return new_codes
