"""
Multimodal embedding utilities using Google Gemini.

Handles both text and image content, producing vectors for pgvector storage.
"""
import asyncio
import base64
import logging
from typing import Union

import httpx
import google.generativeai as genai
from google.generativeai import types as genai_types

from backend.core.config import get_settings

logger = logging.getLogger(__name__)

_settings = get_settings()
genai.configure(api_key=_settings.google_api_key)


async def embed_text(text: str) -> list[float]:
    """Embed a single text string using Gemini embedding model."""
    if not text.strip():
        return [0.0] * _settings.vector_dimension

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _embed_text_sync, text)
    return result


def _embed_text_sync(text: str) -> list[float]:
    result = genai.embed_content(
        model=_settings.gemini_embedding_model,
        content=text,
        task_type="retrieval_document",
    )
    return result["embedding"]


async def embed_image_url(image_url: str) -> list[float]:
    """
    Download an image from a URL and embed it via Gemini multimodal pipeline.
    We first describe the image with Gemini Vision, then embed that description.
    """
    description = await _describe_image_url(image_url)
    return await embed_text(description)


async def _describe_image_url(image_url: str) -> str:
    """Use Gemini 1.5 Pro to generate a text description of an image URL."""
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            resp = await client.get(image_url)
            resp.raise_for_status()
            image_bytes = resp.content
            content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0]
    except Exception as exc:
        logger.warning("Could not download image %s: %s", image_url, exc)
        return ""

    loop = asyncio.get_event_loop()
    description = await loop.run_in_executor(
        None, _describe_image_sync, image_bytes, content_type
    )
    return description


def _describe_image_sync(image_bytes: bytes, content_type: str) -> str:
    model = genai.GenerativeModel(_settings.gemini_model)
    image_part = {
        "inline_data": {
            "mime_type": content_type,
            "data": base64.b64encode(image_bytes).decode("utf-8"),
        }
    }
    response = model.generate_content(
        [
            image_part,
            (
                "You are a defense technology analyst. Describe this image in detail, "
                "focusing on any weapons systems, surveillance technology, autonomous "
                "systems, or dual-use capabilities visible. Be precise and technical."
            ),
        ]
    )
    return response.text


async def embed_pdf_url(pdf_url: str) -> list[float]:
    """Download and embed a patent PDF via Gemini multimodal."""
    description = await _describe_pdf_url(pdf_url)
    return await embed_text(description)


async def _describe_pdf_url(pdf_url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(pdf_url)
            resp.raise_for_status()
            pdf_bytes = resp.content
    except Exception as exc:
        logger.warning("Could not download PDF %s: %s", pdf_url, exc)
        return ""

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _describe_pdf_sync, pdf_bytes)


def _describe_pdf_sync(pdf_bytes: bytes) -> str:
    model = genai.GenerativeModel(_settings.gemini_model)
    pdf_part = {
        "inline_data": {
            "mime_type": "application/pdf",
            "data": base64.b64encode(pdf_bytes).decode("utf-8"),
        }
    }
    response = model.generate_content(
        [
            pdf_part,
            (
                "You are a forensic patent analyst specializing in defense technology. "
                "Summarize the key claims, technical capabilities, and any dual-use "
                "potential in this patent document. Focus on autonomous systems, "
                "targeting, surveillance, and kill-chain relevance."
            ),
        ]
    )
    return response.text


async def embed_texts_batch(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts concurrently."""
    tasks = [embed_text(t) for t in texts]
    return await asyncio.gather(*tasks)
