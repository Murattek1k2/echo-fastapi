"""API routers package."""

from app.api.routers.health import router as health_router
from app.api.routers.reviews import router as reviews_router

__all__ = ["health_router", "reviews_router"]
