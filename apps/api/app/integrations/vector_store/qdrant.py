import logging
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qm

from app.integrations.vector_store.base import VectorSearchHit, VectorStore

logger = logging.getLogger(__name__)


class QdrantVectorStore(VectorStore):
    """Qdrant adapter using a single collection with two named vectors.

    This keeps ingestion and search in one place and avoids maintaining two
    collections. `text_vector_name` and `image_vector_name` are configurable
    so existing collections can be reused.
    """

    def __init__(
        self,
        url: str,
        api_key: str,
        collection: str,
        text_vector_name: str = "text",
        image_vector_name: str = "image",
    ) -> None:
        self._collection = collection
        self._text_vec = text_vector_name
        self._image_vec = image_vector_name
        # Local dev: empty URL falls back to the in-memory mode so the
        # backend boots and /search/text works end-to-end without a
        # running Qdrant Cloud cluster.
        if not url:
            self._client = AsyncQdrantClient(":memory:")
        else:
            self._client = AsyncQdrantClient(url=url, api_key=api_key or None)

    async def ensure_collection(self, text_dim: int, image_dim: int) -> None:
        existing = await self._client.get_collections()
        names = {c.name for c in existing.collections}
        if self._collection in names:
            return
        await self._client.create_collection(
            collection_name=self._collection,
            vectors_config={
                self._text_vec: qm.VectorParams(size=text_dim, distance=qm.Distance.COSINE),
                self._image_vec: qm.VectorParams(size=image_dim, distance=qm.Distance.COSINE),
            },
        )
        logger.info("Created Qdrant collection %s", self._collection)

    async def upsert(self, points: list[dict[str, Any]]) -> None:
        qp: list[qm.PointStruct] = []
        for p in points:
            vectors: dict[str, list[float]] = {}
            if p.get("text_vector") is not None:
                vectors[self._text_vec] = p["text_vector"]
            if p.get("image_vector") is not None:
                vectors[self._image_vec] = p["image_vector"]
            qp.append(
                qm.PointStruct(
                    id=p["id"],
                    vector=vectors,
                    payload=p.get("payload") or {},
                )
            )
        await self._client.upsert(collection_name=self._collection, points=qp)

    async def search_text(
        self,
        vector: list[float],
        limit: int,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchHit]:
        return await self._search(self._text_vec, vector, limit, filters)

    async def search_image(
        self,
        vector: list[float],
        limit: int,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchHit]:
        return await self._search(self._image_vec, vector, limit, filters)

    async def _search(
        self,
        vector_name: str,
        vector: list[float],
        limit: int,
        filters: dict[str, Any] | None,
    ) -> list[VectorSearchHit]:
        qfilter = _build_filter(filters) if filters else None
        res = await self._client.query_points(
            collection_name=self._collection,
            query=vector,
            using=vector_name,
            limit=limit,
            query_filter=qfilter,
            with_payload=True,
        )
        return [
            VectorSearchHit(id=str(p.id), score=float(p.score), payload=p.payload or {})
            for p in res.points
        ]


def _build_filter(filters: dict[str, Any]) -> qm.Filter:
    must: list[qm.FieldCondition] = []
    for key, value in filters.items():
        if value is None:
            continue
        if isinstance(value, list):
            must.append(
                qm.FieldCondition(key=key, match=qm.MatchAny(any=value))
            )
        else:
            must.append(
                qm.FieldCondition(key=key, match=qm.MatchValue(value=value))
            )
    return qm.Filter(must=must)
