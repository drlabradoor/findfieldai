from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.place import BudgetLevel, IndoorOutdoor


class PlaceImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    image_url: str
    sort_order: int = 0


class PlaceBase(BaseModel):
    title: str
    short_description: str = ""
    long_description: str = ""
    country: str
    city: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    category: str
    tags: list[str] = Field(default_factory=list)
    budget_level: BudgetLevel = BudgetLevel.mid
    indoor_outdoor: IndoorOutdoor = IndoorOutdoor.outdoor
    source_url: Optional[str] = None


class PlaceCreate(PlaceBase):
    pass


class PlaceOut(PlaceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    images: list[PlaceImageOut] = Field(default_factory=list)

    @classmethod
    def from_model(cls, place, images: list | None = None) -> "PlaceOut":
        # SQLModel.table=True does not cooperate with model_dump in pydantic v2,
        # so we go through model_validate (from_attributes) and attach images
        # separately. Keeps routers and services free of field-by-field copies.
        out = cls.model_validate(place)
        out.images = [PlaceImageOut.model_validate(i) for i in (images or [])]
        return out


class PlaceFilters(BaseModel):
    country: Optional[str] = None
    city: Optional[str] = None
    category: Optional[str] = None
    budget_level: Optional[BudgetLevel] = None
    indoor_outdoor: Optional[IndoorOutdoor] = None
    tags: Optional[list[str]] = None
