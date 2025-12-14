"""Reviews CRUD endpoints."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.db.session import DbSession
from app.models.media_item import MediaItem
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewRead, ReviewUpdate

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
def create_review(data: ReviewCreate, db: DbSession) -> Review:
    """Create a new review for an existing media item."""
    # Check that media item exists
    media_item = db.get(MediaItem, data.media_item_id)
    if media_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Media item not found"
        )

    review = Review(
        media_item_id=data.media_item_id,
        author_name=data.author_name,
        rating=data.rating,
        text=data.text,
        contains_spoilers=data.contains_spoilers,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/", response_model=list[ReviewRead])
def list_reviews(
    db: DbSession,
    limit: int = 100,
    offset: int = 0,
    media_item_id: int | None = None,
    author_name: str | None = None,
    min_rating: int | None = None,
) -> list[Review]:
    """List reviews with optional filtering and pagination."""
    query = select(Review)

    if media_item_id is not None:
        query = query.where(Review.media_item_id == media_item_id)

    if author_name is not None:
        query = query.where(Review.author_name == author_name)

    if min_rating is not None:
        query = query.where(Review.rating >= min_rating)

    query = query.offset(offset).limit(limit)
    result = db.execute(query)
    return list(result.scalars().all())


@router.get("/{review_id}", response_model=ReviewRead)
def get_review(review_id: int, db: DbSession) -> Review:
    """Get a review by ID."""
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )
    return review


@router.patch("/{review_id}", response_model=ReviewRead)
def update_review(review_id: int, data: ReviewUpdate, db: DbSession) -> Review:
    """Update a review (partial update)."""
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)

    db.commit()
    db.refresh(review)
    return review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int, db: DbSession) -> None:
    """Delete a review."""
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )

    db.delete(review)
    db.commit()
