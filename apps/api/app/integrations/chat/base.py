from abc import ABC, abstractmethod
from typing import Any


class ChatProvider(ABC):
    """Narrow chat-completion interface.

    Used only for intent extraction and grounded answer formatting.
    Kept intentionally tool-free for MVP to avoid vendor lock-in.
    """

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 512,
    ) -> str:
        ...
