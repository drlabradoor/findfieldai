import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.integrations.embeddings.fake import FakeEmbeddings
from app.integrations.vector_store.base import VectorSearchHit, VectorStore
from app.models.place import Place
from app.repositories.place_repo import PlaceRepository
from app.repositories.search_log_repo import SearchLogRepository
from app.schemas.place import PlaceFilters
from app.services.search_service import SearchService


class StubVectorStore(VectorStore):
    def __init__(self, hits: list[VectorSearchHit]) -> None:
        self._hits = hits
        self.last_filters: dict | None = None

    async def ensure_collection(self, text_dim, image_dim):
        pass

    async def upsert(self, points):
        pass

    async def search_text(self, vector, limit, filters=None):
        self.last_filters = filters
        return self._hits[:limit]

    async def search_image(self, vector, limit, filters=None):
        return self._hits[:limit]


@pytest.fixture
def session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    # Force model registration
    from app import models  # noqa: F401

    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.mark.asyncio
async def test_search_text_hydrates_places_from_vector_hits(session: Session) -> None:
    place = Place(
        title="Sunset Pier",
        short_description="quiet coastal spot",
        country="Portugal",
        city="Lisbon",
        category="viewpoint",
    )
    session.add(place)
    session.commit()
    session.refresh(place)

    store = StubVectorStore(
        [VectorSearchHit(id=str(place.id), score=0.91, payload={})]
    )
    service = SearchService(
        embeddings=FakeEmbeddings(),
        vector_store=store,
        place_repo=PlaceRepository(session),
        search_log_repo=SearchLogRepository(session),
    )

    result = await service.search_text(
        query="quiet coastal spot near Lisbon",
        filters=PlaceFilters(country="Portugal"),
        limit=5,
    )

    assert result.count == 1
    assert result.hits[0].score == pytest.approx(0.91)
    assert result.hits[0].place.title == "Sunset Pier"
    assert store.last_filters == {"country": "Portugal"}


@pytest.mark.asyncio
async def test_search_text_drops_unknown_place_ids(session: Session) -> None:
    store = StubVectorStore(
        [VectorSearchHit(id="00000000-0000-0000-0000-000000000000", score=0.5, payload={})]
    )
    service = SearchService(
        embeddings=FakeEmbeddings(),
        vector_store=store,
        place_repo=PlaceRepository(session),
        search_log_repo=SearchLogRepository(session),
    )
    result = await service.search_text(
        query="anything",
        filters=PlaceFilters(),
        limit=5,
    )
    assert result.count == 0
