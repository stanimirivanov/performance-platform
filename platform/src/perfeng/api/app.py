"""FastAPI application factory."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from perfeng.api.routes import artifacts, events, runs, snapshots
from perfeng.storage.database import engine


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

    # Exception handler for database errors
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        return JSONResponse(
            status_code=500,
            content={"detail": "Database error occurred."},
        )

    # Simple DB health check
    @app.get("/health/db")
    async def health_db():
        try:
            async with engine.connect() as conn:
                await conn.execute("SELECT 1")
            return {"status": "healthy", "database": "connected"}
        except Exception:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "database": "disconnected"},
            )

    # Include routers
    app.include_router(runs.router)
    app.include_router(snapshots.router)
    app.include_router(events.router)
    app.include_router(artifacts.router)

    return app
