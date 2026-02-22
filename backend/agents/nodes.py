"""
Single-agent product analysis.

Reads directly from backend/rag/matched_data.json — each entry pairs a patent
with its top-3 most relevant press releases (pre-computed by cosine similarity).
Each patent entry is expected to have a "product" field (added manually).

Public API:
  analyze_product(company, product, entries) -> dict
  _load_matched_all(json_key) -> list[dict]
  _group_by_product(entries) -> dict[str, list[dict]]
"""
import json
import logging
import os
import re

import google.generativeai as genai

from backend.core.config import get_settings
from backend.rag.pipeline import PATENT_JSON_COMPANY_MAP

logger = logging.getLogger(__name__)
_settings = get_settings()
genai.configure(api_key=_settings.google_api_key)

# Reverse map: canonical agent name → JSON company key in matched_data.json
_REVERSE_COMPANY_MAP: dict[str, str] = {v: k for k, v in PATENT_JSON_COMPANY_MAP.items()}

# Path to pre-computed matched data — resolved relative to this file
_MATCHED_DATA_PATH = os.path.join(os.path.dirname(__file__), "../rag/matched_data.json")
_matched_cache: dict | None = None


def _get_model() -> genai.GenerativeModel:
    return genai.GenerativeModel(_settings.gemini_model)


def _ensure_cache() -> dict:
    global _matched_cache
    if _matched_cache is None:
        try:
            with open(_MATCHED_DATA_PATH, encoding="utf-8") as f:
                _matched_cache = json.load(f)
        except FileNotFoundError:
            logger.warning(
                "matched_data.json not found at %s — run run_pipeline.py first.",
                _MATCHED_DATA_PATH,
            )
            _matched_cache = {}
    return _matched_cache


def _load_matched_all(json_key: str) -> list[dict]:
    """
    Load all matched entries for a raw JSON company key (e.g. 'LOCKHEED CORP').
    Used by run_analysis.py to iterate over companies without name translation.
    """
    return _ensure_cache().get(json_key, [])


def _load_matched(company_name: str) -> list[dict]:
    """
    Load matched entries by canonical company name (e.g. 'Lockheed Martin').
    Translates via _REVERSE_COMPANY_MAP before looking up in the cache.
    """
    json_key = _REVERSE_COMPANY_MAP.get(company_name, company_name)
    return _load_matched_all(json_key)


def _group_by_product(entries: list[dict]) -> dict[str, list[dict]]:
    """
    Group matched entries by the 'product' field on the patent object.
    Entries without a product field are collected under 'Unknown'.
    """
    groups: dict[str, list[dict]] = {}
    for entry in entries:
        p = entry["patent"]
        # Use manually set "product" first, then fall back to enriched matched_product_name
        product = p.get("product") or p.get("matched_product_name") or "Unknown"
        groups.setdefault(product, []).append(entry)
    return groups


def _build_news_context(entries: list[dict], max_articles: int = 8) -> str:
    """
    Collect unique press releases from top_press_releases across all matched entries.
    Returns a formatted string of the most relevant articles.
    """
    parts: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        for pr in entry.get("top_press_releases", []):
            url = pr.get("url", pr.get("title", ""))
            if url in seen:
                continue
            seen.add(url)
            parts.append(
                f"[{pr.get('date', '')[:10]}] {pr.get('title', '')}\n"
                f"Source: {pr.get('source', '')}  |  Relevance: {pr.get('similarity', 0):.3f}\n"
                f"{pr.get('summary', '')[:600]}"
            )
            if len(parts) >= max_articles:
                return "\n\n".join(parts)
    return "\n\n".join(parts)


def _build_patent_context(entries: list[dict], max_patents: int = 10) -> str:
    """
    Format patent entries (abstract + claims preview) for the analysis prompt.
    Prioritises patents that have full claims text.
    """
    sorted_entries = sorted(
        entries, key=lambda e: bool(e["patent"].get("claims")), reverse=True
    )
    parts: list[str] = []
    for i, entry in enumerate(sorted_entries[:max_patents], 1):
        p = entry["patent"]
        claims_preview = ""
        if p.get("claims"):
            claims_preview = " ".join(p["claims"])[:600]

        product_line = ""
        if p.get("matched_product_name"):
            product_line = (
                f"Matched product: {p['matched_product_name']}\n"
                f"Product description: {p.get('matched_product_description', '')[:300]}\n"
            )

        desc_preview = ""
        if p.get("description"):
            desc_preview = " ".join(p["description"][:5])[:400]

        parts.append(
            f"[Patent {i}] {p['doc_id']} (published {p.get('date', 'unknown')})\n"
            f"{product_line}"
            f"Abstract: {p.get('abstract', '')[:400]}\n"
            f"Description excerpt: {desc_preview if desc_preview else '(none)'}\n"
            f"Claims: {claims_preview if claims_preview else '(abstract only)'}"
        )
    return "\n\n".join(parts)


async def analyze_product(
    company: str,
    product: str,
    entries: list[dict],
) -> dict:
    """
    Given matched patent+PR entries for one named product, produce a structured
    risk analysis in a single Gemini call.

    Returns a dict with keys:
      product, company, contradiction_pct, risk_score, score_drivers,
      contradictions, cost_analysis, human_in_loop_pct, risk_mitigation
    On error returns a dict with an 'error' key and safe defaults.
    """
    news_text = _build_news_context(entries)
    patent_text = _build_patent_context(entries)
    patent_ids = [e["patent"]["doc_id"] for e in entries[:10]]

    if not news_text:
        news_text = "(No press release data available for this product)"
    if not patent_text:
        patent_text = "(No patent data available for this product)"

    prompt = f"""You are a defense industry analyst producing a structured transparency risk report.

Company: {company}
Product: {product}

== Press Releases (matched to patents by semantic relevance) ==
{news_text}

== Patent Evidence ==
{patent_text}

Task: Analyse the gap between public marketing claims and actual patent-evidenced capabilities.
Produce a JSON object with EXACTLY this schema (no markdown fences, no extra keys):

{{
  "product": "{product}",
  "company": "{company}",
  "contradiction_pct": <float 0-100: % of public claims contradicted or undermined by patent evidence>,
  "risk_score": <int 0-100: 0=fully transparent civilian, 100=severe contradiction + autonomous kill chain>,
  "score_drivers": [
    "<reason 1, max 15 words>",
    "<reason 2, max 15 words>",
    "<reason 3, max 15 words>"
  ],
  "contradictions": [
    {{
      "claim": "<exact or paraphrased public claim from press releases>",
      "evidence": "<patent or technical evidence that contradicts it>",
      "why_it_matters": "<humanitarian or ethical significance, 1-2 sentences>",
      "sources": ["<patent ID from available list>"]
    }}
  ],
  "cost_analysis": {{
    "unit_cost": "<e.g. '$2.1M per unit' or 'not disclosed'>",
    "programme_cost": "<e.g. '$14B programme' or 'not disclosed'>",
    "source": "<press release title or date, or 'estimated'>"
  }},
  "human_in_loop_pct": <float 0-50: 50=always human decision required, 0=fully autonomous kill chain>,
  "risk_mitigation_pct": <float 0-50: 50=always has a risk mitagated circumstance for prevention, 0=no backup risk mitigation plans at all>"
}}

Rules:
- contradiction_pct: contradictions found ÷ total claims extracted × 100
- Include 3–7 contradictions, prioritise the most serious humanitarian implications
- human_in_loop_pct: base on specific patent language (e.g. "autonomous", "operator approval", "without human intervention")
- risk_mitigation: grounded in actual patent text, not aspirational marketing language
- Output ONLY valid JSON — no markdown, no preamble, no explanation

Available patent IDs for source citations: {patent_ids}"""

    raw = ""
    try:
        model = _get_model()
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Strip markdown fences if the model adds them anyway
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        payload = json.loads(raw)

        return {
            "product": payload.get("product", product),
            "company": payload.get("company", company),
            "contradiction_pct": float(payload.get("contradiction_pct", 0)),
            "risk_score": int(payload.get("risk_score", 50)),
            "score_drivers": payload.get("score_drivers", [])[:3],
            "contradictions": payload.get("contradictions", []),
            "cost_analysis": payload.get("cost_analysis", {}),
            "risk_mitigation": float(payload.get("human_in_loop_pct", 30)) + float(payload.get("risk_mitigation_pct", 30)),
        }

    except json.JSONDecodeError as exc:
        logger.error(
            "analyze_product JSON parse error for %s/%s: %s | raw: %.500s",
            company, product, exc, raw,
        )
        return {
            "product": product,
            "company": company,
            "contradiction_pct": 0.0,
            "risk_score": 50,
            "score_drivers": ["Analysis completed with parsing errors"],
            "contradictions": [],
            "cost_analysis": {},
            "risk_mitigation": 50.0,
            "error": f"JSON parse error: {exc}",
        }
    except Exception as exc:
        logger.error("analyze_product error for %s/%s: %s", company, product, exc)
        return {
            "product": product,
            "company": company,
            "contradiction_pct": 0.0,
            "risk_score": 50,
            "score_drivers": [],
            "contradictions": [],
            "cost_analysis": {},
            "risk_mitigation": 50.0,
            "error": str(exc),
        }
