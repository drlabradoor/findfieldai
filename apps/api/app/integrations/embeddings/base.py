from abc import ABC, abstractmethod


class EmbeddingsProvider(ABC):
    """Adapter interface for text and image embedding models.

    Implementations should be swappable: BGE-M3 via Hugging Face today,
    local batch or a different vendor tomorrow. Keep the surface tiny.
    """

    text_dim: int
    image_dim: int

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        ...

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...

    @abstractmethod
    async def embed_image(self, image_bytes: bytes) -> list[float]:
        ...
