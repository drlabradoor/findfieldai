# Findfield Web

Next.js 15 + Tailwind web interface for Findfield AI.

## Run locally

```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000. The home page wires up to `POST /search/text`
on the FastAPI backend at `NEXT_PUBLIC_API_URL`.

## Screens planned

- `/` — home with text search bar + results grid (implemented)
- `/upload` — image upload → `/search/image` (TODO)
- `/chat` — grounded chat panel → `/chat/query` (TODO)
- `/places/[id]` — place detail page (TODO)
- `/favorites` — saved favorites (TODO)

Keep it simple: no heavy design work, no animation libraries. The point is
clarity and speed for discovery.
