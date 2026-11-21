"""FastAPI application main entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1 import documents
from app.core.errors import ResearchRadarError
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Initialize database
    init_db()
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="ResearchRadar API",
    description="Open-source plagiarism checker and research gap analyzer",
    version="0.1.0",
    lifespan=lifespan,
)


# Exception handlers
@app.exception_handler(ResearchRadarError)
async def research_radar_exception_handler(request: Request, exc: ResearchRadarError):
    """Handle custom ResearchRadar exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message},
    )


# Include routers
app.include_router(documents.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "ResearchRadar API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
