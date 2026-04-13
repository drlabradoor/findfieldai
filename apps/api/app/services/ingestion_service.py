import logging

from app.integrations.embeddings.base import EmbeddingsProvider
from app.integrations.vector_store.base import VectorStore
from app.models.place import Place
from app.repositories.place_repo import PlaceRepository

logger = logging.getLogger(__name__)


class IngestionService:
    """Seed pipeline: insert places, embed, upsert to Qdrant.

    Kept synchronous-friendly for MVP. Call `ensure_collection` once, then
    `ingest_place` per record. Reindex = delete collection + run again.
    """

    def __init__(
        self,
        place_repo: PlaceRepository,
        embeddings: EmbeddingsProvider,
        vector_store: VectorStore,
    ) -> None:
        self._places = place_repo
        self._embeddings = embeddings
        self._store = vector_store

    async def ensure_collection(self) -> None:
        await self._store.ensure_collection(
            text_dim=self._embeddings.text_dim,
            image_dim=self._embeddings.image_dim,
        )

    async def ingest_place(self, place: Place) -> None:
        saved = self._places.create(place)
        text_for_embedding = _place_to_text(saved)
        text_vec = await self._embeddings.embed_text(text_for_embedding)
        await self._store.upsert(
            [
                {
                    "id": str(saved.id),
                    "text_vector": text_vec,
                    "image_vector": None,
                    "payload": {
                        "place_id": str(saved.id),
                        "country": saved.country,
                        "city": saved.city,
                        "category": saved.category,
                        "budget_level": saved.budget_level.value
                        if hasattr(saved.budget_level, "value")
                        else saved.budget_level,
                        "indoor_outdoor": saved.indoor_outdoor.value
                        if hasattr(saved.indoor_outdoor, "value")
                        else saved.indoor_outdoor,
                        "tags": saved.tags,
                    },
                }
            ]
        )


def _place_to_text(place: Place) -> str:
    parts = [
        place.title,
        place.short_description,
        place.long_description,
        f"{place.city}, {place.country}",
        place.category,
        " ".join(place.tags or []),
    ]
    return ". ".join(p for p in parts if p)
