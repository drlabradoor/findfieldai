# Findfield AI — Architecture

## One-line summary

A FastAPI backend fronts Supabase Postgres (metadata + auth + storage) and Qdrant (vector index). Everything that touches an external model or vendor is behind a provider adapter so the MVP can start on free tiers and upgrade later.

## Components

```
[ Next.js UI ] ──► [ FastAPI API ] ──► [ Supabase Postgres ]
                         │          ──► [ Supabase Storage  ]
                         │          ──► [ Supabase Auth     ]
                         │
                         ├──► [ Embeddings provider ] (BGE-M3 / CLIP)
                         ├──► [ Qdrant Cloud        ] (text + image vectors)
                         └──► [ Chat provider       ] (OpenAI-compatible LLM)
```

## Retrieval-first flow

All search modes bottom out in Qdrant, not the LLM.

### Text search

1. `POST /search/text` with query + optional filters
2. `SearchService` calls `EmbeddingsProvider.embed_text(query)` → 1024-d vector
3. `VectorStore.search(...)` in Qdrant using the `text` named vector + payload filter
4. Returned place_ids are hydrated from Postgres in a single query
5. Results are returned as `PlaceSearchHit` with score + place payload
6. A `SearchLog` row is written asynchronously

### Image search (planned)

Same shape, but `embed_image(bytes)` → CLIP vector → Qdrant `image` named vector.

### Chat (planned)

1. Call chat provider with a small system prompt to extract structured intent (filters, query_text, mode)
2. Run retrieval with those filters
3. Call chat provider a second time with only the top-K retrieved places as grounded context
4. If top results have weak scores, emit a clarifying question instead of an answer

The chat orchestration never passes candidate-free prose to the model; the LLM is only a formatter + intent parser.

## Provider abstractions

Each lives under [apps/api/app/integrations/](../apps/api/app/integrations/).

- `EmbeddingsProvider` — `embed_text(str) -> list[float]`, `embed_image(bytes) -> list[float]`. Default: Hugging Face Inference API for BGE-M3 + CLIP.
- `VectorStore` — `upsert(...)`, `search(...)`, `ensure_collection(...)`. Default: Qdrant Cloud.
- `ChatProvider` — `complete(messages, tools=None)`. Default: OpenAI-compatible endpoint (e.g. Groq free tier) with an open-weights instruct model.
- `StorageProvider` — `upload(path, bytes)`, `public_url(path)`. Default: Supabase Storage.

Adding a new vendor is a new file in the same folder plus one wire-up in `deps.py`.

## Cost posture

- Embeddings are computed **once** per place at ingestion, never on read
- Query-side embedding is one API call per user search — cacheable by exact query hash
- Chat provider is called at most twice per chat turn (intent → answer), on ≤ K=5 places
- No Redis, Celery, or message bus in the MVP. FastAPI background tasks handle logging and reindex

## Data boundaries

- Postgres is the **source of truth** for places, images, favorites, logs
- Qdrant holds vectors + minimal payload for filter pushdown
- Qdrant IDs are the Postgres place UUIDs — no mapping table needed
- Reindex is idempotent: delete collection → re-upsert from Postgres

## What we are explicitly not building

- Custom ranking model, feedback loop, reranker
- Image moderation pipeline beyond basic MIME check
- Admin CMS — seed data via `POST /places/seed` and ingestion script
- Realtime / websockets
