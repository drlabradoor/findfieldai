from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.search import PlaceSearchHit


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatQueryRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatMessage] = Field(default_factory=list)


class ChatQueryResponse(BaseModel):
    answer: str
    follow_up_question: Optional[str] = None
    results: list[PlaceSearchHit] = Field(default_factory=list)
