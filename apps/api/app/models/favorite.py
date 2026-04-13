from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, UniqueConstraint


class Favorite(SQLModel, table=True):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "place_id", name="uq_user_place"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    place_id: UUID = Field(foreign_key="places.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
