from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.deps import get_ingestion_service, get_place_repo
from app.models.place import Place
from app.repositories.place_repo import PlaceRepository
from app.schemas.place import PlaceCreate, PlaceFilters, PlaceOut
from app.services.ingestion_service import IngestionService
from app.services.osm_import_service import (
    OSMImportError,
    import_city_from_osm,
    is_latin_text,
)

router = APIRouter(prefix="/places", tags=["places"])


class OSMImportRequest(BaseModel):
    city: str
    country: str
    limit: int = Field(default=80, ge=1, le=500)


class WipeRequest(BaseModel):
    city: str | None = None
    country: str | None = None


class CleanupResult(BaseModel):
    deleted: int
    titles: list[str] = Field(default_factory=list)


@router.get("", response_model=list[PlaceOut])
async def list_places(
    country: str | None = Query(default=None),
    city: str | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repo: PlaceRepository = Depends(get_place_repo),
) -> list[PlaceOut]:
    filters = PlaceFilters(country=country, city=city, category=category)
    places = repo.list_places(filters=filters, limit=limit, offset=offset)
    images_by_place = repo.images_for([p.id for p in places])
    return [PlaceOut.from_model(p, images_by_place.get(p.id, [])) for p in places]


@router.get("/{place_id}", response_model=PlaceOut)
async def get_place(
    place_id: UUID,
    repo: PlaceRepository = Depends(get_place_repo),
) -> PlaceOut:
    place = repo.get(place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    images = repo.images_for([place.id]).get(place.id, [])
    return PlaceOut.from_model(place, images)


@router.post("/seed", response_model=list[PlaceOut])
async def seed_places(
    places: list[PlaceCreate],
    ingestion: IngestionService = Depends(get_ingestion_service),
    repo: PlaceRepository = Depends(get_place_repo),
) -> list[PlaceOut]:
    await ingestion.ensure_collection()
    created: list[Place] = []
    for body in places:
        place = Place(**body.model_dump())
        await ingestion.ingest_place(place)
        created.append(place)
    return [PlaceOut.from_model(p, []) for p in created]


@router.post("/import-osm", response_model=list[PlaceOut])
async def import_osm(
    body: OSMImportRequest,
    ingestion: IngestionService = Depends(get_ingestion_service),
) -> list[PlaceOut]:
    import logging
    import traceback

    log = logging.getLogger(__name__)
    try:
        created = await import_city_from_osm(
            ingestion, body.city, body.country, body.limit
        )
    except OSMImportError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        log.exception("import_osm failed")
        raise HTTPException(
            status_code=500,
            detail=f"{type(e).__name__}: {e}\n{traceback.format_exc()[-1500:]}",
        ) from e
    return [PlaceOut.from_model(p, []) for p in created]


@router.post("/cleanup-nonlatin", response_model=CleanupResult)
async def cleanup_nonlatin(
    ingestion: IngestionService = Depends(get_ingestion_service),
    repo: PlaceRepository = Depends(get_place_repo),
) -> CleanupResult:
    """Delete places whose title is not Latin-script (Cyrillic, Georgian, etc).

    Walks the entire ``places`` table, identifies offenders via
    ``is_latin_text``, removes them from Postgres and Qdrant in one pass.
    Idempotent — safe to call repeatedly.
    """
    all_places = repo.list_places(limit=10000)
    offenders = [p for p in all_places if not is_latin_text(p.title)]
    await ingestion.delete_places([p.id for p in offenders])
    return CleanupResult(
        deleted=len(offenders),
        titles=[p.title for p in offenders[:30]],
    )


@router.post("/wipe", response_model=CleanupResult)
async def wipe_places(
    body: WipeRequest,
    ingestion: IngestionService = Depends(get_ingestion_service),
    repo: PlaceRepository = Depends(get_place_repo),
) -> CleanupResult:
    """Bulk-delete places (optionally filtered by city/country).

    Use before re-importing a city to avoid duplicate rows. Without
    filters this nukes the entire collection — call carefully.
    """
    filters = PlaceFilters(city=body.city, country=body.country)
    places = repo.list_places(filters=filters, limit=10000)
    await ingestion.delete_places([p.id for p in places])
    return CleanupResult(
        deleted=len(places),
        titles=[p.title for p in places[:30]],
    )
