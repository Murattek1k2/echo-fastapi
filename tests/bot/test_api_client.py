"""Tests for the Reviews API client."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from bot.api_client import ReviewsApiClient
from bot.exceptions import ApiNotFound, ApiValidationError, ApiUnavailable, ApiBadRequest


class TestReviewsApiClient:
    """Test cases for ReviewsApiClient."""

    @pytest.fixture
    def client(self) -> ReviewsApiClient:
        """Create a test client."""
        return ReviewsApiClient("http://test-api.local", timeout=5.0)

    @pytest.mark.asyncio
    async def test_create_review_success(self, client: ReviewsApiClient) -> None:
        """Test successful review creation."""
        mock_response = httpx.Response(
            201,
            json={
                "id": 1,
                "author_name": "TestUser",
                "media_type": "movie",
                "media_title": "Test Movie",
                "rating": 8,
                "text": "Great movie!",
                "contains_spoilers": False,
                "media_year": 2023,
                "image_url": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
        )
        
        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.create_review(
                author_name="TestUser",
                media_type="movie",
                media_title="Test Movie",
                rating=8,
                text="Great movie!",
                media_year=2023,
            )
            
            assert result["id"] == 1
            assert result["author_name"] == "TestUser"
            assert result["media_title"] == "Test Movie"
            assert result["rating"] == 8

    @pytest.mark.asyncio
    async def test_get_review_success(self, client: ReviewsApiClient) -> None:
        """Test successful review retrieval."""
        mock_response = httpx.Response(
            200,
            json={
                "id": 1,
                "author_name": "TestUser",
                "media_type": "movie",
                "media_title": "Test Movie",
                "rating": 8,
                "text": "Great movie!",
                "contains_spoilers": False,
                "media_year": None,
                "image_url": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
        )
        
        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.get_review(1)
            
            assert result["id"] == 1
            assert result["media_title"] == "Test Movie"

    @pytest.mark.asyncio
    async def test_get_review_not_found(self, client: ReviewsApiClient) -> None:
        """Test handling of 404 response."""
        mock_response = httpx.Response(
            404,
            json={"detail": "Review not found"},
        )
        
        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            with pytest.raises(ApiNotFound) as exc_info:
                await client.get_review(999)
            
            assert "not found" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_create_review_validation_error(self, client: ReviewsApiClient) -> None:
        """Test handling of validation error response."""
        mock_response = httpx.Response(
            422,
            json={
                "detail": [
                    {"loc": ["body", "rating"], "msg": "ensure this value is less than or equal to 10"},
                ]
            },
        )
        
        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            with pytest.raises(ApiValidationError) as exc_info:
                await client.create_review(
                    author_name="Test",
                    media_type="movie",
                    media_title="Test",
                    rating=15,  # Invalid
                    text="Test",
                )
            
            assert exc_info.value.details

    @pytest.mark.asyncio
    async def test_list_reviews_success(self, client: ReviewsApiClient) -> None:
        """Test successful review listing."""
        mock_response = httpx.Response(
            200,
            json=[
                {"id": 1, "media_title": "Movie 1", "rating": 8},
                {"id": 2, "media_title": "Movie 2", "rating": 7},
            ],
        )
        
        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.list_reviews(limit=10, offset=0)
            
            assert len(result) == 2
            assert result[0]["media_title"] == "Movie 1"

    @pytest.mark.asyncio
    async def test_list_reviews_with_filters(self, client: ReviewsApiClient) -> None:
        """Test review listing with filters."""
        mock_response = httpx.Response(
            200,
            json=[{"id": 1, "media_type": "movie", "rating": 9}],
        )
        
        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.list_reviews(
                limit=5,
                offset=0,
                media_type="movie",
                min_rating=8,
            )
            
            assert len(result) == 1
            # Verify request was made with correct params
            mock_request.assert_called_once()
            call_kwargs = mock_request.call_args.kwargs
            assert call_kwargs["params"]["media_type"] == "movie"
            assert call_kwargs["params"]["min_rating"] == 8

    @pytest.mark.asyncio
    async def test_update_review_success(self, client: ReviewsApiClient) -> None:
        """Test successful review update."""
        mock_response = httpx.Response(
            200,
            json={
                "id": 1,
                "rating": 9,
                "text": "Updated text",
            },
        )
        
        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.update_review(1, rating=9, text="Updated text")
            
            assert result["rating"] == 9

    @pytest.mark.asyncio
    async def test_update_review_clear_fields(self, client: ReviewsApiClient) -> None:
        """Test clearing a field using _clear_fields."""
        mock_response = httpx.Response(
            200,
            json={
                "id": 1,
                "media_year": None,
            },
        )
        
        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.update_review(1, _clear_fields=["media_year"])
            
            # Verify that media_year was sent as None
            call_kwargs = mock_request.call_args.kwargs
            assert call_kwargs["json"]["media_year"] is None

    @pytest.mark.asyncio
    async def test_delete_review_success(self, client: ReviewsApiClient) -> None:
        """Test successful review deletion."""
        mock_response = httpx.Response(204)
        
        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            # Should not raise
            await client.delete_review(1)

    @pytest.mark.asyncio
    async def test_api_timeout(self, client: ReviewsApiClient) -> None:
        """Test handling of timeout."""
        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = httpx.TimeoutException("Connection timed out")
            
            with pytest.raises(ApiUnavailable) as exc_info:
                await client.get_review(1)
            
            assert "timed out" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_api_connection_error(self, client: ReviewsApiClient) -> None:
        """Test handling of connection error."""
        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = httpx.ConnectError("Connection refused")
            
            with pytest.raises(ApiUnavailable) as exc_info:
                await client.get_review(1)
            
            assert "connect" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_api_server_error(self, client: ReviewsApiClient) -> None:
        """Test handling of 5xx errors."""
        mock_response = httpx.Response(500, text="Internal Server Error")
        
        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            with pytest.raises(ApiUnavailable) as exc_info:
                await client.get_review(1)
            
            assert "500" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_upload_image_success(self, client: ReviewsApiClient) -> None:
        """Test successful image upload."""
        mock_response = httpx.Response(
            200,
            json={
                "id": 1,
                "image_url": "/uploads/reviews/1/abc123.jpg",
            },
        )
        
        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.upload_review_image(
                review_id=1,
                image_data=b"fake image data",
                filename="test.jpg",
                content_type="image/jpeg",
            )
            
            assert result["image_url"] is not None

    @pytest.mark.asyncio
    async def test_upload_image_bad_request(self, client: ReviewsApiClient) -> None:
        """Test handling of bad request for image upload."""
        mock_response = httpx.Response(
            400,
            json={"detail": "Invalid image file format"},
        )
        
        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            with pytest.raises(ApiBadRequest) as exc_info:
                await client.upload_review_image(
                    review_id=1,
                    image_data=b"not an image",
                    filename="test.txt",
                )
            
            assert "invalid" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_health_check_success(self, client: ReviewsApiClient) -> None:
        """Test successful health check."""
        mock_response = httpx.Response(
            200,
            json={"status": "healthy"},
        )
        
        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.health_check()
            
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, client: ReviewsApiClient) -> None:
        """Test health check when API is down."""
        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = httpx.ConnectError("Connection refused")
            
            result = await client.health_check()
            
            assert result is False
