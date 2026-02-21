"""
Supabase pgvector integration.

Manages upsert and similarity search of document embeddings.
The Supabase table schema expected:

    CREATE EXTENSION IF NOT EXISTS vector;

    CREATE TABLE documents (
        id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        company     TEXT NOT NULL,
        source_type TEXT NOT NULL,          -- 'patent' | 'news' | 'product_image'
        content     TEXT NOT NULL,
        metadata    JSONB DEFAULT '{}',
        image_url   TEXT,
        embedding   vector(768)
    );

    CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
"""
import json
import logging
from typing import Any, Optional

from supabase import create_client, Client as SupabaseClient

from backend.core.config import get_settings

logger = logging.getLogger(__name__)

_settings = get_settings()
TABLE = "documents"


def get_supabase() -> SupabaseClient:
    return create_client(_settings.supabase_url, _settings.supabase_service_key)


async def upsert_document(
    supabase: SupabaseClient,
    company: str,
    source_type: str,
    content: str,
    embedding: list[float],
    metadata: dict[str, Any] | None = None,
    image_url: Optional[str] = None,
) -> dict:
    """Insert or update a document embedding in Supabase."""
    row = {
        "company": company,
        "source_type": source_type,
        "content": content,
        "embedding": embedding,
        "metadata": metadata or {},
        "image_url": image_url,
    }
    result = supabase.table(TABLE).insert(row).execute()
    return result.data[0] if result.data else {}


async def similarity_search(
    supabase: SupabaseClient,
    query_embedding: list[float],
    company: str,
    source_types: list[str] | None = None,
    top_k: int = 10,
) -> list[dict]:
    """
    Perform cosine-similarity search via a Supabase RPC function.

    The expected stored procedure:

        CREATE OR REPLACE FUNCTION match_documents(
            query_embedding vector(768),
            filter_company  text,
            filter_types    text[],
            match_count     int
        )
        RETURNS TABLE (
            id          uuid,
            company     text,
            source_type text,
            content     text,
            metadata    jsonb,
            image_url   text,
            similarity  float
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT
                d.id, d.company, d.source_type, d.content,
                d.metadata, d.image_url,
                1 - (d.embedding <=> query_embedding) AS similarity
            FROM documents d
            WHERE d.company = filter_company
              AND (filter_types IS NULL OR d.source_type = ANY(filter_types))
            ORDER BY d.embedding <=> query_embedding
            LIMIT match_count;
        END;
        $$;
    """
    params = {
        "query_embedding": query_embedding,
        "filter_company": company,
        "filter_types": source_types,
        "match_count": top_k,
    }
    result = supabase.rpc("match_documents", params).execute()
    return result.data or []


async def get_ingestion_stats(supabase: SupabaseClient, company: str) -> dict:
    """Return counts of ingested documents per source type for a company."""
    result = (
        supabase.table(TABLE)
        .select("source_type")
        .eq("company", company)
        .execute()
    )
    rows = result.data or []
    stats: dict[str, int] = {}
    for row in rows:
        st = row.get("source_type", "unknown")
        stats[st] = stats.get(st, 0) + 1
    return stats


async def bulk_upsert_documents(
    supabase: SupabaseClient,
    records: list[dict],
) -> int:
    """Bulk insert multiple pre-formed document rows. Returns count inserted."""
    if not records:
        return 0
    result = supabase.table(TABLE).insert(records).execute()
    return len(result.data or [])
