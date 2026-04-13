# Deployment — Findfield AI

Target stack: **Vercel** (web) → **Render** (API) → **Supabase** (Postgres/Auth/Storage) + **Qdrant Cloud** (vectors) + **Hugging Face Inference** (embeddings) + **Groq** (chat LLM).

All paid-ish services used here have a free tier big enough for the MVP.

## Why this split

- **Vercel** — Next.js lives here because it's the fastest path, preview URLs per PR are free, and there's no cold start that matters for a static-ish UI.
- **Render** — FastAPI lives here because Vercel's Python runtime is a serverless function model that doesn't fit long-lived connections to Qdrant and Supabase well. Render gives you a normal long-running process on the free tier.
- **Secrets on the backend, never on the frontend.** Hugging Face and Groq API keys are set on Render only. The web app talks to the Render URL; it never calls HF or Groq directly. If a key would leak into a `NEXT_PUBLIC_*` var, that's a bug.

---

## 0) Pre-flight: accounts

Create (or log into) free accounts on:

- [Supabase](https://supabase.com) — DB + Auth + Storage
- [Qdrant Cloud](https://cloud.qdrant.io) — vector index, free 1 GB cluster
- [Hugging Face](https://huggingface.co/settings/tokens) — read token for Inference API (BGE-M3, CLIP)
- [Groq](https://console.groq.com) — free-tier chat completions (OpenAI-compatible)
- [Render](https://render.com) — backend hosting
- [Vercel](https://vercel.com) — frontend hosting
- GitHub account for the repo (Render + Vercel both pull from GitHub)

---

## 1) Supabase project

1. New project → pick region close to your Render region (e.g. both in `eu-west` or both in `us-east`).
2. Wait for the DB to provision.
3. **Settings → Database → Connection string → URI** → copy the **session pooler** URL (port 5432). Prepend the driver: replace `postgresql://` with `postgresql+psycopg://`. Result looks like:
   ```
   postgresql+psycopg://postgres.abcdefgh:<password>@aws-0-eu-west-1.pooler.supabase.com:5432/postgres
   ```
   This is `SUPABASE_DB_URL`.
4. **Settings → API** → copy `Project URL`, `anon key`, `service_role key`. These are `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`.
5. **Storage → Create bucket** `places`, set Public. `SUPABASE_STORAGE_BUCKET=places`.
6. **(later)** Auth is free and already on — no setup needed until you wire up `supabase-js` on the web side.

> Render will run the app's `init_db()` on startup, which calls `SQLModel.metadata.create_all` and creates the tables in Supabase automatically. For MVP this is fine; when the schema stabilises, switch to Alembic migrations.

## 2) Qdrant Cloud cluster

1. Create a free cluster (1 GB, always-on).
2. Copy the cluster URL (`https://xxxxx.qdrant.tech`) → `QDRANT_URL`.
3. Create an API key → `QDRANT_API_KEY`.
4. `QDRANT_COLLECTION=places` — the backend creates it on first use via `ensure_collection`.

## 3) Hugging Face token

1. https://huggingface.co/settings/tokens → New token → Read scope.
2. `HUGGINGFACE_API_KEY=hf_...`.
3. Confirm BGE-M3 is accessible: `curl -H "Authorization: Bearer hf_..." https://api-inference.huggingface.co/pipeline/feature-extraction/BAAI/bge-m3 -d '{"inputs":"hello"}'` should return a vector.

> BGE-M3 produces 1024-d vectors. If you swap to another model, update `EMBEDDINGS_TEXT_MODEL` and `EMBEDDINGS_TEXT_DIM` together — the Qdrant collection will be created with the wrong size otherwise and you'll need to recreate it.

## 4) Groq API key

1. https://console.groq.com/keys → create key → `CHAT_API_KEY`.
2. Model: `llama-3.1-8b-instant` is the fastest free-tier option; default is already set in `render.yaml`.

---

## 5) Push the repo to GitHub

```bash
cd d:/_work/findfieldai
git init
git add .
git commit -m "initial findfield ai mvp scaffold"
git branch -M main
git remote add origin git@github.com:<you>/findfieldai.git
git push -u origin main
```

## 6) Deploy the API on Render

**Option A — Blueprint (recommended).** Render reads [apps/api/render.yaml](../apps/api/render.yaml).

1. Render dashboard → **New → Blueprint** → connect GitHub → pick the `findfieldai` repo.
2. Render detects `apps/api/render.yaml` and proposes the `findfield-api` service. Click **Apply**.
3. Render opens the env var panel for the new service. Fill the values marked `sync: false` — everything from steps 1-4 above. Leave `APP_CORS_ORIGINS` and `APP_CORS_ORIGIN_REGEX` empty for now; we'll fill them after the web URL exists.
4. First deploy runs `pip install -r requirements.txt` (takes 2-4 min) then `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Healthcheck at `/health` should turn green.
5. Copy the assigned URL, e.g. `https://findfield-api.onrender.com`. This is your backend URL.

**Smoke test:**
```bash
curl https://findfield-api.onrender.com/health
# {"status":"ok"}
```

**Option B — manual.** New → Web Service → point at the repo, root dir `apps/api`, runtime Python, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Add all env vars from `render.yaml` by hand. Slower, not recommended.

> **Cold starts:** Render free web services sleep after 15 minutes idle. The first request after a sleep takes ~30 seconds while the process boots. For MVP that's fine. If you want to keep it warm, either upgrade to a paid plan or wire a cron-ping.

## 7) Seed production data

Once the API is up, seed a few places so the UI has something to show:

```bash
curl -X POST https://findfield-api.onrender.com/places/seed \
  -H "Content-Type: application/json" \
  --data-binary @apps/api/scripts/seed.example.json
```

This creates the Qdrant collection, inserts the rows into Supabase, and computes BGE-M3 embeddings in one pass. If you see 500s, check Render logs — the two common failures are an expired HF token or a wrong `SUPABASE_DB_URL` (forgot the `+psycopg` driver prefix).

## 8) Deploy the web app on Vercel

1. Vercel dashboard → **New → Project** → import the same GitHub repo.
2. **Root Directory:** `apps/web` (Vercel needs this because the repo is a monorepo — set it in the import screen or under Project Settings).
3. Framework preset: Next.js (auto-detected).
4. Environment variable: `NEXT_PUBLIC_API_URL=https://findfield-api.onrender.com`
5. Deploy. Vercel gives you a URL like `https://findfield-web.vercel.app` (and preview URLs per branch).

> **Only `NEXT_PUBLIC_*` vars are exposed to the browser.** Never put `HUGGINGFACE_API_KEY` or `CHAT_API_KEY` on Vercel — those live only on Render. The web app is a thin shell that talks to the Render API.

## 9) Wire CORS back from Render → Vercel

Now that you know the Vercel URL, go back to Render → `findfield-api` → Environment:

- `APP_CORS_ORIGINS=https://findfield-web.vercel.app`
- `APP_CORS_ORIGIN_REGEX=https://findfield-web-[a-z0-9-]+\.vercel\.app` (so preview deploys work too)

Save → Render auto-redeploys.

## 10) End-to-end check

Open the Vercel URL → type a query → hit Search. If the results grid shows the seeded places, you're done.

If you get a CORS error in the browser console, double-check that the Vercel URL in `APP_CORS_ORIGINS` matches exactly (with/without trailing slash, https vs http).

---

## Operational notes

### Keeping secrets out of the frontend

The web app only knows `NEXT_PUBLIC_API_URL`. It never calls HF/Groq/Qdrant directly. If you're tempted to "just call the model from the frontend for a quick test" — don't; the token ends up in the client bundle forever.

### Costs

- **Supabase free:** 500 MB DB, 1 GB storage, 2 GB bandwidth/month, paused after 1 week inactivity (recoverable in one click).
- **Qdrant Cloud free:** 1 GB cluster, always on.
- **Render free:** 750 hours/month of web-service runtime, sleeps when idle.
- **Vercel hobby:** generous for this app's traffic.
- **Hugging Face Inference:** free tier is rate-limited; at MVP traffic it's fine, but watch the 429s in the Render logs. If you hit limits, move embedding computation to ingestion-time only (which we already do for POIs — only the user-query embedding is live) or swap to a different free provider via the adapter.
- **Groq:** free-tier RPM/TPM is enough for MVP chat.

### Reindex after a schema or embedding model change

If you change `EMBEDDINGS_TEXT_MODEL` or `EMBEDDINGS_TEXT_DIM`, the existing Qdrant collection is now the wrong shape. Fix:

1. Qdrant dashboard → delete collection `places`.
2. Call `POST /places/seed` again (or run `scripts/seed.py` against prod env vars) — `ensure_collection` recreates it with the new dimensions.

### Render → Fly.io migration (future)

If Render's sleep behaviour becomes annoying, Fly.io has a similar free tier without sleep. The only file that changes is `render.yaml` → `fly.toml`. The FastAPI app itself is portable.
