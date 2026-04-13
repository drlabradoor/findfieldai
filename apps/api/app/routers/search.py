import json

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.deps import get_search_service
from app.schemas.place import PlaceFilters
from app.schemas.search import (
    MultimodalSearchRequest,
    SearchResponse,
    TextSearchRequest,
)
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/text", response_model=SearchResponse)
async def search_text(
    req: TextSearchRequest,
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    return await service.search_text(
        query=req.query,
        filters=req.filters,
        limit=req.limit,
    )


@router.post("/image", response_model=SearchResponse)
async def search_image(
    image: UploadFile = File(...),
    filters: str = Form("{}"),
    limit: int = Form(12),
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    parsed_filters = PlaceFilters(**json.loads(filters or "{}"))
    content = await image.read()
    return await service.search_image(
        image_bytes=content,
        filters=parsed_filters,
        limit=limit,
    )


@router.post("/multimodal", response_model=SearchResponse)
async def search_multimodal(
    req: MultimodalSearchRequest,
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    # MVP: if text is present, do text search. Image branch uses /search/image.
    # TODO: combine signals with a simple weighted score once image upload is wired in.
    if req.query:
        return await service.search_text(
            query=req.query,
            filters=req.filters,
            limit=req.limit,
        )
    return SearchResponse(query=None, count=0, hits=[])
