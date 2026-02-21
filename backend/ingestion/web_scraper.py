"""
Scrapes public product pages and press release pages for company product images
and supplementary text content.
"""
import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Known product/IR pages for defense companies
COMPANY_PAGES: dict[str, list[str]] = {
    "Lockheed Martin": [
        "https://www.lockheedmartin.com/en-us/products.html",
        "https://www.lockheedmartin.com/en-us/news/press-releases.html",
    ],
    "BAE Systems": [
        "https://www.baesystems.com/en/products-and-services",
    ],
    "Rheinmetall": [
        "https://www.rheinmetall.com/en/products-and-services",
    ],
    "Thales": [
        "https://www.thalesgroup.com/en/markets/defence-and-security/systems-and-solutions",
    ],
    "Northrop Grumman": [
        "https://www.northropgrumman.com/what-we-do/",
    ],
    "Raytheon": [
        "https://www.rtx.com/raytheon/what-we-do",
    ],
}


@dataclass
class ScrapedProduct:
    name: str
    description: str
    image_url: Optional[str]
    source_url: str
    company_name: str
    alt_text: str = ""
    source_type: str = "product_image"


@dataclass
class ScrapedPage:
    url: str
    title: str
    text_content: str
    images: list[ScrapedProduct] = field(default_factory=list)
    company_name: str = ""


async def scrape_company_products(
    company_name: str, timeout: float = 15.0
) -> list[ScrapedProduct]:
    urls = COMPANY_PAGES.get(company_name, [])
    if not urls:
        logger.warning("No configured scrape URLs for: %s", company_name)
        return []

    products: list[ScrapedProduct] = []
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        for url in urls:
            page_products = await _scrape_page(client, url, company_name)
            products.extend(page_products)

    logger.info("Scraped %d product images for %s", len(products), company_name)
    return products


async def _scrape_page(
    client: httpx.AsyncClient, url: str, company_name: str
) -> list[ScrapedProduct]:
    try:
        response = await client.get(url, headers={"User-Agent": "ResearchBot/1.0"})
        response.raise_for_status()
    except Exception as exc:
        logger.warning("Failed to fetch %s: %s", url, exc)
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    products: list[ScrapedProduct] = []

    for img in soup.find_all("img", src=True):
        src = img.get("src", "")
        alt = img.get("alt", "")
        if not src or len(alt) < 5:
            continue
        # Filter for product-like images (skip icons/logos by size hints)
        width = img.get("width")
        height = img.get("height")
        if width and int(str(width).replace("px", "") or 0) < 100:
            continue

        abs_src = urljoin(base, src)
        # Grab nearest heading or caption as name
        parent = img.parent
        name = ""
        for _ in range(4):
            if parent is None:
                break
            heading = parent.find(re.compile(r"^h[1-6]$"))
            if heading:
                name = heading.get_text(strip=True)
                break
            parent = parent.parent

        products.append(
            ScrapedProduct(
                name=name or alt,
                description=alt,
                image_url=abs_src,
                source_url=url,
                company_name=company_name,
                alt_text=alt,
            )
        )

    return products[:20]  # Limit per page


async def scrape_page_text(url: str, company_name: str = "") -> Optional[ScrapedPage]:
    """Scrape raw text from an arbitrary URL (e.g., a press release link)."""
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        try:
            response = await client.get(url, headers={"User-Agent": "ResearchBot/1.0"})
            response.raise_for_status()
        except Exception as exc:
            logger.warning("Failed to scrape %s: %s", url, exc)
            return None

    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else url
    # Remove script/style noise
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)

    return ScrapedPage(
        url=url,
        title=title,
        text_content=text[:8000],  # Truncate to ~8k chars for embedding
        company_name=company_name,
    )
