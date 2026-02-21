"""
LangGraph agent node implementations.

Each node is a pure async function that takes an AnalysisState and returns
a partial state dict (merged by LangGraph into the full state).
"""
import json
import logging
import re
from typing import Any

import google.generativeai as genai

from backend.core.config import get_settings
from backend.agents.state import AnalysisState, Contradiction
from backend.rag.embeddings import embed_text
from backend.rag.vector_store import get_supabase, similarity_search

logger = logging.getLogger(__name__)
_settings = get_settings()
genai.configure(api_key=_settings.google_api_key)


def _get_model() -> genai.GenerativeModel:
    return genai.GenerativeModel(_settings.gemini_model)


def _format_context(chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks[:8], 1):
        meta = c.get("metadata") or {}
        parts.append(
            f"[Source {i}] ({c.get('source_type', 'unknown')}) "
            f"{meta.get('title', '')} — {c.get('content', '')[:600]}"
        )
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Retriever helper (shared by all nodes)
# ---------------------------------------------------------------------------

async def _retrieve(
    company: str,
    query: str,
    source_types: list[str],
    top_k: int = 8,
) -> list[dict]:
    supabase = get_supabase()
    query_emb = await embed_text(query)
    return await similarity_search(
        supabase, query_emb, company, source_types=source_types, top_k=top_k
    )


# ---------------------------------------------------------------------------
# Node 1 – Investigator
# ---------------------------------------------------------------------------

async def investigator_node(state: AnalysisState) -> dict:
    """
    Retrieves news/press-release chunks and product images,
    then uses Gemini to extract the company's public ethical claims.
    """
    company = state["company_name"]
    query = state["user_query"]

    try:
        news_ctx = await _retrieve(company, query, ["news"], top_k=8)
        img_ctx = await _retrieve(company, query, ["product_image"], top_k=5)

        context_text = _format_context(news_ctx + img_ctx)

        prompt = f"""You are an Investigator agent specializing in corporate ethics and defense industry PR.

Company: {company}
User Query: {query}

== Press Releases & News Context ==
{context_text}

Task:
1. Extract every explicit or implicit ethical, environmental, and humanitarian claim the company makes in these materials.
2. Identify the marketing language used to describe their defense products (e.g., "precision", "protecting lives", "defensive systems").
3. List named products and their stated purpose.

Return your findings as plain text with clear bullet points. Be exhaustive."""

        model = _get_model()
        response = model.generate_content(prompt)
        public_claims = response.text

        return {
            "news_context": news_ctx,
            "product_images": img_ctx,
            "public_claims": public_claims,
            "investigator_status": "done",
        }

    except Exception as exc:
        logger.error("Investigator node error: %s", exc)
        return {
            "investigator_status": "error",
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Node 2 – Forensic
# ---------------------------------------------------------------------------

async def forensic_node(state: AnalysisState) -> dict:
    """
    Retrieves patent chunks and analyzes actual technical capabilities
    against known dual-use weapon system patterns.
    """
    company = state["company_name"]
    query = state["user_query"]
    public_claims = state.get("public_claims", "")

    try:
        patent_ctx = await _retrieve(company, query, ["patent"], top_k=10)
        context_text = _format_context(patent_ctx)

        prompt = f"""You are a Forensic Analyst specializing in defense technology patents and dual-use risk assessment.

Company: {company}
Public Claims Summary:
{public_claims[:1000]}

== Patent Context ==
{context_text}

Task:
1. Identify the actual technical capabilities described in these patents (autonomous targeting, AI-guided weapons, surveillance, electronic warfare, etc.).
2. Classify any dual-use potential: could civilian technology claims mask military kill-chain relevance?
3. Identify IPC codes and explain their military significance.
4. Note specific technical capabilities that contradict or undermine the company's public ethical claims.

Return a structured analysis with:
- Technical Capabilities (bullet list)
- Dual-Use Risks (bullet list)
- Key Patent Evidence (brief quotes or paraphrases from claims)"""

        model = _get_model()
        response = model.generate_content(prompt)
        full_text = response.text

        # Split into capabilities and risks sections
        capabilities = full_text
        risks = ""
        if "Dual-Use Risks" in full_text:
            parts = full_text.split("Dual-Use Risks", 1)
            capabilities = parts[0]
            risks = "Dual-Use Risks" + parts[1]

        return {
            "patent_context": patent_ctx,
            "technical_capabilities": capabilities,
            "dual_use_risks": risks,
            "forensic_status": "done",
        }

    except Exception as exc:
        logger.error("Forensic node error: %s", exc)
        return {
            "forensic_status": "error",
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Node 3 – Synthesizer
# ---------------------------------------------------------------------------

async def synthesizer_node(state: AnalysisState) -> dict:
    """
    Compares Investigator and Forensic findings, produces the final
    structured JSON payload: risk_score, score_drivers, products, contradictions.
    """
    company = state["company_name"]
    public_claims = state.get("public_claims", "")
    technical_capabilities = state.get("technical_capabilities", "")
    dual_use_risks = state.get("dual_use_risks", "")
    patent_ctx = state.get("patent_context", [])
    img_ctx = state.get("product_images", [])

    # Collect product image URLs
    product_image_urls = [
        r["image_url"] for r in img_ctx if r.get("image_url")
    ]

    # Build source references
    patent_sources = list({
        r.get("metadata", {}).get("patent_id", "") or r.get("image_url", "")
        for r in patent_ctx
        if r.get("metadata", {}).get("patent_id") or r.get("image_url")
    })[:5]

    prompt = f"""You are a Synthesizer agent producing a corporate transparency risk report.

Company: {company}

== Public Claims (from press releases & marketing) ==
{public_claims[:2000]}

== Actual Technical Capabilities (from patent analysis) ==
{technical_capabilities[:2000]}

== Dual-Use Risks Identified ==
{dual_use_risks[:1000]}

Task:
Produce a structured JSON object with EXACTLY this schema:

{{
  "risk_score": <integer 0-100>,
  "score_drivers": [
    "<bullet 1: key reason for score, max 15 words>",
    "<bullet 2: key reason for score, max 15 words>",
    "<bullet 3: key reason for score, max 15 words>"
  ],
  "contradictions": [
    {{
      "claim": "<exact or paraphrased public claim>",
      "evidence": "<patent or technical evidence that contradicts it>",
      "why_it_matters": "<humanitarian or ethical significance>",
      "sources": ["<patent ID or URL>"]
    }}
  ]
}}

Rules:
- risk_score: 0=fully transparent/civilian, 100=severe contradiction/high dual-use risk
- Include 3-7 contradictions
- Be specific, cite patent IDs when possible
- Output ONLY valid JSON, no markdown fences, no preamble

Patent source IDs available: {patent_sources}"""

    try:
        model = _get_model()
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Strip markdown fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        payload = json.loads(raw)

        risk_score = int(payload.get("risk_score", 50))
        score_drivers = payload.get("score_drivers", [])[:3]
        contradictions: list[Contradiction] = payload.get("contradictions", [])

        return {
            "risk_score": risk_score,
            "score_drivers": score_drivers,
            "products": product_image_urls,
            "contradictions": contradictions,
            "synthesizer_status": "done",
        }

    except json.JSONDecodeError as exc:
        logger.error("Synthesizer JSON parse error: %s | raw: %s", exc, raw[:500])
        return {
            "risk_score": 50,
            "score_drivers": ["Analysis completed with parsing errors"],
            "products": product_image_urls,
            "contradictions": [],
            "synthesizer_status": "error",
            "error": f"JSON parse error: {exc}",
        }
    except Exception as exc:
        logger.error("Synthesizer node error: %s", exc)
        return {
            "synthesizer_status": "error",
            "error": str(exc),
        }
