"""
End-to-end ingestion pipeline.
Orchestrates fetching → chunking → embedding → storing for a given company.
"""
import asyncio
import logging
from typing import Optional

from backend.core.config import get_settings
from backend.ingestion.yfinance_client import fetch_company_news, fetch_company_info
from backend.ingestion.epo_client import get_epo_client, PatentRecord
from backend.ingestion.web_scraper import scrape_company_products
from backend.rag.chunker import chunk_patent, chunk_news_item, Chunk
from backend.rag.embeddings import embed_text, embed_image_url
from backend.rag.vector_store import get_supabase, bulk_upsert_documents, get_ingestion_stats

logger = logging.getLogger(__name__)
_settings = get_settings()


async def ingest_company(company_name: str) -> dict:
    """
    Full ingestion pipeline for one company.
    Returns stats dict with counts per source type.
    """
    supabase = get_supabase()
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
    count = await bulk_upsert_documents(supabase, records_to_insert)
    logger.info("[pipeline] Inserted %d records for %s", count, company_name)

    return await get_ingestion_stats(supabase, company_name)
