# PatentWatch — AI Corporate Transparency Tool

Analyzes a defense company's public ethical claims against their actual European Patent Office (EPO) filings using a **multimodal RAG pipeline** and **LangGraph multi-agent orchestration**.

## Architecture

```
monorepo/
├── backend/                 # FastAPI (Python)
│   ├── api/
│   │   └── analyze.py       # REST + SSE endpoints
│   ├── ingestion/
│   │   ├── yfinance_client.py   # News & press releases
│   │   ├── epo_client.py        # EPO patent data
│   │   └── web_scraper.py       # Product images
│   ├── rag/
│   │   ├── embeddings.py        # Gemini multimodal embeddings
│   │   ├── chunker.py           # Text chunking
│   │   ├── vector_store.py      # Supabase pgvector CRUD
│   │   └── pipeline.py          # End-to-end ingestion
│   ├── agents/
│   │   ├── state.py             # LangGraph shared state
│   │   ├── nodes.py             # Investigator / Forensic / Synthesizer
│   │   └── graph.py             # LangGraph state machine
│   ├── core/
│   │   └── config.py            # Pydantic settings
│   ├── scripts/
│   │   └── setup_supabase.sql   # DB schema + pgvector setup
│   ├── main.py                  # FastAPI app entry point
│   └── requirements.txt
└── frontend/                # Next.js 14 (App Router)
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   └── page.tsx         # Main dashboard
        ├── components/
        │   ├── Header.tsx
        │   ├── StatsBar.tsx
        │   ├── AgentStatusPanel.tsx
        │   ├── RiskScore.tsx
        │   ├── ScoreDrivers.tsx
        │   ├── ProductGrid.tsx
        │   └── ContradictionsTable.tsx
        ├── lib/
        │   └── api.ts           # API client with SSE streaming
        └── types/
            └── analysis.ts      # TypeScript interfaces
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

Open http://localhost:3000

## API Keys Required

| Key | Source |
|-----|--------|
| GOOGLE_API_KEY | Google AI Studio |
| SUPABASE_URL + SUPABASE_SERVICE_KEY | Supabase project settings > API |
| EPO_CONSUMER_KEY + EPO_CONSUMER_SECRET | EPO OPS Developer Portal |

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
