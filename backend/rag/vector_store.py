"""
Local ChromaDB vector store — replaces Supabase pgvector.

Data is persisted to disk at the path set by settings.chroma_path
(default: backend/data/chroma). No external service or API keys required.

Collection schema mirrors the old Supabase `documents` table:
    company      TEXT  (stored in metadata)
    source_type  TEXT  (stored in metadata) — 'patent' | 'news' | 'product_image'
    content      TEXT  (the document text / ChromaDB `documents` field)
    metadata     DICT  (source-specific fields, flattened to scalar values)
    image_url    TEXT  (stored in metadata, empty string when None)
    embedding    list[float]  (768-dim Gemini vector)
"""
import hashlib
import logging
import os
from typing import Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.core.config import get_settings

logger = logging.getLogger(__name__)

_settings = get_settings()
COLLECTION_NAME = "documents"

# Module-level singleton — avoid re-opening the DB on every request
_client: Optional[chromadb.ClientAPI] = None


def get_chroma() -> chromadb.ClientAPI:
    """Return (and lazily initialise) the persistent ChromaDB client."""
    global _client
    if _client is None:
        path = os.path.abspath(_settings.chroma_path)
        os.makedirs(path, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        logger.info("ChromaDB initialised at %s", path)
    return _client


def _get_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    """Get or create the documents collection with cosine distance."""
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _make_id(company: str, source_type: str, content: str) -> str:
    """Deterministic document ID — makes repeated ingestion idempotent."""
    key = f"{company}:{source_type}:{content[:120]}"
    return hashlib.sha256(key.encode()).hexdigest()[:24]


def _flatten_meta(
    company: str,
    source_type: str,
    image_url: Optional[str],
    extra: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    ChromaDB metadata values must be str | int | float | bool.
    Flatten lists to comma-separated strings and anything else to str.
    """
    flat: dict[str, Any] = {
        "company": company,
        "source_type": source_type,
        "image_url": image_url or "",
    }
    for k, v in (extra or {}).items():
        if isinstance(v, (str, int, float, bool)):
            flat[k] = v
        elif isinstance(v, list):
            flat[k] = ", ".join(str(i) for i in v)
        else:
            flat[k] = str(v)
    return flat


async def upsert_document(
    client: chromadb.ClientAPI,
    company: str,
    source_type: str,
    content: str,
    embedding: list[float],
    metadata: dict[str, Any] | None = None,
    image_url: Optional[str] = None,
) -> dict:
    """Insert or update a single document embedding."""
    col = _get_collection(client)
    doc_id = _make_id(company, source_type, content)
    flat_meta = _flatten_meta(company, source_type, image_url, metadata)

    col.upsert(
        ids=[doc_id],
        embeddings=[embedding],
        documents=[content],
        metadatas=[flat_meta],
    )
    return {"id": doc_id, "company": company, "source_type": source_type}


async def similarity_search(
    client: chromadb.ClientAPI,
    query_embedding: list[float],
    company: str,
    source_types: list[str] | None = None,
    top_k: int = 10,
) -> list[dict]:
    """
    Cosine similarity search filtered by company and optionally source_type.
    Returns dicts with the same shape as the old Supabase row.
    """
    col = _get_collection(client)

    # Build ChromaDB where filter
    if source_types and len(source_types) == 1:
        where: dict = {"$and": [{"company": company}, {"source_type": source_types[0]}]}
    elif source_types:
        where = {"$and": [{"company": company}, {"source_type": {"$in": source_types}}]}
    else:
        where = {"company": company}

    try:
        results = col.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        logger.warning("ChromaDB query error: %s", exc)
        return []

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    ids = results.get("ids", [[]])[0]

    output = []
    for doc_id, content, meta, dist in zip(ids, docs, metas, distances):
        # ChromaDB cosine distance = 1 - cosine_similarity
        similarity = round(1.0 - float(dist), 4)
        output.append({
            "id": doc_id,
            "company": meta.get("company", company),
            "source_type": meta.get("source_type", ""),
            "content": content,
            "metadata": meta,
            "image_url": meta.get("image_url") or None,
            "similarity": similarity,
        })

    return output


async def get_ingestion_stats(client: chromadb.ClientAPI, company: str) -> dict[str, int]:
    """Return document counts per source_type for a given company."""
    col = _get_collection(client)
    stats: dict[str, int] = {}

    for st in ("patent", "news", "product_image"):
        try:
            result = col.get(
                where={"$and": [{"company": company}, {"source_type": st}]},
                include=[],  # only IDs needed for counting
            )
            stats[st] = len(result.get("ids", []))
        except Exception:
            stats[st] = 0

    return stats


async def bulk_upsert_documents(
    client: chromadb.ClientAPI,
    records: list[dict],
) -> int:
    """Bulk upsert pre-formed document records. Returns count upserted."""
    if not records:
        return 0

    col = _get_collection(client)
    ids, embeddings, documents, metadatas = [], [], [], []

    for r in records:
        company = r.get("company", "")
        source_type = r.get("source_type", "")
        content = r.get("content", "")

        doc_id = _make_id(company, source_type, content)
        flat_meta = _flatten_meta(
            company, source_type, r.get("image_url"), r.get("metadata")
        )

        ids.append(doc_id)
        embeddings.append(r.get("embedding", []))
        documents.append(content)
        metadatas.append(flat_meta)

    col.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    logger.info("ChromaDB: upserted %d documents", len(ids))
    return len(ids)
