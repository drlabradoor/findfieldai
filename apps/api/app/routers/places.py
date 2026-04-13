from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import get_ingestion_service, get_place_repo
from app.models.place import Place
from app.repositories.place_repo import PlaceRepository
from app.schemas.place import PlaceCreate, PlaceFilters, PlaceOut
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/places", tags=["places"])


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
