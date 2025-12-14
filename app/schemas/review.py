"""Pydantic schemas for Review."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    """Schema for creating a review."""

    media_item_id: int
    author_name: str
    rating: int = Field(..., ge=1, le=10)
    text: str
    contains_spoilers: bool = False


class ReviewUpdate(BaseModel):
    """Schema for updating a review (partial update)."""

    author_name: str | None = None
    rating: int | None = Field(default=None, ge=1, le=10)
    text: str | None = None
    contains_spoilers: bool | None = None


class ReviewRead(BaseModel):
    """Schema for reading a review."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    media_item_id: int
    author_name: str
    rating: int
    text: str
    contains_spoilers: bool
    created_at: datetime
    updated_at: datetime
