"""
FastAPI routes for the analysis and ingestion endpoints.
"""
import json
import logging
import os
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.ingestion.yfinance_client import fetch_company_news, TICKER_MAP
from backend.rag.pipeline import ingest_company, ingest_patents_from_json, ingest_press_releases_from_json
from backend.rag.vector_store import get_chroma, get_ingestion_stats

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["analysis"])

_ANALYSIS_RESULTS_PATH = os.path.join(
    os.path.dirname(__file__), "../rag/analysis_results.json"
)
_RANKED_RESULTS_PATH = os.path.join(
    os.path.dirname(__file__), "../rag/ranked_results.json"
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    company_name: str = Field(default="", example="Lockheed Martin")
    user_query: str = Field(
        default="",
        example="Analyze ethical contradictions between public claims and patent filings",
    )


class IngestRequest(BaseModel):
    company_name: str = Field(..., example="Lockheed Martin")


class StatsResponse(BaseModel):
    company_name: str
    stats: dict[str, int]


class NewsItemResponse(BaseModel):
    title: str
    publisher: str
    link: str
    published_at: str  # ISO-8601 string — datetime is not directly JSON-serializable
    summary: str
    ticker: str
    company_name: str
    source_type: str


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_rankings_map() -> dict[str, dict]:
    """
    Load ranked_results.json and return a dict keyed by company name.
    Returns {} silently if the file does not exist yet.
    """
    try:
        with open(_RANKED_RESULTS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return {r["company"]: r for r in data.get("rankings", [])}
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


def _reshape_company(company: str, products: dict, ranking: dict | None) -> dict:
    """
    Flatten per-product analysis into one AnalysisResult-shaped dict that matches
    the frontend's existing TypeScript interface exactly:

      { risk_score, score_drivers, products, contradictions, stats,
        investigator_status, forensic_status, synthesizer_status }

    stats carries both numeric aggregates (contradiction_pct, risk_mitigation,
    product_count, avg_unit_cost_usd) and A→F grade strings (grade_overall,
    grade_contradiction, grade_safety, grade_risk_mitigation, grade_cost).
    """
    product_list = list(products.values())
    if not product_list:
        return {
            "risk_score": 0,
            "score_drivers": [],
            "products": [],
            "contradictions": [],
            "stats": {},
            "investigator_status": "done",
            "forensic_status": "done",
            "synthesizer_status": "done",
        }

    # ── risk_score: mean across all products ──────────────────────────────────
    risk_score = round(
        sum(float(p.get("risk_score", 50)) for p in product_list) / len(product_list)
    )

    # ── score_drivers: from the highest-risk product ──────────────────────────
    top_product = max(product_list, key=lambda p: float(p.get("risk_score", 0)))
    score_drivers = top_product.get("score_drivers", [])[:3]

    # ── contradictions: flatten + deduplicate by claim prefix ─────────────────
    seen_claims: set[str] = set()
    contradictions: list[dict] = []
    for p in product_list:
        for c in p.get("contradictions", []):
            key = c.get("claim", "")[:80]
            if key not in seen_claims:
                seen_claims.add(key)
                contradictions.append(c)

    # ── aggregate numeric metrics ─────────────────────────────────────────────
    contradiction_pct = (
        sum(float(p.get("contradiction_pct", 0)) for p in product_list) / len(product_list)
    )
    risk_mitigation = (
        sum(float(p.get("risk_mitigation", 50)) for p in product_list) / len(product_list)
    )

    stats: dict = {
        "contradiction_pct": round(contradiction_pct, 1),
        "risk_mitigation":   round(risk_mitigation, 1),
        "product_count":     len(product_list),
    }

    # ── attach A→F grades from ranked_results if available ───────────────────
    if ranking:
        grades = ranking.get("grades", {})
        overall = ranking.get("overall", "")
        stats["grade_overall"]         = overall
        stats["grade_contradiction"]   = grades.get("contradiction", "")
        stats["grade_safety"]          = grades.get("safety", "")
        stats["grade_risk_mitigation"] = grades.get("risk_mitigation", "")
        stats["grade_cost"]            = grades.get("cost", "")
        agg = ranking.get("aggregated_scores", {})
        stats["avg_unit_cost_usd"]     = agg.get("avg_unit_cost_usd") or 0

    return {
        "risk_score":          risk_score,
        "score_drivers":       score_drivers,
        "products":            list(products.keys()),
        "contradictions":      contradictions,
        "stats":               stats,
        "investigator_status": "done",
        "forensic_status":     "done",
        "synthesizer_status":  "done",
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/companies")
async def list_companies():
    """Return the list of supported companies."""
    return {"companies": list(TICKER_MAP.keys())}


@router.get("/news/{company_name}", response_model=list[NewsItemResponse])
async def get_news(company_name: str, max_items: int = 20):
    """
    Fetch recent press releases and news filings for a company via yfinance.

    Example: GET /api/news/Lockheed%20Martin?max_items=5
    """
    if company_name not in TICKER_MAP:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown company '{company_name}'. Supported: {list(TICKER_MAP.keys())}",
        )
    try:
        items = await fetch_company_news(company_name, max_items=max_items)
    except Exception as exc:
        logger.error("News fetch error for %s: %s", company_name, exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return [
        NewsItemResponse(
            title=item.title,
            publisher=item.publisher,
            link=item.link,
            published_at=item.published_at.isoformat(),
            summary=item.summary,
            ticker=item.ticker,
            company_name=item.company_name,
            source_type=item.source_type,
        )
        for item in items
    ]


@router.get("/stats/{company_name}", response_model=StatsResponse)
async def get_stats(company_name: str):
    """Return ingestion statistics for a company."""
    chroma = get_chroma()
    stats = await get_ingestion_stats(chroma, company_name)
    return StatsResponse(company_name=company_name, stats=stats)


@router.post("/ingest")
async def ingest(req: IngestRequest):
    """
    Trigger full ingestion pipeline for a company.
    Fetches news, patents, and product images, embeds them, and stores in ChromaDB.
    """
    try:
        stats = await ingest_company(req.company_name)
        return {"status": "ok", "company": req.company_name, "stats": stats}
    except Exception as exc:
        logger.error("Ingestion error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ingest-json")
async def ingest_json():
    """
    Ingest patent_results.json and press_releases.json from the rag/ directory into ChromaDB.
    Patents are chunked per individual claim and description section.
    Press releases are company-detected by keyword and chunked as full articles.
    """
    try:
        patent_stats = await ingest_patents_from_json()
        news_stats = await ingest_press_releases_from_json()
        return {"status": "ok", "patents": patent_stats, "news": news_stats}
    except Exception as exc:
        logger.error("JSON ingestion error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    """
    Return pre-computed product analysis reshaped into the frontend AnalysisResult format.

    If company_name is provided, returns a single AnalysisResult for that company
    (products aggregated: mean risk_score, flattened contradictions, grade strings in stats).
    If company_name is empty, returns all companies as { results: { company: AnalysisResult } }.

    Run `python -m backend.scripts.run_analysis` to (re)generate analysis_results.json.
    Run `python -m backend.scripts.rank_results` to (re)generate ranked_results.json (grades).
    """
    try:
        with open(_ANALYSIS_RESULTS_PATH, encoding="utf-8") as f:
            all_results = json.load(f)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=(
                "analysis_results.json not found. "
                "Run `python -m backend.scripts.run_analysis` first."
            ),
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"analysis_results.json is malformed: {exc}")

    rankings_map = _load_rankings_map()

    if req.company_name:
        if req.company_name not in all_results:
            raise HTTPException(
                status_code=404,
                detail=f"No results for company '{req.company_name}'. "
                       f"Available: {list(all_results.keys())}",
            )
        products = all_results[req.company_name]
        ranking = rankings_map.get(req.company_name)
        return _reshape_company(req.company_name, products, ranking)

    # No company filter — return all companies reshaped
    return {
        "results": {
            company: _reshape_company(company, products, rankings_map.get(company))
            for company, products in all_results.items()
        }
    }


@router.post("/analyze/run")
async def run_analysis():
    """
    Trigger the full product-by-product analysis loop and write analysis_results.json.
    This runs synchronously (may take several minutes for all products).
    For large datasets, prefer running `python -m backend.scripts.run_analysis` directly.
    """
    try:
        from backend.scripts.run_analysis import main as _run_main
        await _run_main()
        return {"status": "ok", "message": "analysis_results.json written successfully."}
    except Exception as exc:
        logger.error("run_analysis error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/analyze/stream")
async def analyze_stream(req: AnalyzeRequest):
    """
    Streaming analysis endpoint.

    Emits Server-Sent Events using AgentStreamEvent shape { node, status, data }.
    - Each product completion: node="synthesizer", data={ products: [<name>] }
    - Company complete: node="complete", data=<full AnalysisResult for that company>
    - Error: node="error", message=<str>

    The frontend's streamAnalysis() generator and CompanyData state machinery consume
    this directly without any changes.
    """
    from backend.agents.nodes import _load_matched_all, _group_by_product, analyze_product
    from backend.rag.pipeline import PATENT_JSON_COMPANY_MAP

    async def event_generator() -> AsyncGenerator[str, None]:
        rankings_map = _load_rankings_map()

        try:
            if req.company_name:
                reverse = {v: k for k, v in PATENT_JSON_COMPANY_MAP.items()}
                json_key = reverse.get(req.company_name, req.company_name)
                company_map = {json_key: req.company_name}
            else:
                company_map = PATENT_JSON_COMPANY_MAP

            for json_key, canonical_name in company_map.items():
                entries = _load_matched_all(json_key)
                product_groups = _group_by_product(entries)
                accumulated: dict[str, dict] = {}

                for product, product_entries in product_groups.items():
                    analysis = await analyze_product(canonical_name, product, product_entries)
                    accumulated[product] = analysis

                    # Lightweight per-product ping so the frontend sees progress
                    ping = json.dumps({
                        "node": "synthesizer",
                        "status": "done",
                        "data": {"products": list(accumulated.keys())},
                    })
                    yield f"data: {ping}\n\n"

                # Emit the full reshaped company result as the "complete" event
                ranking = rankings_map.get(canonical_name)
                reshaped = _reshape_company(canonical_name, accumulated, ranking)
                final = json.dumps({
                    "node": "complete",
                    "status": "done",
                    "data": reshaped,
                })
                yield f"data: {final}\n\n"

        except Exception as exc:
            error_payload = json.dumps({"node": "error", "status": "error", "message": str(exc)})
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/rankings")
async def get_rankings(company: str = ""):
    """
    Return A→F letter grades per company aggregated across all their products.

    Grades are computed for 4 metrics:
      - contradiction : % of public claims contradicted by patent evidence
      - risk_mitigation : composite safety/mitigation score (inverted — lower = worse)
      - safety : overall risk score from patent analysis
      - cost : average unit cost (higher = worse; 'not disclosed' penalised)

    Grades are relative (percentile-based across all companies in the dataset).
    overall = the single worst grade across all 4 metrics.

    Optionally filter by company name (case-insensitive substring match).

    Run `python -m backend.scripts.rank_results` to (re)generate ranked_results.json.
    """
    try:
        with open(_RANKED_RESULTS_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=(
                "ranked_results.json not found. "
                "Run `python -m backend.scripts.rank_results` first."
            ),
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"ranked_results.json is malformed: {exc}")

    if company:
        data["rankings"] = [
            r for r in data["rankings"]
            if company.lower() in r["company"].lower()
        ]
    return data
