"""
Standalone test script: verifies yfinance can pull Lockheed Martin press releases.

Run from the repo root (no .env or API keys required):
    python backend/scripts/test_yfinance.py

Optional: pass a different company name as an argument:
    python backend/scripts/test_yfinance.py "BAE Systems"
"""
import asyncio
import os
import sys

# Make 'backend' importable when run from the repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.ingestion.yfinance_client import fetch_company_news, TICKER_MAP

COMPANY = sys.argv[1] if len(sys.argv) > 1 else "Lockheed Martin"
SUMMARY_MAX = 200


async def main() -> None:
    if COMPANY not in TICKER_MAP:
        print(f"ERROR: '{COMPANY}' not in TICKER_MAP.")
        print(f"Supported companies: {', '.join(TICKER_MAP.keys())}")
        sys.exit(1)

    ticker = TICKER_MAP[COMPANY]
    print(f"Company  : {COMPANY}")
    print(f"Ticker   : {ticker}")
    print("=" * 65)

    items = await fetch_company_news(COMPANY, max_items=10)

    if not items:
        print("No items returned. Check your network connection.")
        return

    for i, item in enumerate(items, start=1):
        summary = item.summary or ""
        snippet = summary[:SUMMARY_MAX] + ("…" if len(summary) > SUMMARY_MAX else "")

        print(f"\n[{i:02d}] {item.title}")
        print(f"     Publisher : {item.publisher}")
        print(f"     Published : {item.published_at.strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"     Link      : {item.link}")
        if snippet:
            print(f"     Summary   : {snippet}")

    print(f"\n{'=' * 65}")
    print(f"Total fetched: {len(items)} items for '{COMPANY}' ({ticker})")


if __name__ == "__main__":
    asyncio.run(main())
