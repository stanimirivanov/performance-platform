"""FastAPI application factory."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from perfeng.api.routes import artifacts, events, runs, snapshots


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

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        return JSONResponse(
            status_code=500,
            content={"detail": "Database error occurred."},
        )

    # Include routers
    app.include_router(runs.router)
    app.include_router(snapshots.router)
    app.include_router(events.router)
    app.include_router(artifacts.router)

    return app
