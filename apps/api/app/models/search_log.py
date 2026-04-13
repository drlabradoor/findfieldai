from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column
from sqlmodel import JSON, Field, SQLModel


class SearchType(str, Enum):
    text = "text"
    image = "image"
    multimodal = "multimodal"
    chat = "chat"


class SearchLog(SQLModel, table=True):
    __tablename__ = "search_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="users.id", index=True)
    query_text: Optional[str] = None
    search_type: SearchType = Field(index=True)
    filters_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
