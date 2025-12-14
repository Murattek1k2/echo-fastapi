"""Review ORM model."""

import enum
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(UTC)


class MediaType(str, enum.Enum):
    """Enum for media types."""

    movie = "movie"
    tv = "tv"
    book = "book"
    play = "play"


class Review(Base):
    """ORM model for reviews of media items."""

    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    author_telegram_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    media_type: Mapped[MediaType] = mapped_column(Enum(MediaType), nullable=False)
    media_title: Mapped[str] = mapped_column(String(255), nullable=False)
    media_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    contains_spoilers: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    __table_args__ = (
        Index("ix_reviews_media_title", "media_title"),
        Index("ix_reviews_media_type_title", "media_type", "media_title"),
    )
