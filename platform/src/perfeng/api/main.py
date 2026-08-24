"""FastAPI application for Performance Engineering Platform."""

from fastapi import FastAPI

app = FastAPI(
    title="PerfEng API",
    description="Continuous Performance Engineering Platform API",
    version="0.1.0",
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "perfeng-api"}


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Performance Engineering Platform",
        "docs": "/docs",
        "health": "/health",
    }
