import hashlib
import math

from app.integrations.embeddings.base import EmbeddingsProvider


class FakeEmbeddings(EmbeddingsProvider):
    """Deterministic hash-based embeddings for local/CI use.

    Not semantically meaningful. Useful only so tests and wiring work
    without hitting a provider.
    """

    def __init__(self, text_dim: int = 1024, image_dim: int = 512) -> None:
        self.text_dim = text_dim
        self.image_dim = image_dim

    async def embed_text(self, text: str) -> list[float]:
        return self._hash_to_vec(text.encode("utf-8"), self.text_dim)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed_text(t) for t in texts]

    async def embed_image(self, image_bytes: bytes) -> list[float]:
        return self._hash_to_vec(image_bytes, self.image_dim)

    @staticmethod
    def _hash_to_vec(data: bytes, dim: int) -> list[float]:
        vec: list[float] = []
        seed = 0
        while len(vec) < dim:
            h = hashlib.sha256(data + seed.to_bytes(4, "big")).digest()
            for i in range(0, len(h), 2):
                if len(vec) == dim:
                    break
                val = int.from_bytes(h[i : i + 2], "big") / 65535.0 - 0.5
                vec.append(val)
            seed += 1
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]
