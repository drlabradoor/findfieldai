import logging

from app.integrations.storage.base import StorageProvider

logger = logging.getLogger(__name__)


class SupabaseStorage(StorageProvider):
    """Thin Supabase Storage adapter.

    The Supabase SDK is synchronous; we keep the interface async so the
    service layer can await uniformly. Swap this out for an S3/R2 adapter
    later without touching callers.
    """

    def __init__(self, url: str, service_role_key: str, bucket: str) -> None:
        self._url = url.rstrip("/")
        self._bucket = bucket
        self._client = None
        if url and service_role_key:
            try:
                from supabase import create_client

                self._client = create_client(url, service_role_key)
            except Exception as e:  # pragma: no cover
                logger.warning("Supabase client init failed: %s", e)

    async def upload(self, path: str, content: bytes, content_type: str) -> str:
        if self._client is None:
            raise RuntimeError("Supabase storage not configured")
        self._client.storage.from_(self._bucket).upload(
            path=path,
            file=content,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        return self.public_url(path)

    def public_url(self, path: str) -> str:
        return f"{self._url}/storage/v1/object/public/{self._bucket}/{path}"
