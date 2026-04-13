from uuid import UUID

from sqlmodel import Session, select

from app.models.place import Place
from app.models.place_image import PlaceImage
from app.schemas.place import PlaceFilters


class PlaceRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def get(self, place_id: UUID) -> Place | None:
        return self._s.get(Place, place_id)

    def get_many(self, ids: list[UUID]) -> list[Place]:
        if not ids:
            return []
        stmt = select(Place).where(Place.id.in_(ids))  # type: ignore[attr-defined]
        return list(self._s.exec(stmt).all())

    def list_places(
        self,
        filters: PlaceFilters | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Place]:
        stmt = select(Place)
        if filters:
            if filters.country:
                stmt = stmt.where(Place.country == filters.country)
            if filters.city:
                stmt = stmt.where(Place.city == filters.city)
            if filters.category:
                stmt = stmt.where(Place.category == filters.category)
            if filters.budget_level:
                stmt = stmt.where(Place.budget_level == filters.budget_level)
            if filters.indoor_outdoor:
                stmt = stmt.where(Place.indoor_outdoor == filters.indoor_outdoor)
        stmt = stmt.limit(limit).offset(offset)
        return list(self._s.exec(stmt).all())

    def create(self, place: Place) -> Place:
        self._s.add(place)
        self._s.commit()
        self._s.refresh(place)
        return place

    def images_for(self, place_ids: list[UUID]) -> dict[UUID, list[PlaceImage]]:
        if not place_ids:
            return {}
        stmt = select(PlaceImage).where(PlaceImage.place_id.in_(place_ids))  # type: ignore[attr-defined]
        by_place: dict[UUID, list[PlaceImage]] = {pid: [] for pid in place_ids}
        for img in self._s.exec(stmt).all():
            by_place.setdefault(img.place_id, []).append(img)
        for imgs in by_place.values():
            imgs.sort(key=lambda i: i.sort_order)
        return by_place
