"""
Ranking step — reads analysis_results.json, aggregates per company across all products,
assigns A→F letter grades for 4 metrics, and writes ranked_results.json.

Grading is score-based (absolute thresholds), not percentile/relative:

  Contradiction  : contradiction_pct (0–100, higher = worse)
  Risk Mitigation: risk_mitigation composite (0–100, higher = better → inverted)
  Safety         : risk_score (0–100, higher = worse)
  Cost           : unit_cost normalised to 0–100 scale (higher cost = worse)

Grade thresholds (score 0–100, higher = worse):
  A :  0–19
  B : 20–39
  C : 40–59
  D : 60–69
  E : 70–79
  F : 80–100

Overall = average of the 4 numeric scores → same thresholds applied to that average.

Run from repo root:
    python -m backend.scripts.rank_results
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

# ── Bootstrap: ensure repo root is on the path ───────────────────────────────
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, _REPO_ROOT)

_RAG_DIR  = os.path.join(os.path.dirname(__file__), "../rag")
_IN_PATH  = os.path.join(_RAG_DIR, "analysis_results.json")
_OUT_PATH = os.path.join(_RAG_DIR, "ranked_results.json")


def _parse_unit_cost(unit_cost_str: str) -> float | None:
    """
    Parse a unit cost string like '$82.5M per unit' or '$2.1B' into a float (USD).
    Returns None if the string is 'not disclosed', empty, or unparseable.
    """
    s = (unit_cost_str or "").lower().strip()
    if not s or "not disclosed" in s or s == "unknown":
        return None
    m = re.search(r"\$?([\d,]+\.?\d*)\s*([bmk])?", s)
    if not m:
        return None
    num = float(m.group(1).replace(",", ""))
    suffix = (m.group(2) or "").lower()
    if suffix == "b":
        num *= 1e9
    elif suffix == "m":
        num *= 1e6
    elif suffix == "k":
        num *= 1e3
    return num


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


_COST_MAX_USD = 1_000_000.0  # $1M → 100 on the normalised scale


def _normalise_cost(cost_usd: float) -> float:
    """
    Map a raw USD cost to a 0–100 score (higher = worse).
    Uses log scale capped at $1M = 100.
    Returns None if cost is unknown (zero sentinel).
    """
    import math
    if cost_usd <= 0:
        return None
    score = (math.log10(cost_usd) / math.log10(_COST_MAX_USD)) * 100.0
    return min(score, 100.0)


def _grade(score: float) -> str:
    """Convert a 0–100 score (higher = worse) to an A–F letter grade."""
    if score < 40:
        return "A"
    if score < 60:
        return "B"
    if score < 70:
        return "C"
    if score < 80:
        return "D"
    if score < 90:
        return "E"
    return "F"


def _overall_grade(scores: dict[str, float]) -> str:
    """Return grade for the average of all 4 metric scores."""
    avg = _mean(list(scores.values()))
    return _grade(avg)


def main() -> None:
    with open(_IN_PATH, encoding="utf-8") as f:
        analysis: dict = json.load(f)

    # ── First pass: collect all known unit costs for sentinel calculation ─────
    all_known_costs: list[float] = []
    for products in analysis.values():
        for data in products.values():
            cost = _parse_unit_cost(data.get("cost_analysis", {}).get("unit_cost", ""))
            if cost is not None:
                all_known_costs.append(cost)

    # "not disclosed" → 75th percentile of known costs (penalised but not worst)
    if all_known_costs:
        sorted_costs = sorted(all_known_costs)
        p75_cost = sorted_costs[int(len(sorted_costs) * 0.75)]
    else:
        p75_cost = 0.0

    # ── Second pass: aggregate per company ───────────────────────────────────
    company_data: list[dict] = []

    for company, products in analysis.items():
        product_list = list(products.values())
        if not product_list:
            continue

        contradiction_vals = [float(p.get("contradiction_pct", 0)) for p in product_list]

        # risk_mitigation is already a composite (0–100, higher = better).
        # Invert so that higher = worse, consistent with the other three metrics.
        risk_mit_raw   = [float(p.get("risk_mitigation", 50)) for p in product_list]
        risk_mit_vals  = [100.0 - v for v in risk_mit_raw]

        safety_vals = [float(p.get("risk_score", 50)) for p in product_list]

        cost_raw = [
            _parse_unit_cost(p.get("cost_analysis", {}).get("unit_cost", "")) or p75_cost
            for p in product_list
        ]

        avg_cost_usd = _mean(cost_raw) if any(v > 0 for v in cost_raw) else 0.0
        cost_score = _normalise_cost(avg_cost_usd)  # None if no cost data

        company_data.append({
            "company": company,
            "product_count": len(product_list),
            # 0–100 scores (higher = worse) used for grading; cost may be None
            "scores": {
                "contradiction":   _mean(contradiction_vals),
                "risk_mitigation": _mean(risk_mit_vals),      # already inverted
                "safety":          _mean(safety_vals),
                "cost":            cost_score,
            },
            # Human-readable display values (original scale)
            "agg_display": {
                "contradiction_pct":  _mean(contradiction_vals),
                "risk_mitigation":    _mean(risk_mit_raw),
                "risk_score":         _mean(safety_vals),
                "avg_unit_cost_usd":  avg_cost_usd if avg_cost_usd > 0 else None,
            },
        })
        

    # ── Apply score-based grades directly (no percentile needed) ─────────────
    rankings = []
    for cd in company_data:
        scores = cd["scores"]
        grades = {}
        scored_vals = []
        for m, v in scores.items():
            if v is None:
                grades[m] = "N/A"
            else:
                grades[m] = _grade(v)
                scored_vals.append(v)
        overall_score = round(_mean(scored_vals), 1) if scored_vals else 0.0
        overall = _grade(overall_score) if scored_vals else "N/A"
        rankings.append({
            "company": cd["company"],
            "grades": grades,
            "overall": overall,
            "overall_score": overall_score,
            "aggregated_scores": cd["agg_display"],
            "product_count": cd["product_count"],
        })

    # Sort: worst overall score first (highest = worst), then by safety score descending
    rankings.sort(key=lambda r: (
        -r["overall_score"],
        -r["aggregated_scores"]["risk_score"],
    ))

    output = {
        "rankings": rankings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_companies": len(rankings),
    }

    with open(_OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Written → {_OUT_PATH}  ({len(rankings)} companies ranked)\n")
    print(f"{'Company':<22} {'Overall':<9} {'Contradiction':<15} {'Safety':<9} {'Risk Mit.':<11} {'Cost'}")
    print("-" * 75)
    for r in rankings:
        g = r["grades"]
        print(
            f"{r['company']:<22} {r['overall']:<9} {g['contradiction']:<15} "
            f"{g['safety']:<9} {g['risk_mitigation']:<11} {g['cost']}"
        )


if __name__ == "__main__":
    main()
