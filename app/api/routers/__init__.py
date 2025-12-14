"""API routers package."""

from app.api.routers.health import router as health_router
from app.api.routers.media_items import router as media_items_router
from app.api.routers.reviews import router as reviews_router

__all__ = ["health_router", "media_items_router", "reviews_router"]
