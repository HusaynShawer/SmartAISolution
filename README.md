# SmartAISolution

Customer service AI Agent built with FastAPI, LangGraph, and React.

## Overview

An intelligent support agent that:

- Routes customer queries to specialized agents (RAG, customer data, tickets)
- Answers questions from uploaded documentation (PDF, Markdown, TXT) using vector search
- Retrieves account details and ticket history
- Creates, updates, and escalates support tickets
- Keeps conversational memory per user

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React + Vite + Tailwind)                          │
│  /login · /register · chat UI with SSE streaming            │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / SSE
┌──────────────────────────▼──────────────────────────────────┐
│  FastAPI App (app/)                                          │
│  routers → services → repositories → models (PostgreSQL)     │
│                                                            │
│  /auth · /chat · /conversations · /tickets · /documents      │
│  /health · /metrics (Prometheus)                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  LangGraph Agent (app/agent/)                                │
│  Router → { RAG · SQL · Ticket · Respond }                   │
│  Tools: search_docs · create/update ticket · escalate        │
│  Memory: per-conversation message store                     │
│  LLM: OpenRouter (DeepSeek) · Embeddings: Cohere + pgvector  │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
app/
├── agent/          # LangGraph agent (router + specialist nodes)
├── alembic/        # Database migrations
├── core/           # Config, security, rate limiting, metrics, exceptions
├── database/       # SQLAlchemy async engine & session
├── memory/         # Conversational memory manager
├── models/         # SQLAlchemy ORM models
├── rag/            # Loading, splitting, embedding, retrieval
├── repositories/   # Data access layer
├── routers/        # API endpoints
├── schemas/        # Pydantic validation schemas
├── services/       # Business logic
├── tests/          # pytest suite
└── tools/          # LangChain tools for the agents

frontend/           # React + Vite + Tailwind chat UI
docker-compose.yml  # Full stack: DB + backend + frontend
Dockerfile          # Multi-stage build (frontend + backend)
.github/workflows/  # CI pipeline
```

## Features

### Agent Routing
- **RAG Agent**: answers documentation questions using pgvector similarity search
- **SQL Agent**: reads account info and ticket history
- **Ticket Agent**: creates/updates/escalates tickets with user confirmation
- **Respond**: handles general conversation

### Engineering
- Async FastAPI + SQLAlchemy throughout
- SSE streaming chat responses
- Rate limiting (slowapi)
- Retry logic for embedding/LLM calls (tenacity)
- CORS via environment config
- Auto-generated conversation titles
- LLM token usage tracking
- Prometheus metrics at `/metrics`
- Database health check at `/health`
- Ruff linting + mypy type checking (clean)
- 21 unit tests

## Getting Started

### Option A: Docker (full stack — recommended)

One command runs the database, backend, and built frontend together.

```bash
# 1. Configure keys
cp .env.docker.example .env
#   - fill OPENROUTER_API_KEY and EMBEDDING_API_KEY

# 2. Build & start everything
docker compose up --build -d

# 3. Open the app
open http://localhost:8000
```

- `http://localhost:8000/` — the chat UI (served by FastAPI)
- `http://localhost:8000/docs` — interactive API docs
- `http://localhost:8000/health` — health check
- `http://localhost:8000/metrics` — Prometheus metrics
- Migrations run automatically on startup.
- The app uses a separate DB (`smartSOL-db`, host port `${DB_PORT:-5434}`) inside the stack.

### Option B: Run locally

#### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker (for PostgreSQL with pgvector)

#### Backend

```bash
# 1. Start the database
docker compose up -d db

# 2. Create & activate venv
python -m venv aienv
source aienv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp app/.env.example app/.env
#   - fill DATABASE_URL, JWT_SECRET, OPENROUTER_API_KEY, EMBEDDING_API_KEY

# 5. Run migrations
cd app && alembic upgrade head

# 6. Start the API
cd app && uvicorn main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev        # dev server at http://localhost:3000
npm run build      # production build -> served by FastAPI at /
```

### Health check
```bash
curl http://localhost:8000/health
# {"status":"ok","version":"1.0.0","database":"ok"}
```

## Development Workflow

```bash
ruff check app/                       # lint
mypy app/ --ignore-missing-imports    # type check (run from app/)
cd app && python -m pytest tests/     # tests
cd frontend && npm run build          # frontend build
```

## Environment Variables

See `app/.env.example` for the full list:

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | AsyncPostgreSQL URL (pgvector) |
| `JWT_SECRET` | Secret for signing JWT tokens |
| `OPENROUTER_API_KEY` | LLM provider key |
| `LLM_MODEL` | Model served via OpenRouter |
| `EMBEDDING_API_KEY` | Cohere embeddings key |
| `EMBEDDING_MODEL` | Embedding model name |
| `CORS_ORIGINS` | Allowed browser origins |
| `DEFAULT_RATE_LIMIT` | e.g. `20/minute` |
| `REQUEST_TIMEOUT_SECONDS` | LLM call timeout |

## License

See [LICENSE](./assets/LICENSE.txt).