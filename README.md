# PatentWatch: AI Corporate Transparency Tool

Built at HackEurope (February 2026) by a team from King's AI Society.

Defence companies describe their products in the language of protection and precision. Their patent filings describe what the products actually do. PatentWatch puts the two side by side: it ingests a company's press releases and product pages, retrieves its European Patent Office filings with multimodal RAG, and runs a three-agent LangGraph pipeline that scores how far the public claims diverge from the patented capabilities, citing the specific patent behind each contradiction.

**Stack:** FastAPI, LangGraph, Gemini (text and multimodal embeddings), Supabase pgvector, EPO Open Patent Services, Vite + React + Tailwind. Backend deploys on Railway (`railway.toml`), frontend on Vercel (`vercel.json`).

## Architecture

```
backend/                    FastAPI app
  api/analyze.py            REST + SSE endpoints
  ingestion/                yfinance news, EPO OPS client, product-page scraper
  rag/                      chunking, Gemini embeddings, pgvector store, ingestion pipeline
  agents/                   LangGraph state, Investigator / Forensic / Synthesizer nodes, graph
  core/config.py            Pydantic settings
  scripts/                  Supabase schema, pipeline and analysis runners
  main.py
microservices/              offline data prep: EPO patent pull, filtering, Gemini enrichment, news scraping
frontend/                   Vite + React + Tailwind
  src/components/           CompanyPage, ComparisonTable, ContradictionModal
  src/lib/api.ts            API client with SSE streaming
```

## Agent Pipeline

```
START → [Investigator] → [Forensic] → [Synthesizer] → END
```

| Agent | Role |
|-------|------|
| **Investigator** | Retrieves press releases & product images; extracts public ethical claims |
| **Forensic** | Queries patent embeddings; identifies dual-use capabilities and kill-chain relevance |
| **Synthesizer** | Compares both outputs; produces risk_score, score_drivers, contradictions JSON |

## Quick Start

### 1. Supabase Setup

Run `backend/scripts/setup_supabase.sql` in your Supabase project SQL editor.

### 2. Backend

```bash
cd backend
cp .env.example .env
# Fill in your API keys

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn backend.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open the URL Vite prints (http://localhost:5173 by default).

## API Keys Required

| Key | Source |
|-----|--------|
| GOOGLE_API_KEY | Google AI Studio |
| SUPABASE_URL + SUPABASE_SERVICE_KEY | Supabase project settings > API |
| EPO_CONSUMER_KEY + EPO_CONSUMER_SECRET | EPO OPS Developer Portal |

The `microservices/` scripts read `GOOGLE_API_KEY` from the environment as well. No key is committed to this repo; keep yours in `backend/.env`, which is gitignored.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/companies | List supported companies |
| GET | /api/stats/{company} | Ingestion stats |
| POST | /api/ingest | Trigger data ingestion |
| POST | /api/analyze | Run full analysis (blocking) |
| POST | /api/analyze/stream | Run analysis with SSE streaming |

## Output Format

```json
{
  "risk_score": 82,
  "score_drivers": [
    "Autonomous targeting patents contradict precision protection claims",
    "High kill-chain relevance across 15+ IPC F41/F42 classified patents",
    "AI-guided munitions masked under smart logistics marketing language"
  ],
  "products": ["https://cdn.example.com/product1.jpg"],
  "contradictions": [
    {
      "claim": "Our technology protects civilian lives",
      "evidence": "EP3456789 claims autonomous target selection with no human-in-loop requirement",
      "why_it_matters": "Removes legal accountability from lethal force decisions",
      "sources": ["EP3456789"]
    }
  ]
}
```
