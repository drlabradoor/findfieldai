# Findfield AI — MVP Spec

## Goal

Low-cost MVP web application where users can discover tourist places by:

1. Natural-language description
2. Uploaded photo
3. Chat assistant that refines the search and explains results

Retrieval-first system. The assistant must only discuss real places retrieved from the database / vector index, never hallucinated ones.

## Product scope (MVP)

**In scope**

- Text search using semantic search
- Image search using uploaded photo
- Chat assistant that interprets intent, asks at most one follow-up, retrieves places, and explains why results match
- Place cards (title, short description, city/country, tags/categories, 1–3 images)
- Filters: country, city, category, budget level, indoor/outdoor
- Basic auth
- Saved favorites

**Out of scope**

- Booking, payments, route planning
- Personalized ranking from history
- Admin CMS, custom ML training
- Kubernetes, Kafka, RabbitMQ, Elasticsearch

## Stack

- **Frontend:** Next.js + TypeScript + Tailwind
- **Backend:** FastAPI + Python 3.11+, Pydantic, SQLModel (async where reasonable)
- **DB/Storage/Auth:** Supabase Postgres, Supabase Auth, Supabase Storage
- **Vector search:** Qdrant Cloud (free tier)
- **Text embeddings:** BAAI/bge-m3 via swappable provider
- **Image embeddings:** CLIP-compatible model
- **Chat model:** open-source instruct model via free-tier OpenAI-compatible endpoint
- **Background work:** FastAPI background tasks for MVP; no Celery/Redis

## Cost & performance rules

- Precompute embeddings at ingestion. Never on read for POIs
- Cache repeated queries where practical
- LLM is only for intent extraction, follow-up generation, answer formatting
- For plain search, retrieve directly — LLM is not the search engine
- Keep LLM context small
- Optimize images/thumbnails before storing

## Architecture

Retrieval-first multimodal:

1. **Text search** → text embedding → Qdrant nearest neighbors → metadata filter → ranked results
2. **Image search** → image embedding → Qdrant image vectors → ranked results
3. **Multimodal** → combine text + image + filters in a simple explainable way
4. **Chat** → parse intent → retrieve → explain with grounded answer → at most one clarifying question

## Data model

- **User** (id, email, created_at)
- **Place** (id, title, short/long description, country, city, lat, lng, category, tags, budget_level, indoor_outdoor, source_url, timestamps)
- **PlaceImage** (id, place_id, storage_path, image_url, sort_order)
- **Favorite** (id, user_id, place_id, created_at)
- **SearchLog** (id, user_id?, query_text?, search_type, filters_json, created_at)

## Qdrant design

One collection `places` with named vectors `text` and `image`, payload includes place_id, country, city, category, budget_level, indoor_outdoor, tags.

## API endpoints

Auth: `POST /auth/signup`, `POST /auth/login`, `GET /me`
Places: `GET /places`, `GET /places/{id}`, `POST /places/seed`
Search: `POST /search/text`, `POST /search/image`, `POST /search/multimodal`
Chat: `POST /chat/query`
Favorites: `POST /favorites/{place_id}`, `DELETE /favorites/{place_id}`, `GET /favorites`

## Chat behavior

- Never invent places
- Only talk about retrieved places
- State uncertainty when results are weak
- Ask for clarification when needed
- Short, useful answers

## Ingestion pipeline

1. Insert places to Postgres
2. Upload/store images
3. Generate text embeddings
4. Generate image embeddings
5. Upsert vectors in Qdrant with matching IDs
6. Support reindex

## Engineering rules

- Env vars for all secrets
- `.env.example` + `README.md`
- Basic tests for search + chat orchestration
- Type hints everywhere
- No premature abstractions beyond provider swapping
- Provider adapters for embeddings, chat, vector store, storage

## Development order

1. Backend structure
2. DB schema
3. Text search
4. Image search
5. Chat assistant
6. Frontend integration
7. Seed scripts + docs
