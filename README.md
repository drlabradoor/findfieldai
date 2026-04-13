# Findfield AI

Retrieval-first multimodal discovery for tourist places. Users can find places by natural-language description, by uploaded photo, or through a grounded chat assistant that only talks about places actually retrieved from the vector index.

This repository is an MVP scaffold. See [docs/mvp-spec.md](docs/mvp-spec.md) for the full product spec, [docs/architecture.md](docs/architecture.md) for how the pieces fit together, and [docs/deployment.md](docs/deployment.md) for the Vercel + Render + Supabase + Qdrant deployment walkthrough.

## Repo layout

```
apps/
  api/      FastAPI backend (retrieval, chat, ingestion)
  web/      Next.js frontend (scaffold, not built yet)
packages/
  shared/   Shared TS/Python types (stub)
  prompts/  Chat prompts as versioned markdown
docs/       Spec + architecture
infra/      Deployment notes / IaC stubs
```

## Quickstart (backend)

```bash
cd apps/api
python -m venv .venv
.venv/Scripts/activate                     # Windows
pip install -r requirements.txt            # full stack (Python 3.11)
# OR on Python 3.14 where psycopg/supabase don't build yet:
pip install -r requirements-dev.txt
cp ../../.env.example .env                 # fill in Supabase + Qdrant keys
uvicorn app.main:app --reload
```

Without any env vars the API falls back to SQLite + an in-memory Qdrant + fake embeddings, so `POST /places/seed` → `POST /search/text` works end-to-end locally without any external services.

Then open http://localhost:8000/docs.

## Environment

Copy [.env.example](.env.example) and fill in free-tier credentials:

- Supabase project URL + service role key
- Qdrant Cloud URL + API key
- Embeddings provider key (Hugging Face Inference API by default, for BGE-M3)
- Chat provider key (any OpenAI-compatible free-tier endpoint)

All providers are abstracted — see [apps/api/app/integrations/](apps/api/app/integrations/).

## What works in this scaffold

- FastAPI app with routers for auth, places, search, chat, favorites
- SQLModel tables for Place, PlaceImage, Favorite, SearchLog
- Qdrant adapter with named text/image vectors
- BGE-M3 embeddings adapter via Hugging Face Inference API
- `POST /search/text` end-to-end: query → embedding → Qdrant → Postgres hydrate

Image search, chat orchestration, and ingestion are stubbed with clear TODOs.
