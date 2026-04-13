import logging
from uuid import UUID

from app.integrations.embeddings.base import EmbeddingsProvider
from app.integrations.vector_store.base import VectorStore
from app.models.search_log import SearchType
from app.repositories.place_repo import PlaceRepository
from app.repositories.search_log_repo import SearchLogRepository
from app.schemas.place import PlaceFilters, PlaceOut
from app.schemas.search import PlaceSearchHit, SearchResponse

logger = logging.getLogger(__name__)


class SearchService:
    """Retrieval-first search.

    Flow: query → embedding → Qdrant → hydrate from Postgres → return hits.
    The LLM is never in this path.
    """

    def __init__(
        self,
        embeddings: EmbeddingsProvider,
        vector_store: VectorStore,
        place_repo: PlaceRepository,
        search_log_repo: SearchLogRepository,
    ) -> None:
        self._embeddings = embeddings
        self._store = vector_store
        self._places = place_repo
        self._logs = search_log_repo

    async def search_text(
        self,
        query: str,
        filters: PlaceFilters,
        limit: int = 12,
    ) -> SearchResponse:
        vector = await self._embeddings.embed_text(query)
        hits = await self._store.search_text(
            vector=vector,
            limit=limit,
            filters=_filters_to_payload(filters),
        )
        response = self._hydrate(hits, query=query)
        try:
            self._logs.record(
                search_type=SearchType.text,
                query_text=query,
                filters=filters.model_dump(exclude_none=True),
            )
        except Exception as e:  # best-effort; search success must not depend on logging
            logger.warning("SearchLog write failed: %s", e)
        return response

    async def search_image(
        self,
        image_bytes: bytes,
        filters: PlaceFilters,
        limit: int = 12,
    ) -> SearchResponse:
        vector = await self._embeddings.embed_image(image_bytes)
        hits = await self._store.search_image(
            vector=vector,
            limit=limit,
            filters=_filters_to_payload(filters),
        )
        return self._hydrate(hits, query=None)

    def _hydrate(self, hits, query: str | None) -> SearchResponse:
        ids: list[UUID] = []
        for h in hits:
            try:
                ids.append(UUID(h.id))
            except ValueError:
                continue
        places = {p.id: p for p in self._places.get_many(ids)}
        images_by_place = self._places.images_for(list(places.keys()))

        out_hits: list[PlaceSearchHit] = []
        for h in hits:
            try:
                pid = UUID(h.id)
            except ValueError:
                continue
            place = places.get(pid)
            if not place:
                continue
            out_hits.append(
                PlaceSearchHit(
                    score=h.score,
                    place=PlaceOut.from_model(place, images_by_place.get(pid, [])),
                )
            )
        return SearchResponse(query=query, count=len(out_hits), hits=out_hits)


def _filters_to_payload(filters: PlaceFilters) -> dict:
    # mode='json' coerces enums to their string values so the vector store
    # adapter doesn't need to care about Python enum instances.
    payload: dict = {}
    dump = filters.model_dump(mode="json", exclude_none=True)
    for key in ("country", "city", "category", "budget_level", "indoor_outdoor"):
        if dump.get(key) is not None:
            payload[key] = dump[key]
    if dump.get("tags"):
        payload["tags"] = dump["tags"]
    return payload
