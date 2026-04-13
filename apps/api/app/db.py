from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

_settings = get_settings()

# SQLModel registration happens in app.models at import time.
connect_args: dict = {}
if _settings.supabase_db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    _settings.supabase_db_url,
    echo=False,
    pool_pre_ping=True,
    connect_args=connect_args,
)


def init_db() -> None:
    # Imported for side effects: register tables on SQLModel.metadata.
    from app import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
