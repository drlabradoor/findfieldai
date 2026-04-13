from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.place import PlaceFilters, PlaceOut


class TextSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    filters: PlaceFilters = Field(default_factory=PlaceFilters)
    limit: int = Field(default=12, ge=1, le=50)


class ImageSearchRequest(BaseModel):
    filters: PlaceFilters = Field(default_factory=PlaceFilters)
    limit: int = Field(default=12, ge=1, le=50)


class MultimodalSearchRequest(BaseModel):
    query: Optional[str] = None
    filters: PlaceFilters = Field(default_factory=PlaceFilters)
    limit: int = Field(default=12, ge=1, le=50)


class PlaceSearchHit(BaseModel):
    score: float
    place: PlaceOut


class SearchResponse(BaseModel):
    query: Optional[str] = None
    count: int
    hits: list[PlaceSearchHit]
