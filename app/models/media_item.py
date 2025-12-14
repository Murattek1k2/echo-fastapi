"""MediaItem ORM model."""

import enum
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

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


class MediaItem(Base):
    """ORM model for media items (movies, TV shows, books, plays)."""

    __tablename__ = "media_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[MediaType] = mapped_column(Enum(MediaType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )

    # Relationship to reviews
    reviews: Mapped[list["Review"]] = relationship(
        "Review", back_populates="media_item", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_media_items_title", "title"),)
