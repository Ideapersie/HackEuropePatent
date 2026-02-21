"""
Shared state definition for the LangGraph multi-agent pipeline.
All agents read from and write to this TypedDict.
"""
from typing import Any, Optional
from typing_extensions import TypedDict


class Contradiction(TypedDict):
    claim: str
    evidence: str
    why_it_matters: str
    sources: list[str]


class AnalysisState(TypedDict):
    # Input
    company_name: str
    user_query: str

    # Retrieved context (populated during graph execution)
    news_context: list[dict[str, Any]]        # Retrieved news/press-release chunks
    patent_context: list[dict[str, Any]]      # Retrieved patent chunks
    product_images: list[dict[str, Any]]      # Product image records

    # Investigator output
    public_claims: str                         # Extracted ethical/marketing claims
    investigator_status: str                   # "running" | "done" | "error"

    # Forensic output
    technical_capabilities: str               # Actual capabilities from patents
    dual_use_risks: str                        # Identified dual-use risks
    forensic_status: str                       # "running" | "done" | "error"

    # Synthesizer output
    risk_score: int
    score_drivers: list[str]
    products: list[str]                        # Image URLs
    contradictions: list[Contradiction]
    synthesizer_status: str                    # "running" | "done" | "error"

    # Ingestion stats
    stats: dict[str, int]                      # e.g. {"patent": 30, "news": 25, "product_image": 3}

    # Error tracking
    error: Optional[str]


def initial_state(company_name: str, user_query: str = "") -> AnalysisState:
    return AnalysisState(
        company_name=company_name,
        user_query=user_query or f"Analyze defense ethics and dual-use risks for {company_name}",
        news_context=[],
        patent_context=[],
        product_images=[],
        public_claims="",
        investigator_status="pending",
        technical_capabilities="",
        dual_use_risks="",
        forensic_status="pending",
        risk_score=0,
        score_drivers=[],
        products=[],
        contradictions=[],
        synthesizer_status="pending",
        stats={},
        error=None,
    )
