"""Tests for media items CRUD endpoints."""

from fastapi.testclient import TestClient


def test_create_and_read_media_item(client: TestClient) -> None:
    """Test creating a media item and reading it back."""
    # Create a media item
    create_response = client.post(
        "/media-items/",
        json={"type": "movie", "title": "Test Movie", "year": 2023},
    )
    assert create_response.status_code == 201
    data = create_response.json()
    assert data["type"] == "movie"
    assert data["title"] == "Test Movie"
    assert data["year"] == 2023
    assert "id" in data
    assert "created_at" in data
    item_id = data["id"]

    # Read it back
    get_response = client.get(f"/media-items/{item_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["id"] == item_id
    assert get_data["title"] == "Test Movie"


def test_list_media_items_with_filter(client: TestClient) -> None:
    """Test listing media items with type and title filters."""
    # Create multiple items
    client.post("/media-items/", json={"type": "movie", "title": "Action Movie"})
    client.post("/media-items/", json={"type": "book", "title": "Mystery Book"})
    client.post("/media-items/", json={"type": "movie", "title": "Comedy Movie"})

    # List all
    response = client.get("/media-items/")
    assert response.status_code == 200
    assert len(response.json()) == 3

    # Filter by type
    response = client.get("/media-items/", params={"type": "movie"})
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2
    assert all(item["type"] == "movie" for item in items)

    # Filter by title substring
    response = client.get("/media-items/", params={"title": "Mystery"})
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["title"] == "Mystery Book"


def test_update_media_item(client: TestClient) -> None:
    """Test partial update of a media item."""
    # Create item
    create_response = client.post(
        "/media-items/",
        json={"type": "tv", "title": "Original Title"},
    )
    item_id = create_response.json()["id"]

    # Update only title
    patch_response = client.patch(
        f"/media-items/{item_id}",
        json={"title": "Updated Title"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["title"] == "Updated Title"
    assert patch_response.json()["type"] == "tv"


def test_delete_media_item(client: TestClient) -> None:
    """Test deleting a media item."""
    # Create item
    create_response = client.post(
        "/media-items/",
        json={"type": "play", "title": "Stage Play"},
    )
    item_id = create_response.json()["id"]

    # Delete it
    delete_response = client.delete(f"/media-items/{item_id}")
    assert delete_response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/media-items/{item_id}")
    assert get_response.status_code == 404


def test_get_nonexistent_media_item(client: TestClient) -> None:
    """Test 404 for nonexistent media item."""
    response = client.get("/media-items/99999")
    assert response.status_code == 404
