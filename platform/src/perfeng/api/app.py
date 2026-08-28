"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import runs_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="PerfEng Metadata Storage Service",
        version="1.0.0",
        description="Store and retrieve performance test run metadata.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(runs_router)
    return app
