"""
Standalone analysis runner — iterates over every company and named product in
matched_data.json and writes analysis_results.json.

Prerequisites:
  - backend/rag/matched_data.json must exist (run run_pipeline.py first)
  - Patent entries in matched_data.json must have a "product" field added manually

Steps:
  1. Load matched_data.json
  2. For each company → for each unique product name, call analyze_product()
  3. Write backend/rag/analysis_results.json

Output shape:
  {
    "Lockheed Martin": {
      "F-35": { contradiction_pct, risk_score, contradictions, ... },
      ...
    },
    ...
  }

Run from repo root:
    python -m backend.scripts.run_analysis
"""
import asyncio
import json
import logging
import os
import sys

# ── Bootstrap: ensure repo root is on the path and .env is loaded ────────────
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, _REPO_ROOT)

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

# ── Now import backend modules ────────────────────────────────────────────────
from backend.agents.nodes import analyze_product, _load_matched_all, _group_by_product
from backend.rag.pipeline import PATENT_JSON_COMPANY_MAP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)

_OUT_PATH = os.path.join(os.path.dirname(__file__), "../rag/analysis_results.json")

# Delay between product calls to avoid Gemini rate limits (RPM cap)
_CALL_DELAY = 2.0


async def main() -> None:
    results: dict = {}
    total_products = 0
    done = 0

    # Count total products up front for progress logging
    for json_key, canonical_name in PATENT_JSON_COMPANY_MAP.items():
        entries = _load_matched_all(json_key)
        groups = _group_by_product(entries)
        total_products += len(groups)
        logger.info(
            "Company '%s' — %d products: %s",
            canonical_name, len(groups), list(groups.keys()),
        )

    logger.info("=" * 60)
    logger.info("Starting analysis — %d products across %d companies",
                total_products, len(PATENT_JSON_COMPANY_MAP))
    logger.info("=" * 60)

    for json_key, canonical_name in PATENT_JSON_COMPANY_MAP.items():
        entries = _load_matched_all(json_key)
        if not entries:
            logger.warning("No matched entries for '%s' — skipping.", canonical_name)
            continue

        product_groups = _group_by_product(entries)
        results[canonical_name] = {}

        for product, product_entries in product_groups.items():
            logger.info(
                "[%d/%d] Analysing %s / %s  (%d entries)...",
                done + 1, total_products, canonical_name, product, len(product_entries),
            )
            analysis = await analyze_product(canonical_name, product, product_entries)
            results[canonical_name][product] = analysis
            done += 1

            if "error" in analysis:
                logger.warning(
                    "  ⚠ Error for %s/%s: %s", canonical_name, product, analysis["error"]
                )
            else:
                logger.info(
                    "  risk_score=%s  contradiction_pct=%.1f%%  human_in_loop=%.0f%%",
                    analysis.get("risk_score"),
                    analysis.get("contradiction_pct", 0),
                    analysis.get("risk_mitigation", 0),
                )

            # Rate-limit between Gemini calls
            if done < total_products:
                await asyncio.sleep(_CALL_DELAY)

    logger.info("=" * 60)
    logger.info("Analysis complete — writing analysis_results.json...")
    with open(_OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    size_kb = os.path.getsize(_OUT_PATH) // 1024
    logger.info("Saved → %s (%d KB)", _OUT_PATH, size_kb)
    logger.info("  Companies : %s", list(results.keys()))
    logger.info(
        "  Total products : %d",
        sum(len(v) for v in results.values()),
    )
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
