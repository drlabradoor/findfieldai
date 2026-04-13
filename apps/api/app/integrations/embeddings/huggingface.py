import logging
from typing import Any

import httpx

from app.integrations.embeddings.base import EmbeddingsProvider

logger = logging.getLogger(__name__)

_HF_BASE = "https://router.huggingface.co/hf-inference/models"


class HuggingFaceEmbeddings(EmbeddingsProvider):
    """Hugging Face Inference API adapter.

    Default text model is BAAI/bge-m3 (1024-d).
    Default image model is sentence-transformers/clip-ViT-B-32 (512-d).
    """

    def __init__(
        self,
        api_key: str,
        text_model: str,
        image_model: str,
        text_dim: int,
        image_dim: int,
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._text_model = text_model
        self._image_model = image_model
        self.text_dim = text_dim
        self.image_dim = image_dim
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def embed_text(self, text: str) -> list[float]:
        vectors = await self.embed_texts([text])
        return vectors[0]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        url = f"{_HF_BASE}/{self._text_model}/pipeline/feature-extraction"
        payload: dict[str, Any] = {
            "inputs": texts,
            "options": {"wait_for_model": True},
        }
        resp = await self._client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return [self._flatten(v) for v in data]

    async def embed_image(self, image_bytes: bytes) -> list[float]:
        url = f"{_HF_BASE}/{self._image_model}/pipeline/feature-extraction"
        resp = await self._client.post(
            url,
            content=image_bytes,
            headers={
                **({"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}),
                "Content-Type": "application/octet-stream",
            },
        )
        resp.raise_for_status()
        return self._flatten(resp.json())

    @staticmethod
    def _flatten(value: Any) -> list[float]:
        # HF feature-extraction may return [dim] or [tokens, dim]; mean-pool if needed.
        if isinstance(value, list) and value and isinstance(value[0], list):
            cols = len(value[0])
            sums = [0.0] * cols
            for row in value:
                for i, v in enumerate(row):
                    sums[i] += float(v)
            return [s / len(value) for s in sums]
        return [float(v) for v in value]
