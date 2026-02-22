"""
Standalone pipeline runner — matches patents to press releases and writes matched_data.json.

Steps:
  1. Embed all 200 press releases in rate-limited batches (10 concurrent, 1s pause between)
  2. For each patent, embed its abstract and rank all press releases by cosine similarity
  3. Attach the top-3 most relevant press releases to each patent record
  4. Write backend/rag/matched_data.json  (human-readable, used as agent input)

Run from repo root:
    python -m backend.scripts.run_pipeline
"""
import asyncio
import json
import logging
import math
import os
import sys

# ── Bootstrap: ensure repo root is on the path and .env is loaded ────────────
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, _REPO_ROOT)

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

# ── Now import backend modules (settings will pick up the loaded env vars) ───
from backend.rag.embeddings import embed_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
_RAG_DIR    = os.path.join(os.path.dirname(__file__), "../rag")
PATENT_PATH = os.path.join(_RAG_DIR, "patent_results_enriched.json")
PR_PATH     = os.path.join(_RAG_DIR, "gemini_sourced_articles.json")
OUT_PATH    = os.path.join(_RAG_DIR, "matched_data.json")

_BATCH_SIZE  = 10    # max concurrent Gemini embedding calls
_BATCH_DELAY = 1.0   # seconds between batches — keeps RPM well under 60


def _cosine_sim(a: list[float], b: list[float]) -> float:
    """Pure-Python cosine similarity — avoids numpy dependency."""
    dot    = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


async def _embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts in rate-limited batches of _BATCH_SIZE."""
    results: list[list[float]] = []
    for i in range(0, len(texts), _BATCH_SIZE):
        batch = texts[i : i + _BATCH_SIZE]
        batch_results = await asyncio.gather(*[embed_text(t) for t in batch])
        results.extend(batch_results)
        if i + _BATCH_SIZE < len(texts):
            await asyncio.sleep(_BATCH_DELAY)
    return results


async def main() -> None:
    # ── Load source data ──────────────────────────────────────────────────────
    with open(PATENT_PATH, encoding="utf-8") as f:
        patents_by_company: dict = json.load(f)
    with open(PR_PATH, encoding="utf-8") as f:
        press_releases: list[dict] = json.load(f)

    total_patents = sum(len(v) for v in patents_by_company.values())
    logger.info("Loaded %d patents across %d companies, %d press releases.",
                total_patents, len(patents_by_company), len(press_releases))

    # ── Step 1: Embed all press releases in batches ───────────────────────────
    logger.info("Step 1/3 — Embedding %d press releases (batches of %d)...",
                len(press_releases), _BATCH_SIZE)
    pr_texts = [
        f"{r.get('title', '')}\n\n{r.get('summary', '')}"
        for r in press_releases
    ]
    pr_embeddings: list[list[float]] = await _embed_batch(pr_texts)
    logger.info("Press release embeddings complete.")

    # ── Step 2: Match each patent to its top-3 press releases ────────────────
    logger.info("Step 2/3 — Matching %d patents to press releases...", total_patents)
    matched: dict = {}
    done = 0

    for json_company, patents in patents_by_company.items():
        matched[json_company] = []
        for patent in patents:
            embed_str = "\n\n".join(filter(None, [
                patent.get("matched_product_name", ""),
                patent.get("matched_product_description", ""),
                patent.get("abstract", ""),
            ]))
            patent_emb = await embed_text(embed_str)

            scored = []
            for pr, pr_emb in zip(press_releases, pr_embeddings):
                sim = _cosine_sim(patent_emb, pr_emb)
                scored.append({**pr, "similarity": round(sim, 4)})

            scored.sort(key=lambda x: x["similarity"], reverse=True)
            matched[json_company].append({
                "patent": patent,
                "top_press_releases": scored[:3],
            })
            done += 1
            if done % 50 == 0:
                logger.info("  Matched %d / %d patents...", done, total_patents)

        logger.info("  Company '%s' done — %d patents matched.", json_company, len(patents))

    logger.info("Matching complete.")

    # ── Step 3: Write matched_data.json ──────────────────────────────────────
    logger.info("Step 3/3 — Writing matched_data.json...")
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(matched, f, indent=2, ensure_ascii=False)
    size_kb = os.path.getsize(OUT_PATH) // 1024
    logger.info("Saved → %s (%d KB)", OUT_PATH, size_kb)

    logger.info("=" * 60)
    logger.info("DONE — matched_data.json ready for agent input.")
    logger.info("  Companies : %s", list(matched.keys()))
    logger.info("  Total entries : %d", total_patents)
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
