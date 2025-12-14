"""Pydantic schemas for MediaItem."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.media_item import MediaType


class MediaItemCreate(BaseModel):
    """Schema for creating a media item."""

    type: MediaType
    title: str
    year: int | None = None


class MediaItemUpdate(BaseModel):
    """Schema for updating a media item (partial update)."""

    type: MediaType | None = None
    title: str | None = None
    year: int | None = None


class MediaItemRead(BaseModel):
    """Schema for reading a media item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    type: MediaType
    title: str
    year: int | None
    created_at: datetime
