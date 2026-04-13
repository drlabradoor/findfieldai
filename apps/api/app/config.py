from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["dev", "prod", "test"] = "dev"
    app_log_level: str = "INFO"
    app_cors_origins: str = "http://localhost:3000"
    # Optional regex applied in addition to exact origins — useful for
    # Vercel preview URLs (e.g. https://findfield-web-.*\.vercel\.app).
    app_cors_origin_regex: str = ""

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_db_url: str = "sqlite:///./findfield.db"
    supabase_storage_bucket: str = "places"

    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_collection: str = "places"
    qdrant_text_vector: str = "text"
    qdrant_image_vector: str = "image"

    embeddings_provider: Literal["huggingface", "local", "fake"] = "huggingface"
    embeddings_text_model: str = "BAAI/bge-m3"
    embeddings_image_model: str = "sentence-transformers/clip-ViT-B-32"
    embeddings_text_dim: int = 1024
    embeddings_image_dim: int = 512
    huggingface_api_key: str = ""

    chat_provider: Literal["openai_compat", "fake"] = "openai_compat"
    chat_base_url: str = "https://api.groq.com/openai/v1"
    chat_api_key: str = ""
    chat_model: str = "llama-3.1-8b-instant"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.app_cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
