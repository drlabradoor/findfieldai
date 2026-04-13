from functools import lru_cache

from fastapi import Depends
from sqlmodel import Session

from app.config import Settings, get_settings
from app.db import get_session
from app.integrations.chat.base import ChatProvider
from app.integrations.chat.openai_compat import OpenAICompatChat
from app.integrations.embeddings.base import EmbeddingsProvider
from app.integrations.embeddings.fake import FakeEmbeddings
from app.integrations.embeddings.huggingface import HuggingFaceEmbeddings
from app.integrations.storage.base import StorageProvider
from app.integrations.storage.supabase import SupabaseStorage
from app.integrations.vector_store.base import VectorStore
from app.integrations.vector_store.qdrant import QdrantVectorStore
from app.repositories.favorite_repo import FavoriteRepository
from app.repositories.place_repo import PlaceRepository
from app.repositories.search_log_repo import SearchLogRepository
from app.services.chat_service import ChatService
from app.services.ingestion_service import IngestionService
from app.services.search_service import SearchService


@lru_cache
def _embeddings_singleton() -> EmbeddingsProvider:
    s = get_settings()
    if s.embeddings_provider == "fake" or not s.huggingface_api_key:
        return FakeEmbeddings(
            text_dim=s.embeddings_text_dim,
            image_dim=s.embeddings_image_dim,
        )
    return HuggingFaceEmbeddings(
        api_key=s.huggingface_api_key,
        text_model=s.embeddings_text_model,
        image_model=s.embeddings_image_model,
        text_dim=s.embeddings_text_dim,
        image_dim=s.embeddings_image_dim,
    )


@lru_cache
def _vector_store_singleton() -> VectorStore:
    s = get_settings()
    return QdrantVectorStore(
        url=s.qdrant_url,
        api_key=s.qdrant_api_key,
        collection=s.qdrant_collection,
        text_vector_name=s.qdrant_text_vector,
        image_vector_name=s.qdrant_image_vector,
    )


@lru_cache
def _chat_singleton() -> ChatProvider:
    s = get_settings()
    return OpenAICompatChat(
        base_url=s.chat_base_url,
        api_key=s.chat_api_key,
        model=s.chat_model,
    )


@lru_cache
def _storage_singleton() -> StorageProvider:
    s = get_settings()
    return SupabaseStorage(
        url=s.supabase_url,
        service_role_key=s.supabase_service_role_key,
        bucket=s.supabase_storage_bucket,
    )


def get_embeddings() -> EmbeddingsProvider:
    return _embeddings_singleton()


def get_vector_store() -> VectorStore:
    return _vector_store_singleton()


def get_chat_provider() -> ChatProvider:
    return _chat_singleton()


def get_storage() -> StorageProvider:
    return _storage_singleton()


def get_place_repo(session: Session = Depends(get_session)) -> PlaceRepository:
    return PlaceRepository(session)


def get_favorite_repo(session: Session = Depends(get_session)) -> FavoriteRepository:
    return FavoriteRepository(session)


def get_search_log_repo(session: Session = Depends(get_session)) -> SearchLogRepository:
    return SearchLogRepository(session)


def get_search_service(
    embeddings: EmbeddingsProvider = Depends(get_embeddings),
    vector_store: VectorStore = Depends(get_vector_store),
    place_repo: PlaceRepository = Depends(get_place_repo),
    search_log_repo: SearchLogRepository = Depends(get_search_log_repo),
) -> SearchService:
    return SearchService(
        embeddings=embeddings,
        vector_store=vector_store,
        place_repo=place_repo,
        search_log_repo=search_log_repo,
    )


def get_chat_service(
    chat: ChatProvider = Depends(get_chat_provider),
    search: SearchService = Depends(get_search_service),
) -> ChatService:
    return ChatService(chat=chat, search=search)


def get_ingestion_service(
    place_repo: PlaceRepository = Depends(get_place_repo),
    embeddings: EmbeddingsProvider = Depends(get_embeddings),
    vector_store: VectorStore = Depends(get_vector_store),
) -> IngestionService:
    return IngestionService(
        place_repo=place_repo,
        embeddings=embeddings,
        vector_store=vector_store,
    )


def get_settings_dep() -> Settings:
    return get_settings()
