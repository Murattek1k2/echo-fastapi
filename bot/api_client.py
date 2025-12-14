"""Async HTTP client for Reviews API."""

from typing import Any

import httpx

from bot.exceptions import ApiBadRequest, ApiNotFound, ApiUnavailable, ApiValidationError


class ReviewsApiClient:
    """Async HTTP client for interacting with the Reviews API."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        """Initialize the API client.

        Args:
            base_url: Base URL for the Reviews API (e.g., http://localhost:8000)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def _make_request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an HTTP request and handle errors.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            path: API path (e.g., /reviews)
            **kwargs: Additional arguments for httpx request

        Returns:
            HTTP response

        Raises:
            ApiNotFound: Resource not found
            ApiValidationError: Validation error
            ApiBadRequest: Bad request
            ApiUnavailable: API unavailable
        """
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, **kwargs)
        except httpx.TimeoutException as e:
            raise ApiUnavailable(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise ApiUnavailable(f"Failed to connect to API: {e}") from e
        except httpx.RequestError as e:
            raise ApiUnavailable(f"Request failed: {e}") from e

        return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> httpx.Response:
        """Handle HTTP response and raise appropriate exceptions.

        Args:
            response: HTTP response

        Returns:
            Response if successful

        Raises:
            ApiNotFound: 404 response
            ApiValidationError: 422 response
            ApiBadRequest: 400 response
            ApiUnavailable: 5xx response
        """
        if response.status_code == 404:
            detail = self._extract_detail(response)
            raise ApiNotFound(detail)

        if response.status_code == 422:
            try:
                data = response.json()
                details = data.get("detail", [])
                if isinstance(details, list):
                    messages = [
                        f"{err.get('loc', ['?'])[-1]}: {err.get('msg', 'error')}"
                        for err in details
                    ]
                    raise ApiValidationError("Validation error", details=messages)
                raise ApiValidationError(str(details))
            except (ValueError, KeyError):
                raise ApiValidationError("Validation error")

        if response.status_code == 400:
            detail = self._extract_detail(response)
            raise ApiBadRequest(detail)

        if response.status_code >= 500:
            raise ApiUnavailable(f"Server error: {response.status_code}")

        return response

    def _extract_detail(self, response: httpx.Response) -> str:
        """Extract error detail from response."""
        try:
            data = response.json()
            return data.get("detail", "Unknown error")
        except (ValueError, KeyError):
            return "Unknown error"

    async def create_review(
        self,
        author_name: str,
        media_type: str,
        media_title: str,
        rating: int,
        text: str,
        media_year: int | None = None,
        contains_spoilers: bool = False,
        author_telegram_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a new review.

        Args:
            author_name: Author name
            media_type: Media type (movie, tv, book, play)
            media_title: Media title
            rating: Rating (1-10)
            text: Review text
            media_year: Optional media year
            contains_spoilers: Whether the review contains spoilers
            author_telegram_id: Optional Telegram user ID of the author

        Returns:
            Created review data
        """
        payload = {
            "author_name": author_name,
            "media_type": media_type,
            "media_title": media_title,
            "rating": rating,
            "text": text,
            "contains_spoilers": contains_spoilers,
        }
        if media_year is not None:
            payload["media_year"] = media_year
        if author_telegram_id is not None:
            payload["author_telegram_id"] = author_telegram_id

        response = await self._make_request("POST", "/reviews/", json=payload)
        return response.json()

    async def list_reviews(
        self,
        limit: int = 10,
        offset: int = 0,
        media_type: str | None = None,
        min_rating: int | None = None,
        author_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """List reviews with optional filters.

        Args:
            limit: Maximum number of reviews to return
            offset: Offset for pagination
            media_type: Filter by media type
            min_rating: Filter by minimum rating
            author_name: Filter by author name

        Returns:
            List of reviews
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if media_type is not None:
            params["media_type"] = media_type
        if min_rating is not None:
            params["min_rating"] = min_rating
        if author_name is not None:
            params["author_name"] = author_name

        response = await self._make_request("GET", "/reviews/", params=params)
        return response.json()

    async def get_review(self, review_id: int) -> dict[str, Any]:
        """Get a single review by ID.

        Args:
            review_id: Review ID

        Returns:
            Review data
        """
        response = await self._make_request("GET", f"/reviews/{review_id}")
        return response.json()

    async def update_review(
        self,
        review_id: int,
        **fields: Any,
    ) -> dict[str, Any]:
        """Update a review with partial data.

        Args:
            review_id: Review ID
            **fields: Fields to update (rating, text, contains_spoilers, etc.)
                      Use a special _clear_fields list to explicitly clear fields.

        Returns:
            Updated review data
        """
        # Build payload, keeping None values only if they're explicitly meant to clear a field
        # The API's PATCH endpoint uses exclude_unset=True, so we need to send None explicitly
        payload = {}
        clear_fields = fields.pop("_clear_fields", [])
        
        for k, v in fields.items():
            if v is not None:
                payload[k] = v
        
        # Add fields to clear as None
        for field in clear_fields:
            payload[field] = None
        
        response = await self._make_request("PATCH", f"/reviews/{review_id}", json=payload)
        return response.json()

    async def delete_review(self, review_id: int) -> None:
        """Delete a review.

        Args:
            review_id: Review ID
        """
        await self._make_request("DELETE", f"/reviews/{review_id}")

    async def upload_review_image(
        self,
        review_id: int,
        image_data: bytes,
        filename: str,
        content_type: str = "image/jpeg",
    ) -> dict[str, Any]:
        """Upload an image for a review.

        Args:
            review_id: Review ID
            image_data: Image file content
            filename: Original filename
            content_type: MIME type of the image

        Returns:
            Updated review data with image URL
        """
        files = {"file": (filename, image_data, content_type)}
        response = await self._make_request(
            "POST",
            f"/reviews/{review_id}/image",
            files=files,
        )
        return response.json()

    async def health_check(self) -> bool:
        """Check if the API is healthy.

        Returns:
            True if API is healthy
        """
        try:
            response = await self._make_request("GET", "/health")
            return response.json().get("status") == "healthy"
        except ApiUnavailable:
            return False

    async def download_image(self, image_url: str) -> bytes | None:
        """Download an image from the API.

        Args:
            image_url: Image URL path (e.g., /uploads/reviews/1/image.jpg)

        Returns:
            Image bytes or None if failed
        """
        url = f"{self.base_url}{image_url}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return response.content
                return None
        except httpx.RequestError:
            return None

    def get_absolute_image_url(self, image_url: str) -> str:
        """Build absolute URL for an image.

        Args:
            image_url: Relative image URL from API (e.g., /uploads/...)

        Returns:
            Absolute URL
        """
        if image_url.startswith("http"):
            return image_url
        return f"{self.base_url}{image_url}"
