"""Image upload handler for reviews."""

import re

from aiogram import F, Router
from aiogram.types import Message

from bot.api_client import ReviewsApiClient
from bot.exceptions import ApiNotFound, ApiUnavailable
from bot.logging_config import get_logger
from bot.rate_limiter import rate_limiter
from bot.utils.formatting import format_error, format_review_updated

logger = get_logger(__name__)

router = Router()


def get_api_client() -> ReviewsApiClient:
    """Get API client instance. Override this in tests."""
    from bot.config import get_settings
    settings = get_settings()
    return ReviewsApiClient(settings.api_base_url, settings.request_timeout)


def extract_review_id_from_message(text: str | None) -> int | None:
    """Extract review ID from a message text.
    
    Looks for patterns like "Review #123" or "ID: 123".
    
    Args:
        text: Message text to search
        
    Returns:
        Review ID if found, None otherwise
    """
    if not text:
        return None
    
    # Look for "Review #123" pattern
    match = re.search(r"Review #(\d+)", text)
    if match:
        return int(match.group(1))
    
    # Look for "ID: 123" pattern
    match = re.search(r"ID:\s*(\d+)", text)
    if match:
        return int(match.group(1))
    
    # Look for "#123" at start of line
    match = re.search(r"^#(\d+)", text, re.MULTILINE)
    if match:
        return int(match.group(1))
    
    return None


@router.message(F.photo, F.reply_to_message)
async def handle_photo_reply(message: Message) -> None:
    """Handle photo replies to upload image to a review.
    
    When a user replies to a bot message containing a review ID with a photo,
    this uploads the image to that review.
    """
    if not message.from_user or not message.reply_to_message:
        return
    
    if not rate_limiter.is_allowed(message.from_user.id):
        retry_after = int(rate_limiter.get_retry_after(message.from_user.id))
        await message.answer(
            format_error(f"Too many requests. Please wait {retry_after} seconds."),
            parse_mode="HTML",
        )
        return
    
    # Get the text from the replied message
    reply_text = message.reply_to_message.text or message.reply_to_message.caption
    review_id = extract_review_id_from_message(reply_text)
    
    if review_id is None:
        await message.answer(
            "💡 To upload an image, reply to a message that contains a review ID.\n\n"
            "For example, reply with a photo to a message from <code>/review 1</code>",
            parse_mode="HTML",
        )
        return
    
    # Get the largest photo
    if not message.photo:
        return
    
    photo = message.photo[-1]
    
    try:
        # Download the photo
        from aiogram import Bot
        bot: Bot = message.bot  # type: ignore
        file = await bot.get_file(photo.file_id)
        if not file.file_path:
            await message.answer(format_error("Failed to get file from Telegram."), parse_mode="HTML")
            return
        
        file_content = await bot.download_file(file.file_path)
        if not file_content:
            await message.answer(format_error("Failed to download file."), parse_mode="HTML")
            return
        
        image_data = file_content.read()
        
        # Determine filename
        filename = f"telegram_photo_{photo.file_id[-8:]}.jpg"
        
        # Upload to the API
        client = get_api_client()
        review = await client.upload_review_image(
            review_id=review_id,
            image_data=image_data,
            filename=filename,
            content_type="image/jpeg",
        )
        
        await message.answer(
            f"🖼️ <b>Image uploaded successfully!</b>\n\n"
            f"{format_review_updated(review)}",
            parse_mode="HTML",
        )
        
    except ApiNotFound:
        await message.answer(format_error(f"Review #{review_id} not found."), parse_mode="HTML")
    except ApiUnavailable:
        await message.answer(
            format_error("The API is temporarily unavailable. Please try again later."),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.exception("Failed to upload image")
        await message.answer(format_error(f"Failed to upload image: {e}"), parse_mode="HTML")
