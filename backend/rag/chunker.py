"""
Text chunking utilities for RAG ingestion.
Splits large documents into overlapping chunks suitable for embedding.
"""
import re
from dataclasses import dataclass, field
from typing import Any

# Matches "1 ." or "1." at the start of a line (claim number boundary)
_CLAIM_NUM_RE = re.compile(r'(?:^|\n)\s*(\d+)\s*\.\s+', re.MULTILINE)
# Strips [NNNN] paragraph markers from EPO description paragraphs
_PARA_TAG_RE = re.compile(r'^\[\d+\]\s*')
_SECTION_LABELS = ["BACKGROUND", "TECHNICAL FIELD", "SUMMARY", "DETAILED DESCRIPTION",
                   "DESCRIPTION OF DRAWINGS", "CLAIMS", "FIELD OF THE INVENTION"]


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


def _split_claims(claims_array: list[str]) -> list[tuple[int, str]]:
    """Join all claim strings, then split by claim number. Returns [(claim_num, text), ...]."""
    joined = " ".join(claims_array)
    splits = list(_CLAIM_NUM_RE.finditer(joined))
    result = []
    for i, match in enumerate(splits):
        claim_num = int(match.group(1))
        start = match.end()
        end = splits[i + 1].start() if i + 1 < len(splits) else len(joined)
        claim_text = joined[start:end].strip()
        if claim_text:
            result.append((claim_num, claim_text))
    return result


def _chunk_description(desc_array: list[str], base_meta: dict) -> list[Chunk]:
    """Group description paragraphs into ~900-char chunks with section labels."""
    chunks: list[Chunk] = []
    current_parts: list[str] = []
    current_len = 0
    current_label = "DESCRIPTION"
    chunk_idx = 0

    def flush():
        nonlocal current_parts, current_len, chunk_idx
        if not current_parts:
            return
        text = " ".join(current_parts).strip()
        if text:
            chunks.append(Chunk(
                text=text,
                metadata={**base_meta, "section": "description", "section_label": current_label,
                          "chunk_index": chunk_idx},
                chunk_index=chunk_idx,
            ))
            chunk_idx += 1
        current_parts = []
        current_len = 0

    for para in desc_array:
        # Strip paragraph marker tags like [0001]
        clean = _PARA_TAG_RE.sub("", para).strip()
        # Skip blanks, very short lines, and figure captions
        if len(clean) < 40 or clean.upper().startswith("FIG"):
            continue
        # Detect section boundary
        upper = clean.upper()
        for label in _SECTION_LABELS:
            if label in upper and len(clean) < 120:
                flush()
                current_label = label
                break
        if current_len + len(clean) > 900:
            flush()
        current_parts.append(clean)
        current_len += len(clean) + 1

    flush()
    return chunks


def chunk_patent_json(patent: dict, company: str) -> list[Chunk]:
    """
    Optimal chunking for a patent_results.json record.

    Produces:
    - 1 header chunk: patent ID + abstract (always)
    - N claim chunks: one per individual numbered claim (if claims present)
    - M description chunks: grouped by section, ~900 chars each (if description present)
    """
    base_meta: dict[str, Any] = {
        "patent_id": patent["doc_id"],
        "company": company,
        "company_name": company,
        "source_type": "patent",
        "country": patent.get("country", ""),
        "date": patent.get("date", ""),
    }

    chunks: list[Chunk] = []

    # A. Header: patent ID + abstract
    abstract = patent.get("abstract", "").strip()
    header_text = f"Patent {patent['doc_id']}: {abstract}"
    chunks.append(Chunk(
        text=header_text,
        metadata={**base_meta, "section": "abstract", "chunk_index": 0},
        chunk_index=0,
    ))

    # B. Per-claim chunks
    if patent.get("claims"):
        claim_pairs = _split_claims(patent["claims"])
        if not claim_pairs:
            # Fallback: treat whole claims blob as one chunk
            joined = " ".join(patent["claims"]).strip()
            for sub in chunk_text(joined, chunk_size=800, overlap=80,
                                   metadata={**base_meta, "section": "claim", "claim_number": 0}):
                chunks.append(sub)
        else:
            for claim_num, claim_body in claim_pairs:
                claim_str = f"Claim {claim_num}: {claim_body}"
                if len(claim_str) > 800:
                    for sub in chunk_text(claim_str, chunk_size=800, overlap=80,
                                          metadata={**base_meta, "section": "claim",
                                                    "claim_number": claim_num}):
                        chunks.append(sub)
                else:
                    chunks.append(Chunk(
                        text=claim_str,
                        metadata={**base_meta, "section": "claim", "claim_number": claim_num,
                                  "chunk_index": claim_num},
                        chunk_index=claim_num,
                    ))

    # C. Description section chunks
    if patent.get("description"):
        chunks.extend(_chunk_description(patent["description"], base_meta))

    return chunks


def chunk_press_release(record: dict, company: str) -> list[Chunk]:
    """Chunk a press_releases.json record. Uses title + full content body."""
    meta: dict[str, Any] = {
        "company": company,
        "company_name": company,
        "source_type": "news",
        "title": record.get("title", ""),
        "publisher": "",
        "link": record.get("canonical_url", ""),
        "published_at": record.get("date_published", ""),
    }
    combined = f"{record.get('title', '')}\n\n{record.get('content', '')}"
    return chunk_text(combined, chunk_size=800, overlap=100, metadata=meta)


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
