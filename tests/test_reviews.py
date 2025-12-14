"""Tests for reviews CRUD endpoints."""

import io
from pathlib import Path

from fastapi.testclient import TestClient


def test_create_review_and_fetch_it_back(client: TestClient) -> None:
    """Test creating a review and reading it back."""
    # Create a review
    create_response = client.post(
        "/reviews/",
        json={
            "author_name": "Alice",
            "media_type": "movie",
            "media_title": "Test Movie",
            "media_year": 2023,
            "rating": 8,
            "text": "Great movie!",
            "contains_spoilers": False,
        },
    )
    assert create_response.status_code == 201
    data = create_response.json()
    assert data["author_name"] == "Alice"
    assert data["media_type"] == "movie"
    assert data["media_title"] == "Test Movie"
    assert data["media_year"] == 2023
    assert data["rating"] == 8
    assert data["text"] == "Great movie!"
    assert data["contains_spoilers"] is False
    assert data["image_url"] is None
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    review_id = data["id"]

    # Fetch it back
    get_response = client.get(f"/reviews/{review_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["id"] == review_id
    assert get_data["media_title"] == "Test Movie"


def test_list_reviews_with_media_type_filter(client: TestClient) -> None:
    """Test listing reviews filtered by media_type."""
    # Create reviews for different media types
    client.post(
        "/reviews/",
        json={
            "author_name": "Alice",
            "media_type": "movie",
            "media_title": "Action Movie",
            "rating": 8,
            "text": "Great!",
        },
    )
    client.post(
        "/reviews/",
        json={
            "author_name": "Bob",
            "media_type": "book",
            "media_title": "Mystery Book",
            "rating": 9,
            "text": "Amazing!",
        },
    )
    client.post(
        "/reviews/",
        json={
            "author_name": "Carol",
            "media_type": "movie",
            "media_title": "Comedy Movie",
            "rating": 7,
            "text": "Good!",
        },
    )

    # Filter by media_type=movie
    response = client.get("/reviews/", params={"media_type": "movie"})
    assert response.status_code == 200
    reviews = response.json()
    assert len(reviews) == 2
    assert all(r["media_type"] == "movie" for r in reviews)


def test_list_reviews_with_min_rating_filter(client: TestClient) -> None:
    """Test listing reviews filtered by minimum rating."""
    # Create reviews with different ratings
    client.post(
        "/reviews/",
        json={
            "author_name": "Alice",
            "media_type": "movie",
            "media_title": "Movie 1",
            "rating": 3,
            "text": "Low rating",
        },
    )
    client.post(
        "/reviews/",
        json={
            "author_name": "Bob",
            "media_type": "movie",
            "media_title": "Movie 2",
            "rating": 7,
            "text": "Medium rating",
        },
    )
    client.post(
        "/reviews/",
        json={
            "author_name": "Carol",
            "media_type": "movie",
            "media_title": "Movie 3",
            "rating": 9,
            "text": "High rating",
        },
    )

    # Filter by min_rating
    response = client.get("/reviews/", params={"min_rating": 7})
    assert response.status_code == 200
    reviews = response.json()
    assert len(reviews) == 2
    assert all(r["rating"] >= 7 for r in reviews)


def test_upload_image_to_review(client: TestClient, temp_uploads_dir: str) -> None:
    """Test uploading an image to a review and confirming the response contains image_url."""
    # Create a review first
    create_response = client.post(
        "/reviews/",
        json={
            "author_name": "Alice",
            "media_type": "movie",
            "media_title": "Test Movie",
            "rating": 8,
            "text": "Great movie!",
        },
    )
    assert create_response.status_code == 201
    review_id = create_response.json()["id"]

    # Upload an image with valid JPEG signature
    # JPEG starts with FF D8 FF
    jpeg_header = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01"
    test_image = io.BytesIO(jpeg_header + b"\x00" * 100)
    upload_response = client.post(
        f"/reviews/{review_id}/image",
        files={"file": ("test_image.jpg", test_image, "image/jpeg")},
    )
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert upload_data["image_url"] is not None
    assert upload_data["image_url"].startswith("/")
    assert "reviews" in upload_data["image_url"]
    assert str(review_id) in upload_data["image_url"]

    # Verify by fetching the review again
    get_response = client.get(f"/reviews/{review_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["image_url"] is not None
    assert get_data["image_url"] == upload_data["image_url"]

    # Verify file exists on disk
    image_path_relative = get_data["image_path"]
    # The path in the response is relative to UPLOADS_DIR setting, need to construct actual path
    full_path = Path(temp_uploads_dir) / "reviews" / str(review_id)
    assert full_path.exists()
    files = list(full_path.iterdir())
    assert len(files) == 1


def test_delete_review_with_image_cleanup(client: TestClient, temp_uploads_dir: str) -> None:
    """Test that deleting a review also cleans up its image files."""
    # Create a review
    create_response = client.post(
        "/reviews/",
        json={
            "author_name": "Alice",
            "media_type": "movie",
            "media_title": "Test Movie",
            "rating": 8,
            "text": "Great movie!",
        },
    )
    assert create_response.status_code == 201
    review_id = create_response.json()["id"]

    # Upload an image with valid JPEG signature
    jpeg_header = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01"
    test_image = io.BytesIO(jpeg_header + b"\x00" * 100)
    upload_response = client.post(
        f"/reviews/{review_id}/image",
        files={"file": ("test_image.jpg", test_image, "image/jpeg")},
    )
    assert upload_response.status_code == 200

    # Verify directory exists
    review_dir = Path(temp_uploads_dir) / "reviews" / str(review_id)
    assert review_dir.exists()

    # Delete the review
    delete_response = client.delete(f"/reviews/{review_id}")
    assert delete_response.status_code == 204

    # Verify review is gone
    get_response = client.get(f"/reviews/{review_id}")
    assert get_response.status_code == 404

    # Verify image directory is cleaned up
    assert not review_dir.exists()


def test_review_rating_validation(client: TestClient) -> None:
    """Test that rating must be between 1 and 10."""
    # Rating too low
    response = client.post(
        "/reviews/",
        json={
            "author_name": "Test",
            "media_type": "movie",
            "media_title": "Test Movie",
            "rating": 0,
            "text": "Test",
        },
    )
    assert response.status_code == 422

    # Rating too high
    response = client.post(
        "/reviews/",
        json={
            "author_name": "Test",
            "media_type": "movie",
            "media_title": "Test Movie",
            "rating": 11,
            "text": "Test",
        },
    )
    assert response.status_code == 422


def test_update_review(client: TestClient) -> None:
    """Test partial update of a review."""
    # Create review
    review_response = client.post(
        "/reviews/",
        json={
            "author_name": "TestAuthor",
            "media_type": "book",
            "media_title": "Update Review Test",
            "rating": 5,
            "text": "Original text",
        },
    )
    review_id = review_response.json()["id"]

    # Update only rating
    patch_response = client.patch(
        f"/reviews/{review_id}",
        json={"rating": 8},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["rating"] == 8
    assert patch_response.json()["text"] == "Original text"


def test_delete_review(client: TestClient) -> None:
    """Test deleting a review."""
    # Create review
    review_response = client.post(
        "/reviews/",
        json={
            "author_name": "TestAuthor",
            "media_type": "play",
            "media_title": "Delete Review Test",
            "rating": 6,
            "text": "To be deleted",
        },
    )
    review_id = review_response.json()["id"]

    # Delete it
    delete_response = client.delete(f"/reviews/{review_id}")
    assert delete_response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/reviews/{review_id}")
    assert get_response.status_code == 404


def test_health_check(client: TestClient) -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_upload_image_non_image_file_rejected(client: TestClient) -> None:
    """Test that non-image files are rejected."""
    # Create a review first
    create_response = client.post(
        "/reviews/",
        json={
            "author_name": "Alice",
            "media_type": "movie",
            "media_title": "Test Movie",
            "rating": 8,
            "text": "Great movie!",
        },
    )
    assert create_response.status_code == 201
    review_id = create_response.json()["id"]

    # Try to upload a non-image file
    test_file = io.BytesIO(b"not an image")
    upload_response = client.post(
        f"/reviews/{review_id}/image",
        files={"file": ("test.txt", test_file, "text/plain")},
    )
    assert upload_response.status_code == 400
    assert "image" in upload_response.json()["detail"].lower()


def test_upload_image_invalid_signature_rejected(client: TestClient) -> None:
    """Test that files with invalid image signatures are rejected."""
    # Create a review first
    create_response = client.post(
        "/reviews/",
        json={
            "author_name": "Alice",
            "media_type": "movie",
            "media_title": "Test Movie",
            "rating": 8,
            "text": "Great movie!",
        },
    )
    assert create_response.status_code == 201
    review_id = create_response.json()["id"]

    # Try to upload a file with image content-type but invalid signature
    fake_image = io.BytesIO(b"not a real image file")
    upload_response = client.post(
        f"/reviews/{review_id}/image",
        files={"file": ("fake.jpg", fake_image, "image/jpeg")},
    )
    assert upload_response.status_code == 400
    assert "invalid" in upload_response.json()["detail"].lower()


def test_list_reviews_with_media_title_filter(client: TestClient) -> None:
    """Test listing reviews filtered by media_title substring."""
    # Create reviews
    client.post(
        "/reviews/",
        json={
            "author_name": "Alice",
            "media_type": "movie",
            "media_title": "The Matrix",
            "rating": 9,
            "text": "Classic!",
        },
    )
    client.post(
        "/reviews/",
        json={
            "author_name": "Bob",
            "media_type": "movie",
            "media_title": "Matrix Reloaded",
            "rating": 7,
            "text": "Good sequel!",
        },
    )
    client.post(
        "/reviews/",
        json={
            "author_name": "Carol",
            "media_type": "book",
            "media_title": "Harry Potter",
            "rating": 10,
            "text": "Amazing!",
        },
    )

    # Filter by media_title substring
    response = client.get("/reviews/", params={"media_title": "Matrix"})
    assert response.status_code == 200
    reviews = response.json()
    assert len(reviews) == 2
    assert all("Matrix" in r["media_title"] for r in reviews)


def test_create_review_with_large_telegram_id(client: TestClient) -> None:
    """Test creating a review with a large Telegram user ID (exceeds 32-bit integer)."""
    # Telegram IDs can exceed the 32-bit integer max (2,147,483,647)
    # This tests the BigInteger column type for author_telegram_id
    large_telegram_id = 7712027002  # This is from the original bug report
    
    create_response = client.post(
        "/reviews/",
        json={
            "author_name": "Zulfat_Dev",
            "author_telegram_id": large_telegram_id,
            "media_type": "movie",
            "media_title": "Таксист",
            "media_year": 2021,
            "rating": 9,
            "text": "Текст отзыва",
            "contains_spoilers": False,
        },
    )
    assert create_response.status_code == 201
    data = create_response.json()
    assert data["author_name"] == "Zulfat_Dev"
    assert data["author_telegram_id"] == large_telegram_id
    assert data["media_title"] == "Таксист"
    assert data["rating"] == 9
