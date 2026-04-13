from typing import Any

import httpx

from app.integrations.chat.base import ChatProvider


class OpenAICompatChat(ChatProvider):
    """Chat completion via any OpenAI-compatible endpoint.

    Works with Groq, Together, Fireworks, local vLLM, etc.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def complete(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 512,
    ) -> str:
        url = f"{self._base_url}/chat/completions"
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        resp = await self._client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
