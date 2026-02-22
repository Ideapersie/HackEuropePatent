"""
End-to-end ingestion pipeline.
Orchestrates fetching → chunking → embedding → storing for a given company.
"""
import asyncio
import json
import logging
import os
from typing import Optional

from backend.core.config import get_settings
from backend.ingestion.yfinance_client import fetch_company_news, fetch_company_info
from backend.ingestion.epo_client import get_epo_client, PatentRecord
from backend.ingestion.web_scraper import scrape_company_products
from backend.rag.chunker import chunk_patent, chunk_news_item, chunk_patent_json, chunk_press_release, Chunk
from backend.rag.embeddings import embed_text, embed_image_url
from backend.rag.vector_store import get_chroma, bulk_upsert_documents, get_ingestion_stats

# Maps JSON company keys → canonical names used by agents
PATENT_JSON_COMPANY_MAP: dict[str, str] = {
    "LOCKHEED CORP": "Lockheed Martin",
    "RTX CORP": "RTX",
    "BAE Systems": "BAE Systems",
    "BOEING CO": "Boeing",
    "SAAB AB": "SAAB",
}

# Keywords for detecting which company a press release belongs to (case-insensitive)
PRESS_RELEASE_COMPANY_KEYWORDS: dict[str, list[str]] = {
    "Lockheed Martin": ["lockheed"],
    "Boeing": ["boeing"],
    "BAE Systems": ["bae systems"],
    "RTX": ["rtx", "raytheon"],
    "SAAB": ["saab"],
    "Northrop Grumman": ["northrop grumman", "northrop"],
    "Airbus": ["airbus"],
}

logger = logging.getLogger(__name__)
_settings = get_settings()


async def ingest_company(company_name: str) -> dict:
    """
    Full ingestion pipeline for one company.
    Returns stats dict with counts per source type.
    """
    chroma = get_chroma()
    records_to_insert: list[dict] = []

    # 1. Fetch and embed news
    logger.info("[pipeline] Fetching news for %s", company_name)
    news_items = await fetch_company_news(company_name, max_items=50)
    for item in news_items:
        chunks = chunk_news_item(item)
        embeddings = await asyncio.gather(*[embed_text(c.text) for c in chunks])
        for chunk, emb in zip(chunks, embeddings):
            records_to_insert.append({
                "company": company_name,
                "source_type": "news",
                "content": chunk.text,
                "embedding": emb,
                "metadata": chunk.metadata,
                "image_url": None,
            })

    # 2. Fetch and embed patents via EPO
    logger.info("[pipeline] Fetching patents for %s", company_name)
    epo = get_epo_client(_settings.epo_consumer_key, _settings.epo_consumer_secret)
    patents = await epo.fetch_patents(company_name, max_results=30)
    for patent in patents:
        chunks = chunk_patent(patent)
        embeddings = await asyncio.gather(*[embed_text(c.text) for c in chunks])
        for chunk, emb in zip(chunks, embeddings):
            records_to_insert.append({
                "company": company_name,
                "source_type": "patent",
                "content": chunk.text,
                "embedding": emb,
                "metadata": chunk.metadata,
                "image_url": patent.pdf_url,
            })

    # 3. Scrape and embed product images
    logger.info("[pipeline] Scraping product images for %s", company_name)
    products = await scrape_company_products(company_name)
    for product in products:
        if not product.image_url:
            continue
        emb = await embed_image_url(product.image_url)
        records_to_insert.append({
            "company": company_name,
            "source_type": "product_image",
            "content": f"{product.name}: {product.description}",
            "embedding": emb,
            "metadata": {
                "name": product.name,
                "source_url": product.source_url,
                "alt_text": product.alt_text,
            },
            "image_url": product.image_url,
        })

    # 4. Bulk insert
    count = await bulk_upsert_documents(chroma, records_to_insert)
    logger.info("[pipeline] Inserted %d records for %s", count, company_name)

    return await get_ingestion_stats(chroma, company_name)


async def ingest_patents_from_json(json_path: str | None = None) -> dict:
    """
    Load patent_results.json, chunk each record optimally (header + per-claim + description
    sections), embed, and upsert to ChromaDB.  Returns per-company chunk counts.
    """
    path = json_path or os.path.join(os.path.dirname(__file__), "patent_results.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    chroma = get_chroma()
    all_stats: dict[str, int] = {}

    for json_company, patents in data.items():
        canonical = PATENT_JSON_COMPANY_MAP.get(json_company, json_company)
        records_to_insert: list[dict] = []

        for patent in patents:
            chunks = chunk_patent_json(patent, canonical)
            if not chunks:
                continue
            embeddings = await asyncio.gather(*[embed_text(c.text) for c in chunks])
            for chunk, emb in zip(chunks, embeddings):
                records_to_insert.append({
                    "company": canonical,
                    "source_type": "patent",
                    "content": chunk.text,
                    "embedding": emb,
                    "metadata": chunk.metadata,
                    "image_url": None,
                })

        count = await bulk_upsert_documents(chroma, records_to_insert)
        logger.info("[json-ingest] Patents: %s → %d chunks from %d records",
                    canonical, count, len(patents))
        all_stats[canonical] = count

    return all_stats


async def ingest_press_releases_from_json(json_path: str | None = None) -> dict:
    """
    Load press_releases.json, detect company from content keywords, chunk each article,
    embed, and upsert to ChromaDB.  Returns per-company chunk counts.
    One article can be assigned to multiple companies if it mentions more than one.
    """
    path = json_path or os.path.join(os.path.dirname(__file__), "press_releases.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    chroma = get_chroma()
    company_records: dict[str, list[dict]] = {co: [] for co in PRESS_RELEASE_COMPANY_KEYWORDS}

    for record in data:
        search_text = (record.get("title", "") + " " + record.get("content", "")).lower()
        for company, keywords in PRESS_RELEASE_COMPANY_KEYWORDS.items():
            if not any(kw in search_text for kw in keywords):
                continue
            chunks = chunk_press_release(record, company)
            if not chunks:
                continue
            embeddings = await asyncio.gather(*[embed_text(c.text) for c in chunks])
            for chunk, emb in zip(chunks, embeddings):
                company_records[company].append({
                    "company": company,
                    "source_type": "news",
                    "content": chunk.text,
                    "embedding": emb,
                    "metadata": chunk.metadata,
                    "image_url": None,
                })

    all_stats: dict[str, int] = {}
    for company, records in company_records.items():
        if not records:
            continue
        count = await bulk_upsert_documents(chroma, records)
        logger.info("[json-ingest] News: %s → %d chunks", company, count)
        all_stats[company] = count

    return all_stats
