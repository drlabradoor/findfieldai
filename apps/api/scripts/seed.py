"""Local seed runner.

Usage:
    python -m scripts.seed path/to/seed.json

Reads a JSON list of places, inserts them via the ingestion pipeline so
text embeddings are generated and upserted into Qdrant in one pass.
"""

import asyncio
import json
import sys
from pathlib import Path

from sqlmodel import Session

from app.db import engine, init_db
from app.deps import _embeddings_singleton, _vector_store_singleton
from app.models.place import Place
from app.repositories.place_repo import PlaceRepository
from app.services.ingestion_service import IngestionService


async def run(path: Path) -> None:
    init_db()
    data = json.loads(path.read_text(encoding="utf-8"))
    with Session(engine) as session:
        service = IngestionService(
            place_repo=PlaceRepository(session),
            embeddings=_embeddings_singleton(),
            vector_store=_vector_store_singleton(),
        )
        await service.ensure_collection()
        for item in data:
            await service.ingest_place(Place(**item))
            print(f"ingested: {item['title']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python -m scripts.seed path/to/seed.json")
        sys.exit(1)
    asyncio.run(run(Path(sys.argv[1])))
