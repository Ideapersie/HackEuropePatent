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

    # Investigator output
    public_claims: str                         # Extracted ethical/marketing claims
    investigator_status: str                   # "running" | "done" | "error"

    # Forensic output
    technical_capabilities: str               # Actual capabilities from patents
    dual_use_risks: str                        # Identified dual-use risks
    forensic_status: str                       # "running" | "done" | "error"

    # Synthesizer output
    contradiction_pct: float                   # 0–100: % of public claims contradicted by patents
    risk_score: int                            # 0–100 overall risk score
    score_drivers: list[str]                   # Key reasons for the risk score
    contradictions: list[Contradiction]        # Individual claim vs. evidence pairs
    cost_analysis: dict[str, Any]             # unit_cost, programme_cost, source
    human_in_loop_pct: float                   # 0–100: estimated % human oversight in weapon systems
    risk_mitigation: list[str]                 # Stated safeguards / safety mechanisms
    synthesizer_status: str                    # "running" | "done" | "error"

    # Error tracking
    error: Optional[str]


def initial_state(company_name: str, user_query: str = "") -> AnalysisState:
    return AnalysisState(
        company_name=company_name,
        user_query=user_query or f"Analyze defense ethics and dual-use risks for {company_name}",
        public_claims="",
        investigator_status="pending",
        technical_capabilities="",
        dual_use_risks="",
        forensic_status="pending",
        contradiction_pct=0.0,
        risk_score=0,
        score_drivers=[],
        contradictions=[],
        cost_analysis={},
        human_in_loop_pct=0.0,
        risk_mitigation=[],
        synthesizer_status="pending",
        error=None,
    )
