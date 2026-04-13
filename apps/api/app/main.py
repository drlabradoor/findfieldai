from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import init_db
from app.logging import setup_logging
from app.routers import auth, chat, favorites, health, places, search


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Findfield AI API",
        description="Retrieval-first multimodal place discovery.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_origin_regex=settings.app_cors_origin_regex or None,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(places.router)
    app.include_router(search.router)
    app.include_router(chat.router)
    app.include_router(favorites.router)
    return app


app = create_app()
