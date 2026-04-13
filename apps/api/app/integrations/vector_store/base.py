from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class VectorSearchHit:
    id: str
    score: float
    payload: dict[str, Any]


class VectorStore(ABC):
    """Minimal vector-store interface used by the search service.

    Keep this narrow — the intent is provider swap, not a general-purpose wrapper.
    """

    @abstractmethod
    async def ensure_collection(self, text_dim: int, image_dim: int) -> None:
        ...

    @abstractmethod
    async def upsert(
        self,
        points: list[dict[str, Any]],
    ) -> None:
        """Upsert points.

        Each point: {"id": str, "text_vector": list[float] | None,
                     "image_vector": list[float] | None, "payload": dict}.
        """

    @abstractmethod
    async def search_text(
        self,
        vector: list[float],
        limit: int,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchHit]:
        ...

    @abstractmethod
    async def search_image(
        self,
        vector: list[float],
        limit: int,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchHit]:
        ...
