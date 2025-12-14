"""Main FastAPI application."""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routers import health_router, reviews_router
from app.db.migrations import run_migrations
from app.db.session import Base, engine

# Directory for uploaded files
UPLOADS_DIR = os.getenv("UPLOADS_DIR", "uploads")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create database tables on startup and ensure uploads directory exists."""
    # Run migrations for existing tables before create_all
    run_migrations(engine)
    Base.metadata.create_all(bind=engine)
    # Ensure uploads directory exists
    Path(UPLOADS_DIR).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Echo FastAPI",
    description="A CRUD API for sharing reviews of movies, TV shows, books, and plays.",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount static files directory for serving uploaded images
Path(UPLOADS_DIR).mkdir(parents=True, exist_ok=True)
app.mount(f"/{UPLOADS_DIR}", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# Include routers
app.include_router(health_router)
app.include_router(reviews_router)


@app.get("/")
def root() -> dict:
    """Root endpoint."""
    return {"message": "Hello World"}
