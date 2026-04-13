"""OpenStreetMap importer for places (CLI wrapper).

Thin CLI around ``app.services.osm_import_service`` so it runs through
the same pipeline as the ``POST /places/import-osm`` endpoint.

Usage:
    python -m scripts.import_osm "Lisbon" --country Portugal --limit 80
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from sqlmodel import Session

from app.db import engine, init_db
from app.deps import _embeddings_singleton, _vector_store_singleton
from app.repositories.place_repo import PlaceRepository
from app.services.ingestion_service import IngestionService
from app.services.osm_import_service import import_city_from_osm


async def run(city: str, country: str, limit: int) -> None:
    init_db()
    with Session(engine) as session:
        ingestion = IngestionService(
            place_repo=PlaceRepository(session),
            embeddings=_embeddings_singleton(),
            vector_store=_vector_store_singleton(),
        )
        created = await import_city_from_osm(ingestion, city, country, limit)
        for p in created:
            print(f"  + {p.title}  [{p.category}]")
        print(f"\nDone. Ingested {len(created)} places from OSM.")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="Import places from OpenStreetMap.")
    ap.add_argument("city", help="City name, e.g. 'Lisbon'")
    ap.add_argument("--country", required=True, help="Country, e.g. 'Portugal'")
    ap.add_argument(
        "--limit",
        type=int,
        default=80,
        help="Max places to ingest (default: 80)",
    )
    args = ap.parse_args()
    asyncio.run(run(args.city, args.country, args.limit))


if __name__ == "__main__":
    main()
