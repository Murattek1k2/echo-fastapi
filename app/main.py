"""Main FastAPI application."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.api.routers import health_router, media_items_router, reviews_router
from app.db.session import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Echo FastAPI",
    description="A CRUD API for sharing reviews of movies, TV shows, books, and plays.",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(health_router)
app.include_router(media_items_router)
app.include_router(reviews_router)


@app.get("/")
def root() -> dict:
    """Root endpoint."""
    return {"message": "Hello World"}
