# PEHero

Agentic AI PE deal platform. 22 specialist agents (sourcing, underwriting, diligence, capital, portfolio operations) + marketing landing + 3-pane chat UI, on **one FastHTML app**.

## Stack

- Python 3.13, FastHTML + Uvicorn, single process (port 5058 by default).
- LLM: xAI Grok via OpenAI-compatible endpoint (`utils/llm.py`).
- Agents: LangGraph `create_react_agent` per specialist.
- DB: PostgreSQL via `DB_URL`, two schemas — `pehero` (OLTP) and `pehero_rag` (pgvector chunks/embeddings).
- Embeddings: pluggable provider (fastembed local default → OpenAI fallback) in `rag/embeddings.py`.

## Layout

```
main.py              entrypoint
app.py               FastHTML app, mounts landing + chat route groups
landing/             marketing site (/, /platform, /agents, /how-it-works, /pricing, /contact)
chat/                3-pane product (/app, /app/chat, /app/auth/*, /app/_debug/ping)
agents/              5 category subpackages, 22 agent modules
tools/               shared LangChain StructuredTools
db/                  schema.sql, rag_schema.sql, migrate.py, models.py
rag/                 embeddings, indexer, retriever
synthetic/           PE data generators (populate pehero + pehero_rag)
utils/               llm, config, logging, session
prompts/             system prompts per agent + shared PE glossary (pe_context.md)
static/              css + js
```

## Running locally

```bash
cp .env.example .env                    # fill in DB_URL + XAI_API_KEY
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m db.migrate                    # creates both schemas + pgvector
python -m synthetic.generate --seed 42  # populates OLTP + RAG
python main.py                          # serves on :5058
```

Smoke test after boot: `curl http://localhost:5058/app/_debug/ping` → JSON with `{"ok": true, "reply": "pong"}`.

## Deployment

- Dockerfile + docker-compose.yml included for Coolify. Production target: pehero.fyi.
- Use the `app` profile in Coolify (external Postgres). Use `full` profile for local bring-up with pgvector image alongside.

## Conventions

- All LLM calls go through `utils.llm.build_llm()` / `build_agent_llm()` — no direct `ChatOpenAI` construction elsewhere.
- Every agent module exports `SPEC`, `TOOLS`, `SYSTEM_PROMPT`, `build()`. Registry (`agents/registry.py`) discovers them.
- Synthetic data must be deterministic given `--seed` so tests are stable.
- Schemas `pehero.*` and `pehero_rag.*` are always qualified in SQL — never rely on `search_path`.
- Agent module filenames and tool filenames still mirror the Bricksmith origin (rent_roll_parser.py, leases.py, properties.py, etc.). The PUBLIC names in the AgentSpec (`Cap Table Parser`, `Contract Abstractor`, etc.) and all prompts / synthetic content are PE-specific. Don't be surprised: `tools/rentroll.py` queries `pehero.cap_tables`.
