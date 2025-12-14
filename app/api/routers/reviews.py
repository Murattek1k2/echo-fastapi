"""Reviews CRUD endpoints."""

import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, status
from sqlalchemy import select

from app.db.session import DbSession
from app.models.review import MediaType, Review
from app.schemas.review import ReviewCreate, ReviewRead, ReviewUpdate

router = APIRouter(prefix="/reviews", tags=["Reviews"])

# Max file size for image uploads (5MB)
MAX_IMAGE_SIZE = 5 * 1024 * 1024

# Directory for uploaded files
UPLOADS_DIR = os.getenv("UPLOADS_DIR", "uploads")


@router.post("/", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
def create_review(data: ReviewCreate, db: DbSession) -> Review:
    """Create a new review."""
    review = Review(
        author_name=data.author_name,
        media_type=data.media_type,
        media_title=data.media_title,
        media_year=data.media_year,
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
    media_type: MediaType | None = None,
    media_title: str | None = None,
    author_name: str | None = None,
    min_rating: int | None = None,
) -> list[Review]:
    """List reviews with optional filtering and pagination."""
    query = select(Review)

    if media_type is not None:
        query = query.where(Review.media_type == media_type)

    if media_title is not None:
        query = query.where(Review.media_title.ilike(f"%{media_title}%"))

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
    """Delete a review and its associated image files."""
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )

    # Delete associated image files if present (best-effort)
    if review.image_path:
        review_uploads_dir = Path(UPLOADS_DIR) / "reviews" / str(review_id)
        try:
            if review_uploads_dir.exists():
                shutil.rmtree(review_uploads_dir)
        except OSError:
            pass  # Best-effort deletion

    db.delete(review)
    db.commit()


@router.post("/{review_id}/image", response_model=ReviewRead)
async def upload_review_image(
    review_id: int, file: UploadFile, db: DbSession
) -> Review:
    """Upload an image for a review."""
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )

    # Validate content type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    # Read file content and validate size
    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {MAX_IMAGE_SIZE // (1024 * 1024)}MB",
        )

    # Generate safe filename
    extension = ""
    if file.filename and "." in file.filename:
        extension = "." + file.filename.rsplit(".", 1)[-1].lower()
    safe_filename = f"{uuid.uuid4().hex}{extension}"

    # Create directory and save file
    review_uploads_dir = Path(UPLOADS_DIR) / "reviews" / str(review_id)
    review_uploads_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = review_uploads_dir / safe_filename
    file_path.write_bytes(content)

    # Update review with image path
    relative_path = f"{UPLOADS_DIR}/reviews/{review_id}/{safe_filename}"
    review.image_path = relative_path
    db.commit()
    db.refresh(review)

    return review
