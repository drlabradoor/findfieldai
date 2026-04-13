from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class PlaceImage(SQLModel, table=True):
    __tablename__ = "place_images"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    place_id: UUID = Field(foreign_key="places.id", index=True)
    storage_path: str
    image_url: str
    sort_order: int = 0
