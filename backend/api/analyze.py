"""
FastAPI routes for the analysis and ingestion endpoints.
"""
import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.agents.graph import compiled_graph
from backend.agents.state import initial_state
from backend.ingestion.yfinance_client import fetch_company_news, TICKER_MAP
from backend.rag.pipeline import ingest_company
from backend.rag.vector_store import get_chroma, get_ingestion_stats

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["analysis"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    company_name: str = Field(..., example="Lockheed Martin")
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
    Fetches news, patents, and product images, embeds them, and stores in Supabase.
    """
    try:
        stats = await ingest_company(req.company_name)
        return {"status": "ok", "company": req.company_name, "stats": stats}
    except Exception as exc:
        logger.error("Ingestion error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    """
    Run the full LangGraph multi-agent pipeline and return the final state.
    Non-streaming version – waits for all agents to complete.
    """
    state = initial_state(req.company_name, req.user_query)
    try:
        final_state = await compiled_graph.ainvoke(state)
        return {
            "risk_score": final_state["risk_score"],
            "score_drivers": final_state["score_drivers"],
            "products": final_state["products"],
            "contradictions": final_state["contradictions"],
            "stats": final_state.get("stats", {}),
            "investigator_status": final_state["investigator_status"],
            "forensic_status": final_state["forensic_status"],
            "synthesizer_status": final_state["synthesizer_status"],
        }
    except Exception as exc:
        logger.error("Analysis error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/analyze/stream")
async def analyze_stream(req: AnalyzeRequest):
    """
    Streaming version of the analysis endpoint.
    Emits Server-Sent Events (SSE) as each agent completes.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        state = initial_state(req.company_name, req.user_query)

        try:
            async for event in compiled_graph.astream(state, stream_mode="updates"):
                node_name = list(event.keys())[0]
                node_state = event[node_name]
                payload = json.dumps({
                    "node": node_name,
                    "status": node_state.get(f"{node_name}_status", "done"),
                    "data": {k: v for k, v in node_state.items() if k != "embedding"},
                })
                yield f"data: {payload}\n\n"

            # Final state
            final_state = await compiled_graph.ainvoke(initial_state(req.company_name, req.user_query))
            final_payload = json.dumps({
                "node": "complete",
                "status": "done",
                "data": {
                    "risk_score": final_state["risk_score"],
                    "score_drivers": final_state["score_drivers"],
                    "products": final_state["products"],
                    "contradictions": final_state["contradictions"],
                },
            })
            yield f"data: {final_payload}\n\n"

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
