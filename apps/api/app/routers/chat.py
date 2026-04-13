from fastapi import APIRouter, Depends

from app.deps import get_chat_service
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/query", response_model=ChatQueryResponse)
async def chat_query(
    req: ChatQueryRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatQueryResponse:
    return await service.query(req)
