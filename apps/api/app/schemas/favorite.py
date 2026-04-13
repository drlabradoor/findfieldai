from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.place import PlaceOut


class FavoriteOut(BaseModel):
    id: UUID
    place: PlaceOut
    created_at: datetime
