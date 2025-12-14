"""Pydantic schemas for Review."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.review import MediaType


class ReviewCreate(BaseModel):
    """Schema for creating a review."""

    author_name: str
    author_telegram_id: int | None = None
    media_type: MediaType
    media_title: str
    media_year: int | None = None
    rating: int = Field(..., ge=1, le=10)
    text: str
    contains_spoilers: bool = False


class ReviewCreateForm(BaseModel):
    """Schema for creating a review with optional image via form data."""

    author_name: str
    media_type: MediaType
    media_title: str
    media_year: int | None = None
    rating: int = Field(..., ge=1, le=10)
    text: str
    contains_spoilers: bool = False


class ReviewUpdate(BaseModel):
    """Schema for updating a review (partial update)."""

    author_name: str | None = None
    media_type: MediaType | None = None
    media_title: str | None = None
    media_year: int | None = None
    rating: int | None = Field(default=None, ge=1, le=10)
    text: str | None = None
    contains_spoilers: bool | None = None


class ReviewRead(BaseModel):
    """Schema for reading a review."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    author_name: str
    author_telegram_id: int | None = None
    media_type: MediaType
    media_title: str
    media_year: int | None
    rating: int
    text: str
    contains_spoilers: bool
    image_path: str | None = None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def image_url(self) -> str | None:
        """Compute the image URL from image_path."""
        if self.image_path:
            return f"/{self.image_path}"
        return None
