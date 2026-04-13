from abc import ABC, abstractmethod


class StorageProvider(ABC):
    @abstractmethod
    async def upload(self, path: str, content: bytes, content_type: str) -> str:
        """Upload bytes and return the public URL."""

    @abstractmethod
    def public_url(self, path: str) -> str:
        ...
