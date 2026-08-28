"""
FastAPI application factory for the metadata storage service.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import DatabaseRepository
from .routes import router


def create_app(dsn: str | None = None) -> FastAPI:
    """Application factory with dependency injection."""
    repo = DatabaseRepository(dsn)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await repo.connect()
        yield
        await repo.close()

    app = FastAPI(
        title="PerfEng Metadata Storage Service",
        version="1.0.0",
        description="Store and retrieve performance test run metadata.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app
