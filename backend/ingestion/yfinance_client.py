"""
Fetches company press releases and news filings using yfinance.
"""
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import yfinance as yf

logger = logging.getLogger(__name__)

TICKER_MAP: dict[str, str] = {
    "Lockheed Martin": "LMT",
    "BAE Systems": "BAESY",
    "Rheinmetall": "RHM.DE",
    "Thales": "HO.PA",
    "Leonardo": "LDO.MI",
    "Airbus": "AIR.PA",
    "General Dynamics": "GD",
    "Northrop Grumman": "NOC",
    "Raytheon": "RTX",
}


@dataclass
class NewsItem:
    title: str
    publisher: str
    link: str
    published_at: datetime
    summary: str
    ticker: str
    company_name: str
    source_type: str = "news"


async def fetch_company_news(company_name: str, max_items: int = 50) -> list[NewsItem]:
    """Fetch recent news and press releases for a company via yfinance."""
    ticker_symbol = TICKER_MAP.get(company_name)
    if not ticker_symbol:
        logger.warning("No ticker found for company: %s", company_name)
        return []

    loop = asyncio.get_event_loop()
    items = await loop.run_in_executor(None, _fetch_sync, ticker_symbol, company_name, max_items)
    return items


def _fetch_sync(ticker_symbol: str, company_name: str, max_items: int) -> list[NewsItem]:
    ticker = yf.Ticker(ticker_symbol)
    raw_news = ticker.news or []

    results: list[NewsItem] = []
    for item in raw_news[:max_items]:
        content = item.get("content", {})
        title = content.get("title", item.get("title", ""))
        publisher = (
            content.get("provider", {}).get("displayName", "")
            or item.get("publisher", "")
        )
        link = (
            content.get("canonicalUrl", {}).get("url", "")
            or item.get("link", "")
        )
        summary = content.get("summary", item.get("summary", ""))

        # Parse publish time
        pub_time = content.get("pubDate") or item.get("providerPublishTime")
        if isinstance(pub_time, (int, float)):
            published_at = datetime.fromtimestamp(pub_time)
        elif isinstance(pub_time, str):
            try:
                published_at = datetime.fromisoformat(pub_time.replace("Z", "+00:00"))
            except ValueError:
                published_at = datetime.utcnow()
        else:
            published_at = datetime.utcnow()

        results.append(
            NewsItem(
                title=title,
                publisher=publisher,
                link=link,
                published_at=published_at,
                summary=summary,
                ticker=ticker_symbol,
                company_name=company_name,
            )
        )

    logger.info("Fetched %d news items for %s (%s)", len(results), company_name, ticker_symbol)
    return results


async def fetch_company_info(company_name: str) -> dict:
    """Fetch general company info (description, sector, etc.)."""
    ticker_symbol = TICKER_MAP.get(company_name)
    if not ticker_symbol:
        return {}

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_info_sync, ticker_symbol)


def _fetch_info_sync(ticker_symbol: str) -> dict:
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info or {}
    return {
        "longBusinessSummary": info.get("longBusinessSummary", ""),
        "sector": info.get("sector", ""),
        "industry": info.get("industry", ""),
        "website": info.get("website", ""),
        "fullTimeEmployees": info.get("fullTimeEmployees"),
    }
