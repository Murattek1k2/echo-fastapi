"""Tests for formatting utilities."""

import pytest
from unittest.mock import MagicMock

from bot.utils.formatting import (
    escape_html,
    format_media_type,
    format_photo_caption,
    format_rating,
    format_spoilers,
    format_review_summary,
    format_review_detail,
    format_review_created,
    format_review_updated,
    format_review_deleted,
    format_error,
    get_author_name,
)


class TestEscapeHtml:
    """Tests for HTML escaping."""

    def test_escape_special_characters(self) -> None:
        """Test that special characters are escaped."""
        assert escape_html("<script>") == "&lt;script&gt;"
        assert escape_html("a & b") == "a &amp; b"
        assert escape_html('"quoted"') == "&quot;quoted&quot;"

    def test_preserve_regular_text(self) -> None:
        """Test that regular text is preserved."""
        assert escape_html("Hello World") == "Hello World"
        assert escape_html("Rating: 8/10") == "Rating: 8/10"


class TestFormatMediaType:
    """Tests for media type formatting (Russian)."""

    def test_movie_emoji(self) -> None:
        """Test movie gets correct emoji."""
        result = format_media_type("movie")
        assert "🎬" in result
        assert "Фильм" in result

    def test_tv_emoji(self) -> None:
        """Test TV gets correct emoji."""
        result = format_media_type("tv")
        assert "📺" in result
        assert "Сериал" in result

    def test_book_emoji(self) -> None:
        """Test book gets correct emoji."""
        result = format_media_type("book")
        assert "📖" in result
        assert "Книга" in result

    def test_play_emoji(self) -> None:
        """Test play gets correct emoji."""
        result = format_media_type("play")
        assert "🎭" in result
        assert "Спектакль" in result

    def test_unknown_type(self) -> None:
        """Test unknown type gets default emoji."""
        result = format_media_type("unknown")
        assert "📝" in result


class TestFormatRating:
    """Tests for rating formatting."""

    def test_low_rating(self) -> None:
        """Test low rating formatting."""
        result = format_rating(3)
        assert "⭐" in result
        assert "3/10" in result

    def test_high_rating(self) -> None:
        """Test high rating formatting."""
        result = format_rating(9)
        assert "⭐" in result or "🌟" in result
        assert "9/10" in result

    def test_max_rating(self) -> None:
        """Test max rating formatting."""
        result = format_rating(10)
        assert "10/10" in result


class TestFormatSpoilers:
    """Tests for spoilers flag formatting (Russian)."""

    def test_contains_spoilers(self) -> None:
        """Test spoilers warning."""
        result = format_spoilers(True)
        assert "⚠️" in result
        assert "спойлер" in result.lower()

    def test_no_spoilers(self) -> None:
        """Test no spoilers indicator."""
        result = format_spoilers(False)
        assert "✅" in result
        assert "без спойлеров" in result.lower()


class TestFormatReviewSummary:
    """Tests for review summary formatting."""

    def test_basic_summary(self) -> None:
        """Test basic review summary."""
        review = {
            "id": 1,
            "media_title": "Test Movie",
            "media_type": "movie",
            "rating": 8,
            "author_name": "TestUser",
        }
        result = format_review_summary(review)
        
        assert "#1" in result
        assert "Test Movie" in result
        assert "TestUser" in result
        assert "8" in result

    def test_escapes_html_in_title(self) -> None:
        """Test that HTML in title is escaped."""
        review = {
            "id": 1,
            "media_title": "<script>alert('xss')</script>",
            "media_type": "movie",
            "rating": 8,
            "author_name": "User",
        }
        result = format_review_summary(review)
        
        assert "<script>" not in result
        assert "&lt;script&gt;" in result


class TestFormatReviewDetail:
    """Tests for detailed review formatting."""

    def test_full_review(self) -> None:
        """Test full review detail formatting."""
        review = {
            "id": 42,
            "media_title": "Inception",
            "media_type": "movie",
            "media_year": 2010,
            "rating": 9,
            "author_name": "CinemaFan",
            "text": "Mind-bending masterpiece!",
            "contains_spoilers": False,
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "image_url": None,
        }
        result = format_review_detail(review)
        
        assert "#42" in result
        assert "Inception" in result
        assert "2010" in result
        assert "9/10" in result or "9" in result
        assert "CinemaFan" in result
        assert "Mind-bending masterpiece!" in result
        assert "2024-01-15" in result

    def test_review_with_image(self) -> None:
        """Test review with image - now handled separately by photo caption."""
        review = {
            "id": 1,
            "media_title": "Test",
            "media_type": "movie",
            "media_year": None,
            "rating": 8,
            "author_name": "User",
            "text": "Good",
            "contains_spoilers": False,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "image_url": "/uploads/test.jpg",
        }
        # format_review_detail now doesn't include image info (image is sent separately)
        result = format_review_detail(review)
        # The detail format should still work
        assert "#1" in result
        assert "Test" in result

    def test_review_without_year(self) -> None:
        """Test review without year doesn't show parentheses."""
        review = {
            "id": 1,
            "media_title": "Test",
            "media_type": "movie",
            "media_year": None,
            "rating": 8,
            "author_name": "User",
            "text": "Good",
            "contains_spoilers": False,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "image_url": None,
        }
        result = format_review_detail(review)
        
        # Should not have empty parentheses
        assert "()" not in result


class TestFormatPhotoCaption:
    """Tests for photo caption formatting."""

    def test_caption_is_short(self) -> None:
        """Test that caption is <= 1024 chars."""
        review = {
            "media_title": "A" * 500,
            "media_type": "movie",
            "media_year": 2024,
            "rating": 10,
        }
        result = format_photo_caption(review)
        assert len(result) <= 1024

    def test_caption_includes_title_and_rating(self) -> None:
        """Test caption includes basic info."""
        review = {
            "media_title": "Test Movie",
            "media_type": "movie",
            "media_year": 2024,
            "rating": 8,
        }
        result = format_photo_caption(review)
        assert "Test Movie" in result
        assert "8/10" in result


class TestFormatReviewCreated:
    """Tests for created review message (Russian)."""

    def test_success_message(self) -> None:
        """Test success message format."""
        review = {"id": 123, "media_title": "New Movie"}
        result = format_review_created(review)
        
        assert "✅" in result
        assert "123" in result
        assert "New Movie" in result


class TestFormatReviewUpdated:
    """Tests for updated review message (Russian)."""

    def test_update_message(self) -> None:
        """Test update message format."""
        review = {"id": 456}
        result = format_review_updated(review)
        
        assert "✅" in result
        assert "456" in result
        # Russian: "обновлён"
        assert "обновлён" in result.lower()


class TestFormatReviewDeleted:
    """Tests for deleted review message (Russian)."""

    def test_delete_message(self) -> None:
        """Test delete message format."""
        result = format_review_deleted(789)
        
        assert "🗑️" in result
        assert "#789" in result
        # Russian: "удалён"
        assert "удалён" in result.lower()


class TestFormatError:
    """Tests for error message formatting (Russian)."""

    def test_error_format(self) -> None:
        """Test error message format."""
        result = format_error("Something went wrong")
        
        assert "❌" in result
        assert "Something went wrong" in result

    def test_escapes_html_in_error(self) -> None:
        """Test that HTML in error is escaped."""
        result = format_error("<b>error</b>")
        
        # The error message content should be escaped
        assert "&lt;b&gt;error&lt;/b&gt;" in result
        # The formatting <b>Ошибка:</b> is intentional (Russian)
        assert "<b>Ошибка:</b>" in result


class TestGetAuthorName:
    """Tests for author name extraction."""

    def test_username_priority(self) -> None:
        """Test that username is used when available."""
        user = MagicMock()
        user.username = "john_doe"
        user.first_name = "John"
        user.last_name = "Doe"
        user.id = 12345
        
        result = get_author_name(user)
        
        assert result == "john_doe"

    def test_full_name_fallback(self) -> None:
        """Test fallback to first and last name."""
        user = MagicMock()
        user.username = None
        user.first_name = "John"
        user.last_name = "Doe"
        user.id = 12345
        
        result = get_author_name(user)
        
        assert result == "John Doe"

    def test_first_name_only(self) -> None:
        """Test using first name only when no last name."""
        user = MagicMock()
        user.username = None
        user.first_name = "John"
        user.last_name = None
        user.id = 12345
        
        result = get_author_name(user)
        
        assert result == "John"

    def test_id_fallback(self) -> None:
        """Test fallback to user ID."""
        user = MagicMock()
        user.username = None
        user.first_name = None
        user.last_name = None
        user.id = 12345
        
        result = get_author_name(user)
        
        assert result == "tg_12345"


class TestImageUrlHandling:
    """Tests for API client image URL handling."""

    def test_absolute_url_from_relative(self) -> None:
        """Test building absolute URL from relative path."""
        from bot.api_client import ReviewsApiClient
        
        client = ReviewsApiClient("http://localhost:8000")
        result = client.get_absolute_image_url("/uploads/test.jpg")
        
        assert result == "http://localhost:8000/uploads/test.jpg"

    def test_absolute_url_already_absolute(self) -> None:
        """Test that already absolute URLs are unchanged."""
        from bot.api_client import ReviewsApiClient
        
        client = ReviewsApiClient("http://localhost:8000")
        result = client.get_absolute_image_url("https://example.com/image.jpg")
        
        assert result == "https://example.com/image.jpg"
