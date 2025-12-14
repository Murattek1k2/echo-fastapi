"""Media items CRUD endpoints."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.db.session import DbSession
from app.models.media_item import MediaItem, MediaType
from app.schemas.media_item import MediaItemCreate, MediaItemRead, MediaItemUpdate

router = APIRouter(prefix="/media-items", tags=["Media Items"])


@router.post("/", response_model=MediaItemRead, status_code=status.HTTP_201_CREATED)
def create_media_item(data: MediaItemCreate, db: DbSession) -> MediaItem:
    """Create a new media item."""
    media_item = MediaItem(
        type=data.type,
        title=data.title,
        year=data.year,
    )
    db.add(media_item)
    db.commit()
    db.refresh(media_item)
    return media_item


@router.get("/", response_model=list[MediaItemRead])
def list_media_items(
    db: DbSession,
    limit: int = 100,
    offset: int = 0,
    type: MediaType | None = None,
    title: str | None = None,
) -> list[MediaItem]:
    """List media items with optional filtering and pagination."""
    query = select(MediaItem)

    if type is not None:
        query = query.where(MediaItem.type == type)

    if title is not None:
        query = query.where(MediaItem.title.ilike(f"%{title}%"))

    query = query.offset(offset).limit(limit)
    result = db.execute(query)
    return list(result.scalars().all())


@router.get("/{item_id}", response_model=MediaItemRead)
def get_media_item(item_id: int, db: DbSession) -> MediaItem:
    """Get a media item by ID."""
    media_item = db.get(MediaItem, item_id)
    if media_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Media item not found"
        )
    return media_item


@router.patch("/{item_id}", response_model=MediaItemRead)
def update_media_item(
    item_id: int, data: MediaItemUpdate, db: DbSession
) -> MediaItem:
    """Update a media item (partial update)."""
    media_item = db.get(MediaItem, item_id)
    if media_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Media item not found"
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(media_item, field, value)

    db.commit()
    db.refresh(media_item)
    return media_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media_item(item_id: int, db: DbSession) -> None:
    """Delete a media item."""
    media_item = db.get(MediaItem, item_id)
    if media_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Media item not found"
        )

    db.delete(media_item)
    db.commit()
