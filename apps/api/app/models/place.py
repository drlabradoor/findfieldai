from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column
from sqlmodel import JSON, Field, SQLModel


class BudgetLevel(str, Enum):
    free = "free"
    low = "low"
    mid = "mid"
    high = "high"


class IndoorOutdoor(str, Enum):
    indoor = "indoor"
    outdoor = "outdoor"
    both = "both"


class Place(SQLModel, table=True):
    __tablename__ = "places"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(index=True)
    short_description: str = ""
    long_description: str = ""

    country: str = Field(index=True)
    city: str = Field(index=True)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    category: str = Field(index=True)
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    budget_level: BudgetLevel = Field(default=BudgetLevel.mid, index=True)
    indoor_outdoor: IndoorOutdoor = Field(default=IndoorOutdoor.outdoor, index=True)

    source_url: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
