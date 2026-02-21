"""
Text chunking utilities for RAG ingestion.
Splits large documents into overlapping chunks suitable for embedding.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    chunk_index: int = 0


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 150,
    metadata: dict | None = None,
) -> list[Chunk]:
    """
    Split text into overlapping chunks.

    Args:
        text: The source text to chunk.
        chunk_size: Target characters per chunk.
        overlap: Character overlap between adjacent chunks.
        metadata: Optional metadata attached to every chunk.

    Returns:
        List of Chunk objects.
    """
    if not text.strip():
        return []

    meta = metadata or {}
    chunks: list[Chunk] = []
    start = 0
    idx = 0

    while start < len(text):
        end = start + chunk_size
        chunk_text_slice = text[start:end]

        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk_text_slice.rfind(". ")
            if last_period > chunk_size // 2:
                chunk_text_slice = chunk_text_slice[: last_period + 1]

        chunks.append(
            Chunk(
                text=chunk_text_slice.strip(),
                metadata={**meta, "chunk_index": idx},
                chunk_index=idx,
            )
        )
        start += len(chunk_text_slice) - overlap
        idx += 1

    return chunks


def chunk_patent(patent_record) -> list[Chunk]:
    """Create chunks from a PatentRecord, preserving metadata."""
    base_meta = {
        "patent_id": patent_record.patent_id,
        "title": patent_record.title,
        "company_name": patent_record.company_name,
        "source_type": "patent",
        "pdf_url": patent_record.pdf_url,
        "ipc_codes": patent_record.ipc_codes,
    }

    chunks = []
    # Title + abstract as first chunk
    header = f"Patent: {patent_record.title}\n\nAbstract: {patent_record.abstract}"
    chunks.extend(chunk_text(header, metadata={**base_meta, "section": "abstract"}))

    # Claims as additional chunks
    if patent_record.claims:
        chunks.extend(
            chunk_text(
                patent_record.claims,
                metadata={**base_meta, "section": "claims"},
            )
        )

    return chunks


def chunk_news_item(news_item) -> list[Chunk]:
    """Create chunks from a NewsItem."""
    base_meta = {
        "company_name": news_item.company_name,
        "source_type": "news",
        "title": news_item.title,
        "publisher": news_item.publisher,
        "link": news_item.link,
        "published_at": news_item.published_at.isoformat(),
    }
    combined = f"{news_item.title}\n\n{news_item.summary}"
    return chunk_text(combined, metadata=base_meta)
