"""Tests for reviews CRUD endpoints."""

from fastapi.testclient import TestClient


def test_create_review_and_filter_by_media_item(client: TestClient) -> None:
    """Test creating a review and listing reviews filtered by media_item_id."""
    # First create a media item
    media_response = client.post(
        "/media-items/",
        json={"type": "movie", "title": "Review Test Movie"},
    )
    media_item_id = media_response.json()["id"]

    # Create a second media item
    media_response2 = client.post(
        "/media-items/",
        json={"type": "book", "title": "Review Test Book"},
    )
    media_item_id2 = media_response2.json()["id"]

    # Create reviews for both
    review1 = client.post(
        "/reviews/",
        json={
            "media_item_id": media_item_id,
            "author_name": "Alice",
            "rating": 8,
            "text": "Great movie!",
            "contains_spoilers": False,
        },
    )
    assert review1.status_code == 201
    review1_data = review1.json()
    assert review1_data["rating"] == 8
    assert review1_data["author_name"] == "Alice"

    review2 = client.post(
        "/reviews/",
        json={
            "media_item_id": media_item_id2,
            "author_name": "Bob",
            "rating": 9,
            "text": "Amazing book!",
        },
    )
    assert review2.status_code == 201

    # List reviews filtered by media_item_id
    response = client.get("/reviews/", params={"media_item_id": media_item_id})
    assert response.status_code == 200
    reviews = response.json()
    assert len(reviews) == 1
    assert reviews[0]["media_item_id"] == media_item_id


def test_review_requires_existing_media_item(client: TestClient) -> None:
    """Test that creating a review for nonexistent media item returns 404."""
    response = client.post(
        "/reviews/",
        json={
            "media_item_id": 99999,
            "author_name": "Test",
            "rating": 5,
            "text": "Test review",
        },
    )
    assert response.status_code == 404


def test_review_rating_validation(client: TestClient) -> None:
    """Test that rating must be between 1 and 10."""
    media_response = client.post(
        "/media-items/",
        json={"type": "movie", "title": "Rating Test"},
    )
    media_item_id = media_response.json()["id"]

    # Rating too low
    response = client.post(
        "/reviews/",
        json={
            "media_item_id": media_item_id,
            "author_name": "Test",
            "rating": 0,
            "text": "Test",
        },
    )
    assert response.status_code == 422

    # Rating too high
    response = client.post(
        "/reviews/",
        json={
            "media_item_id": media_item_id,
            "author_name": "Test",
            "rating": 11,
            "text": "Test",
        },
    )
    assert response.status_code == 422


def test_filter_reviews_by_min_rating(client: TestClient) -> None:
    """Test filtering reviews by minimum rating."""
    # Create media item
    media_response = client.post(
        "/media-items/",
        json={"type": "movie", "title": "Min Rating Test"},
    )
    media_item_id = media_response.json()["id"]

    # Create reviews with different ratings (different authors for unique constraint)
    client.post(
        "/reviews/",
        json={
            "media_item_id": media_item_id,
            "author_name": "Alice",
            "rating": 3,
            "text": "Low rating",
        },
    )
    client.post(
        "/reviews/",
        json={
            "media_item_id": media_item_id,
            "author_name": "Bob",
            "rating": 7,
            "text": "Medium rating",
        },
    )
    client.post(
        "/reviews/",
        json={
            "media_item_id": media_item_id,
            "author_name": "Carol",
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


def test_update_review(client: TestClient) -> None:
    """Test partial update of a review."""
    # Create media item and review
    media_response = client.post(
        "/media-items/",
        json={"type": "book", "title": "Update Review Test"},
    )
    media_item_id = media_response.json()["id"]

    review_response = client.post(
        "/reviews/",
        json={
            "media_item_id": media_item_id,
            "author_name": "TestAuthor",
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
    # Create media item and review
    media_response = client.post(
        "/media-items/",
        json={"type": "play", "title": "Delete Review Test"},
    )
    media_item_id = media_response.json()["id"]

    review_response = client.post(
        "/reviews/",
        json={
            "media_item_id": media_item_id,
            "author_name": "TestAuthor",
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
