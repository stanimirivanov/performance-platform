"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import artifacts, events, runs, snapshots


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="PerfEng Metadata Storage Service",
        version="1.0.0",
        description="Store and retrieve performance test run metadata.",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(runs.router)
    app.include_router(snapshots.router)
    app.include_router(events.router)
    app.include_router(artifacts.router)

    return app
