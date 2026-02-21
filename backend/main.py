"""
FastAPI application entry point.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import get_settings
from backend.api.analyze import router as analyze_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)

settings = get_settings()

app = FastAPI(
    title="HackEuropePatent – AI Corporate Transparency Tool",
    description=(
        "Analyzes defense company public claims against EPO patent filings "
        "using a multimodal RAG pipeline and LangGraph multi-agent orchestration."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
