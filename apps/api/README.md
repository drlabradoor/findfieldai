# Findfield API

FastAPI backend for Findfield AI.

## Run locally

```bash
python -m venv .venv
.venv/Scripts/activate   # Windows
pip install -r requirements.txt
cp .env.example .env     # then edit
uvicorn app.main:app --reload
```

Swagger UI: http://localhost:8000/docs

## Seed a few places

```bash
python -m scripts.seed scripts/seed.example.json
```

This creates the Qdrant collection (if missing), inserts the rows into
Postgres, and upserts text embeddings — so `POST /search/text` will return
real hits after running it.

## Tests

```bash
pytest
```

## Layout

- `app/config.py` — settings from env
- `app/models/` — SQLModel tables
- `app/schemas/` — Pydantic request/response
- `app/repositories/` — DB queries (keep business logic out)
- `app/services/` — search, chat, ingestion orchestration
- `app/integrations/` — provider adapters (embeddings, qdrant, chat, storage)
- `app/routers/` — thin HTTP handlers, no business logic
- `app/deps.py` — FastAPI DI wiring
- `scripts/seed.py` — local ingestion driver
