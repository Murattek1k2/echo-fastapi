"""Tests for review handlers, specifically back-to-list functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, Message

from bot.keyboards import ReviewListCallback


class TestHandleBackToList:
    """Tests for handle_back_to_list callback handler."""

    @pytest.fixture
    def mock_callback_data(self) -> ReviewListCallback:
        """Create mock callback data."""
        return ReviewListCallback(offset=0, filter_param="")

    @pytest.fixture
    def mock_text_message(self) -> MagicMock:
        """Create mock text message."""
        message = MagicMock(spec=Message)
        message.content_type = ContentType.TEXT
        message.edit_text = AsyncMock()
        message.delete = AsyncMock()
        message.answer = AsyncMock()
        return message

    @pytest.fixture
    def mock_photo_message(self) -> MagicMock:
        """Create mock photo message."""
        message = MagicMock(spec=Message)
        message.content_type = ContentType.PHOTO
        message.edit_text = AsyncMock()
        message.delete = AsyncMock()
        message.answer = AsyncMock()
        return message

    @pytest.fixture
    def mock_callback_with_text_message(self, mock_text_message: MagicMock) -> MagicMock:
        """Create mock callback query with text message."""
        callback = MagicMock(spec=CallbackQuery)
        callback.message = mock_text_message
        callback.answer = AsyncMock()
        return callback

    @pytest.fixture
    def mock_callback_with_photo_message(self, mock_photo_message: MagicMock) -> MagicMock:
        """Create mock callback query with photo message."""
        callback = MagicMock(spec=CallbackQuery)
        callback.message = mock_photo_message
        callback.answer = AsyncMock()
        return callback

    @pytest.mark.asyncio
    async def test_text_message_uses_edit_text(
        self,
        mock_callback_with_text_message: MagicMock,
        mock_callback_data: ReviewListCallback,
    ) -> None:
        """Test that text messages use edit_text method."""
        from bot.handlers.reviews import handle_back_to_list

        mock_reviews = [
            {"id": 1, "media_title": "Test Movie", "media_type": "movie", "rating": 8, "author_name": "User"},
        ]

        with patch("bot.handlers.reviews.get_api_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.list_reviews = AsyncMock(return_value=mock_reviews)
            mock_get_client.return_value = mock_client

            await handle_back_to_list(mock_callback_with_text_message, mock_callback_data)

            # Should use edit_text for text messages
            mock_callback_with_text_message.message.edit_text.assert_called_once()
            # Should NOT use delete + answer pattern
            mock_callback_with_text_message.message.delete.assert_not_called()
            # answer should be called on callback, not on message for sending new message
            mock_callback_with_text_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_photo_message_uses_delete_and_answer(
        self,
        mock_callback_with_photo_message: MagicMock,
        mock_callback_data: ReviewListCallback,
    ) -> None:
        """Test that photo messages use delete + answer pattern."""
        from bot.handlers.reviews import handle_back_to_list

        mock_reviews = [
            {"id": 1, "media_title": "Test Movie", "media_type": "movie", "rating": 8, "author_name": "User"},
        ]

        with patch("bot.handlers.reviews.get_api_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.list_reviews = AsyncMock(return_value=mock_reviews)
            mock_get_client.return_value = mock_client

            await handle_back_to_list(mock_callback_with_photo_message, mock_callback_data)

            # Should use delete + answer for photo messages
            mock_callback_with_photo_message.message.delete.assert_called_once()
            mock_callback_with_photo_message.message.answer.assert_called_once()
            # Should NOT use edit_text for photo messages
            mock_callback_with_photo_message.message.edit_text.assert_not_called()
            # callback.answer should also be called
            mock_callback_with_photo_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_photo_message_deletion_error_handled_gracefully(
        self,
        mock_callback_with_photo_message: MagicMock,
        mock_callback_data: ReviewListCallback,
    ) -> None:
        """Test that deletion errors are handled gracefully for photo messages."""
        from bot.handlers.reviews import handle_back_to_list

        mock_reviews = [
            {"id": 1, "media_title": "Test Movie", "media_type": "movie", "rating": 8, "author_name": "User"},
        ]

        # Make delete raise an exception (simulating message too old)
        mock_callback_with_photo_message.message.delete = AsyncMock(side_effect=Exception("Message too old"))

        with patch("bot.handlers.reviews.get_api_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.list_reviews = AsyncMock(return_value=mock_reviews)
            mock_get_client.return_value = mock_client

            # Should not raise exception
            await handle_back_to_list(mock_callback_with_photo_message, mock_callback_data)

            # Should still try to send new message despite deletion failure
            mock_callback_with_photo_message.message.answer.assert_called_once()
            mock_callback_with_photo_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_reviews_text_message(
        self,
        mock_callback_with_text_message: MagicMock,
        mock_callback_data: ReviewListCallback,
    ) -> None:
        """Test handling no reviews with text message."""
        from bot.handlers.reviews import handle_back_to_list

        with patch("bot.handlers.reviews.get_api_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.list_reviews = AsyncMock(return_value=[])
            mock_get_client.return_value = mock_client

            await handle_back_to_list(mock_callback_with_text_message, mock_callback_data)

            # Should use edit_text for text messages when no reviews
            mock_callback_with_text_message.message.edit_text.assert_called_once()
            mock_callback_with_text_message.message.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_reviews_photo_message(
        self,
        mock_callback_with_photo_message: MagicMock,
        mock_callback_data: ReviewListCallback,
    ) -> None:
        """Test handling no reviews with photo message."""
        from bot.handlers.reviews import handle_back_to_list

        with patch("bot.handlers.reviews.get_api_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.list_reviews = AsyncMock(return_value=[])
            mock_get_client.return_value = mock_client

            await handle_back_to_list(mock_callback_with_photo_message, mock_callback_data)

            # Should use delete + answer for photo messages when no reviews
            mock_callback_with_photo_message.message.delete.assert_called_once()
            mock_callback_with_photo_message.message.answer.assert_called_once()
            mock_callback_with_photo_message.message.edit_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_message_returns_early(
        self,
        mock_callback_data: ReviewListCallback,
    ) -> None:
        """Test that handler returns early when callback has no message."""
        from bot.handlers.reviews import handle_back_to_list

        callback = MagicMock(spec=CallbackQuery)
        callback.message = None
        callback.answer = AsyncMock()

        with patch("bot.handlers.reviews.get_api_client") as mock_get_client:
            # Should return early without calling API
            await handle_back_to_list(callback, mock_callback_data)

            mock_get_client.assert_not_called()
