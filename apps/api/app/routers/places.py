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
    fetch_place_image_url,
    import_city_from_osm,
    is_latin_text,
)
import httpx
import httpx as _httpx_for_debug

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


class BackfillRequest(BaseModel):
    city: str | None = None
    country: str | None = None
    limit: int = Field(default=200, ge=1, le=2000)


class BackfillResult(BaseModel):
    checked: int
    updated: int
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
    try:
        created = await import_city_from_osm(
            ingestion, body.city, body.country, body.limit
        )
    except OSMImportError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
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


@router.post("/debug-image")
async def debug_image(qid: str = Query(...)) -> dict:
    """Temporary: probe Wikidata directly from inside Render so we can see
    what's going wrong with image lookup. Remove once verified."""
    result: dict = {"qid": qid}
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
    try:
        async with _httpx_for_debug.AsyncClient(
            timeout=20.0, follow_redirects=True
        ) as client:
            r = await client.get(
                url,
                headers={"User-Agent": "findfieldai/0.1 (https://github.com/drlabradoor/findfieldai; drkapuler@gmail.com)"},
            )
            result["status"] = r.status_code
            result["content_type"] = r.headers.get("content-type")
            result["body_size"] = len(r.content)
            if r.status_code == 200:
                try:
                    data = r.json()
                    entity = (data.get("entities") or {}).get(qid) or {}
                    claims = entity.get("claims", {}) if isinstance(entity, dict) else {}
                    p18 = claims.get("P18", []) if isinstance(claims, dict) else []
                    result["has_p18"] = bool(p18)
                    if p18:
                        ms = p18[0].get("mainsnak", {})
                        dv = ms.get("datavalue", {})
                        result["p18_value"] = dv.get("value")
                except Exception as e:  # noqa: BLE001
                    result["json_error"] = f"{type(e).__name__}: {e}"
            else:
                result["body_preview"] = r.text[:300]
    except Exception as e:  # noqa: BLE001
        result["http_error"] = f"{type(e).__name__}: {e}"

    # Also test what the real function returns
    try:
        async with _httpx_for_debug.AsyncClient(timeout=20.0) as client:
            result["fn_result"] = await fetch_place_image_url(client, {"wikidata": qid})
    except Exception as e:  # noqa: BLE001
        result["fn_error"] = f"{type(e).__name__}: {e}"
    return result


@router.post("/backfill-images", response_model=BackfillResult)
async def backfill_images(
    body: BackfillRequest,
    repo: PlaceRepository = Depends(get_place_repo),
) -> BackfillResult:
    """Fetch and store images for existing places that have none.

    Idempotent — places that already have images are skipped.
    Uses Wikimedia Commons geosearch (lat/lon) as the primary source.
    """
    filters = PlaceFilters(city=body.city, country=body.country)
    places = repo.list_places(filters=filters, limit=body.limit)
    images_by_place = repo.images_for([p.id for p in places])
    without_image = [p for p in places if not images_by_place.get(p.id)]

    updated_titles: list[str] = []
    async with httpx.AsyncClient(timeout=20.0) as client:
        for place in without_image:
            url = await fetch_place_image_url(
                client, {}, lat=place.latitude, lon=place.longitude
            )
            if url:
                repo.add_images(place.id, [url])
                updated_titles.append(place.title)

    return BackfillResult(
        checked=len(without_image),
        updated=len(updated_titles),
        titles=updated_titles[:30],
    )


@router.post("/debug-commons")
async def debug_commons(lat: float = Query(...), lon: float = Query(...)) -> dict:
    """Temporary: probe Commons geosearch from inside Render."""
    result: dict = {"lat": lat, "lon": lon}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "generator": "geosearch",
                    "ggsnamespace": "6",
                    "ggsradius": "500",
                    "ggslimit": "5",
                    "ggscoord": f"{lat}|{lon}",
                    "prop": "imageinfo",
                    "iiprop": "url",
                    "iiurlwidth": "800",
                    "format": "json",
                },
                headers={"User-Agent": "findfieldai/0.1 (https://github.com/drlabradoor/findfieldai; drkapuler@gmail.com)"},
            )
            result["status"] = r.status_code
            result["url"] = str(r.url)
            result["body_size"] = len(r.content)
            if r.status_code == 200:
                data = r.json()
                pages = (data.get("query") or {}).get("pages") or {}
                result["page_count"] = len(pages)
                result["titles"] = [p.get("title") for p in pages.values()][:5]
            else:
                result["body_preview"] = r.text[:300]
            result["fn_result"] = await fetch_place_image_url(client, {}, lat=lat, lon=lon)
    except Exception as e:  # noqa: BLE001
        result["error"] = f"{type(e).__name__}: {e}"
    return result


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
