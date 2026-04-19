# PEHero

Agentic AI for private equity — 22 specialist agents that source, underwrite, close, and operate your deals.

- **Marketing landing** at `/` with hero, agent directory, how-it-works, pricing.
- **3-pane chat app** at `/app` with left agent/session browser, centre chat, right artifact pane.
- **22 LangGraph ReAct agents** across deal sourcing, LBO underwriting, due diligence, capital/LP, and portfolio operations — routed by prefix (`triage:`, `lbo:`, `memo:`…) or by keyword heuristics with an LLM fallback classifier.
- **xAI Grok** as the default LLM via OpenAI-compatible endpoint.
- **PostgreSQL** on the existing `DB_URL` with two schemas: `pehero` (OLTP — companies, funds, cap tables, financials, contracts, transaction + trading comps, LBO models, debt stacks, LP CRM, market signals, portfolio KPIs) and `pehero_rag` (pgvector — CIMs, QoE reports, MSAs, legal DD, ESG reports, industry studies).
- **Synthetic PE dataset** out of the box: ~40 portfolio / pipeline companies across 6 sectors, 24 months of monthly financials, cap tables with realistic class structures, ~480 material contracts, transaction + trading comps, 60 LP contacts, and ~320 indexed documents.
- **Local embeddings** via fastembed (no OpenAI key required) — BAAI/bge-small-en-v1.5 at 384 dim.

## Running locally

```bash
cp .env.example .env                    # fill DB_URL + XAI_API_KEY
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m db.migrate                    # creates pehero + pehero_rag schemas
python -m synthetic.generate --seed 42  # populate OLTP + RAG (~1 min)
python main.py                          # serves on :5058
```

Smoke test: `curl http://localhost:5058/app/_debug/ping` → `{"ok": true, "reply": "pong"}`.
End-to-end test: `pytest -q tests/`.

## Running in Docker (local)

```bash
DB_URL=... XAI_API_KEY=... docker compose up --build
```

On boot, the container runs `python -m db.migrate` automatically (idempotent).
Seed synthetic data once with:

```bash
docker compose exec web python -m synthetic.generate --seed 42
```

## Deploying to Coolify (pehero.fyi)

1. Point Coolify at this repo (Docker Compose build type).
2. Set environment variables in Coolify:
   - `DB_URL` — managed Postgres with pgvector enabled
   - `XAI_API_KEY`
3. Attach the `pehero.fyi` domain (port 5058).
4. First deploy only: `docker compose exec web python -m synthetic.generate --seed 42` from Coolify's terminal to populate synthetic data. Subsequent deploys re-run `db.migrate` automatically and leave your data in place.

## Directory layout

```
main.py              entrypoint (thin shim)
app.py               FastHTML app, mounts landing + chat
landing/             / /platform /agents /agents/<slug> /how-it-works /pricing /contact
chat/                /app + /app/chat (SSE stream) + /app/auth/*
agents/              registry + router + 5 category packages (22 agents total)
tools/               StructuredTools: companies, captable, financials, market, diligence, capital, asset, rag
db/                  schema.sql, rag_schema.sql, migrate.py
rag/                 embeddings (pluggable), indexer, retriever
synthetic/           PE dataset + DD doc generators + RAG ingest
prompts/             per-agent system prompts + shared PE glossary
```
