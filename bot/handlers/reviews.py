"""Review CRUD handlers."""

import re
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.api_client import ReviewsApiClient
from bot.exceptions import ApiBadRequest, ApiNotFound, ApiUnavailable, ApiValidationError
from bot.keyboards import (
    confirmation_keyboard,
    edit_field_keyboard,
    media_type_keyboard,
    pagination_keyboard,
    rating_keyboard,
    skip_keyboard,
    spoilers_keyboard,
)
from bot.logging_config import get_logger
from bot.rate_limiter import rate_limiter
from bot.states import ReviewCreateStates, ReviewDeleteStates, ReviewEditStates
from bot.utils.formatting import (
    format_error,
    format_review_created,
    format_review_deleted,
    format_review_detail,
    format_review_summary,
    format_review_updated,
    get_author_name,
)

logger = get_logger(__name__)

router = Router()


def get_api_client() -> ReviewsApiClient:
    """Get API client instance. Override this in tests."""
    from bot.config import get_settings
    settings = get_settings()
    return ReviewsApiClient(settings.api_base_url, settings.request_timeout)


async def handle_api_error(message: Message, error: Exception) -> None:
    """Handle API errors with user-friendly messages."""
    if isinstance(error, ApiNotFound):
        await message.answer(format_error("Review not found."), parse_mode="HTML")
    elif isinstance(error, ApiValidationError):
        details = "\n".join(error.details) if error.details else error.message
        await message.answer(format_error(f"Validation error:\n{details}"), parse_mode="HTML")
    elif isinstance(error, ApiBadRequest):
        await message.answer(format_error(error.message), parse_mode="HTML")
    elif isinstance(error, ApiUnavailable):
        await message.answer(
            format_error("The API is temporarily unavailable. Please try again later."),
            parse_mode="HTML",
        )
    else:
        logger.exception("Unexpected error")
        await message.answer(
            format_error("An unexpected error occurred. Please try again."),
            parse_mode="HTML",
        )


# ============== CREATE REVIEW ==============

@router.message(Command("review_new"))
async def cmd_review_new(message: Message, state: FSMContext) -> None:
    """Start the review creation flow."""
    if not message.from_user:
        return
    
    if not rate_limiter.is_allowed(message.from_user.id):
        retry_after = int(rate_limiter.get_retry_after(message.from_user.id))
        await message.answer(
            format_error(f"Too many requests. Please wait {retry_after} seconds."),
            parse_mode="HTML",
        )
        return
    
    await state.clear()
    await state.set_state(ReviewCreateStates.media_type)
    await message.answer(
        "📝 <b>Create a new review</b>\n\nSelect the media type:",
        reply_markup=media_type_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(ReviewCreateStates.media_type, F.data.startswith("media_type:"))
async def process_media_type(callback: CallbackQuery, state: FSMContext) -> None:
    """Process media type selection."""
    if not callback.data or not callback.message:
        return
    
    media_type = callback.data.split(":")[1]
    await state.update_data(media_type=media_type)
    await state.set_state(ReviewCreateStates.media_title)
    
    await callback.message.edit_text(
        f"📝 Media type: <b>{media_type.title()}</b>\n\nEnter the title:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(ReviewCreateStates.media_title)
async def process_media_title(message: Message, state: FSMContext) -> None:
    """Process media title input."""
    if not message.text:
        await message.answer("Please enter a text title.")
        return
    
    await state.update_data(media_title=message.text.strip())
    await state.set_state(ReviewCreateStates.media_year)
    
    await message.answer(
        "📅 Enter the year (or skip):",
        reply_markup=skip_keyboard(),
    )


@router.callback_query(ReviewCreateStates.media_year, F.data == "skip")
async def skip_media_year(callback: CallbackQuery, state: FSMContext) -> None:
    """Skip media year."""
    if not callback.message:
        return
    
    await state.update_data(media_year=None)
    await state.set_state(ReviewCreateStates.rating)
    
    await callback.message.edit_text(
        "⭐ Select your rating (1-10):",
        reply_markup=rating_keyboard(),
    )
    await callback.answer()


@router.message(ReviewCreateStates.media_year)
async def process_media_year(message: Message, state: FSMContext) -> None:
    """Process media year input."""
    if not message.text:
        await message.answer("Please enter a year or click Skip.")
        return
    
    try:
        year = int(message.text.strip())
        if year < 1800 or year > 2100:
            await message.answer("Please enter a valid year (1800-2100).")
            return
    except ValueError:
        await message.answer("Please enter a valid year number.")
        return
    
    await state.update_data(media_year=year)
    await state.set_state(ReviewCreateStates.rating)
    
    await message.answer(
        "⭐ Select your rating (1-10):",
        reply_markup=rating_keyboard(),
    )


@router.callback_query(ReviewCreateStates.rating, F.data.startswith("rating:"))
async def process_rating(callback: CallbackQuery, state: FSMContext) -> None:
    """Process rating selection."""
    if not callback.data or not callback.message:
        return
    
    rating = int(callback.data.split(":")[1])
    await state.update_data(rating=rating)
    await state.set_state(ReviewCreateStates.contains_spoilers)
    
    await callback.message.edit_text(
        "⚠️ Does your review contain spoilers?",
        reply_markup=spoilers_keyboard(),
    )
    await callback.answer()


@router.callback_query(ReviewCreateStates.contains_spoilers, F.data.startswith("spoilers:"))
async def process_spoilers(callback: CallbackQuery, state: FSMContext) -> None:
    """Process spoilers selection."""
    if not callback.data or not callback.message:
        return
    
    contains_spoilers = callback.data.split(":")[1] == "yes"
    await state.update_data(contains_spoilers=contains_spoilers)
    await state.set_state(ReviewCreateStates.text)
    
    await callback.message.edit_text(
        "📝 Now write your review text:",
    )
    await callback.answer()


@router.message(ReviewCreateStates.text)
async def process_review_text(message: Message, state: FSMContext) -> None:
    """Process review text and create the review."""
    if not message.text or not message.from_user:
        await message.answer("Please enter your review text.")
        return
    
    data = await state.get_data()
    await state.clear()
    
    author_name = get_author_name(message.from_user)
    
    try:
        client = get_api_client()
        review = await client.create_review(
            author_name=author_name,
            media_type=data["media_type"],
            media_title=data["media_title"],
            rating=data["rating"],
            text=message.text.strip(),
            media_year=data.get("media_year"),
            contains_spoilers=data.get("contains_spoilers", False),
        )
        await message.answer(format_review_created(review), parse_mode="HTML")
    except Exception as e:
        await handle_api_error(message, e)


# ============== LIST REVIEWS ==============

@router.message(Command("reviews"))
async def cmd_reviews(message: Message, command: CommandObject) -> None:
    """List reviews with optional filters."""
    if not message.from_user:
        return
    
    if not rate_limiter.is_allowed(message.from_user.id):
        retry_after = int(rate_limiter.get_retry_after(message.from_user.id))
        await message.answer(
            format_error(f"Too many requests. Please wait {retry_after} seconds."),
            parse_mode="HTML",
        )
        return
    
    # Parse filters from command arguments
    args = command.args or ""
    filters: dict[str, Any] = {}
    filter_param = ""
    
    # Check for media_type filter (e.g., "/reviews movie")
    if args and args.lower() in ("movie", "tv", "book", "play"):
        filters["media_type"] = args.lower()
        filter_param = f"media_type={args.lower()}"
    else:
        # Check for key=value filters
        for part in args.split():
            if "=" in part:
                key, value = part.split("=", 1)
                if key == "min_rating":
                    try:
                        filters["min_rating"] = int(value)
                        filter_param = f"min_rating={value}"
                    except ValueError:
                        pass
                elif key == "author":
                    filters["author_name"] = value
                    filter_param = f"author_name={value}"
    
    try:
        client = get_api_client()
        reviews = await client.list_reviews(limit=5, offset=0, **filters)
        
        if not reviews:
            await message.answer("📭 No reviews found.", parse_mode="HTML")
            return
        
        lines = ["<b>📚 Recent Reviews</b>\n"]
        for review in reviews:
            lines.append(format_review_summary(review))
            lines.append("")
        
        keyboard = pagination_keyboard(0, 5, len(reviews), filter_param)
        await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        await handle_api_error(message, e)


@router.callback_query(F.data.startswith("page:"))
async def handle_pagination(callback: CallbackQuery) -> None:
    """Handle pagination button clicks."""
    if not callback.data or not callback.message:
        return
    
    parts = callback.data.split(":")
    offset = int(parts[1])
    limit = int(parts[2])
    filter_param = parts[3] if len(parts) > 3 else ""
    
    # Parse filter param
    filters: dict[str, Any] = {}
    if filter_param:
        key, value = filter_param.split("=", 1)
        if key == "min_rating":
            filters["min_rating"] = int(value)
        elif key == "media_type":
            filters["media_type"] = value
        elif key == "author_name":
            filters["author_name"] = value
    
    try:
        client = get_api_client()
        reviews = await client.list_reviews(limit=limit, offset=offset, **filters)
        
        if not reviews:
            await callback.answer("No more reviews.")
            return
        
        lines = ["<b>📚 Reviews</b>\n"]
        for review in reviews:
            lines.append(format_review_summary(review))
            lines.append("")
        
        keyboard = pagination_keyboard(offset, limit, len(reviews), filter_param)
        await callback.message.edit_text(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        await callback.answer()
    except Exception as e:
        logger.exception("Pagination error")
        await callback.answer("Error loading reviews.")


# ============== VIEW SINGLE REVIEW ==============

@router.message(Command("review"))
async def cmd_review(message: Message, command: CommandObject) -> None:
    """View a single review by ID."""
    if not message.from_user:
        return
    
    if not rate_limiter.is_allowed(message.from_user.id):
        retry_after = int(rate_limiter.get_retry_after(message.from_user.id))
        await message.answer(
            format_error(f"Too many requests. Please wait {retry_after} seconds."),
            parse_mode="HTML",
        )
        return
    
    if not command.args:
        await message.answer(
            "Usage: <code>/review &lt;id&gt;</code>\n\nExample: <code>/review 1</code>",
            parse_mode="HTML",
        )
        return
    
    try:
        review_id = int(command.args.strip())
    except ValueError:
        await message.answer(format_error("Invalid review ID. Please provide a number."), parse_mode="HTML")
        return
    
    try:
        client = get_api_client()
        review = await client.get_review(review_id)
        
        image_url = review.get("image_url")
        if image_url:
            # Try to send as photo
            try:
                full_url = f"{client.base_url}{image_url}"
                await message.answer_photo(
                    photo=full_url,
                    caption=format_review_detail(review),
                    parse_mode="HTML",
                )
                return
            except Exception:
                # Fall back to text with image link
                logger.warning("Failed to send image as photo, falling back to text")
        
        await message.answer(format_review_detail(review), parse_mode="HTML")
    except Exception as e:
        await handle_api_error(message, e)


# ============== EDIT REVIEW ==============

@router.message(Command("review_edit"))
async def cmd_review_edit(message: Message, command: CommandObject, state: FSMContext) -> None:
    """Start editing a review."""
    if not message.from_user:
        return
    
    if not rate_limiter.is_allowed(message.from_user.id):
        retry_after = int(rate_limiter.get_retry_after(message.from_user.id))
        await message.answer(
            format_error(f"Too many requests. Please wait {retry_after} seconds."),
            parse_mode="HTML",
        )
        return
    
    if not command.args:
        await message.answer(
            "Usage: <code>/review_edit &lt;id&gt;</code>\n\nExample: <code>/review_edit 1</code>",
            parse_mode="HTML",
        )
        return
    
    try:
        review_id = int(command.args.strip())
    except ValueError:
        await message.answer(format_error("Invalid review ID."), parse_mode="HTML")
        return
    
    # Verify the review exists
    try:
        client = get_api_client()
        await client.get_review(review_id)
    except Exception as e:
        await handle_api_error(message, e)
        return
    
    await state.clear()
    await state.set_state(ReviewEditStates.select_field)
    await state.update_data(review_id=review_id)
    
    await message.answer(
        f"✏️ <b>Edit Review #{review_id}</b>\n\nSelect the field to edit:",
        reply_markup=edit_field_keyboard(review_id),
        parse_mode="HTML",
    )


@router.callback_query(ReviewEditStates.select_field, F.data.startswith("edit:"))
async def process_field_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Process field selection for editing."""
    if not callback.data or not callback.message:
        return
    
    parts = callback.data.split(":")
    if len(parts) < 2:
        return
    
    if parts[1] == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Edit cancelled.")
        await callback.answer()
        return
    
    review_id = int(parts[1])
    field = parts[2]
    
    await state.update_data(review_id=review_id, edit_field=field)
    
    if field == "media_type":
        await state.set_state(ReviewEditStates.edit_media_type)
        await callback.message.edit_text(
            "Select new media type:",
            reply_markup=media_type_keyboard(),
        )
    elif field == "rating":
        await state.set_state(ReviewEditStates.edit_rating)
        await callback.message.edit_text(
            "Select new rating:",
            reply_markup=rating_keyboard(),
        )
    elif field == "contains_spoilers":
        await state.set_state(ReviewEditStates.edit_contains_spoilers)
        await callback.message.edit_text(
            "Does the review contain spoilers?",
            reply_markup=spoilers_keyboard(),
        )
    elif field == "media_title":
        await state.set_state(ReviewEditStates.edit_media_title)
        await callback.message.edit_text("Enter new title:")
    elif field == "media_year":
        await state.set_state(ReviewEditStates.edit_media_year)
        await callback.message.edit_text(
            "Enter new year (or click Skip to remove):",
            reply_markup=skip_keyboard(),
        )
    elif field == "text":
        await state.set_state(ReviewEditStates.edit_text)
        await callback.message.edit_text("Enter new review text:")
    
    await callback.answer()


@router.callback_query(ReviewEditStates.edit_media_type, F.data.startswith("media_type:"))
async def edit_media_type(callback: CallbackQuery, state: FSMContext) -> None:
    """Update media type."""
    if not callback.data or not callback.message:
        return
    
    media_type = callback.data.split(":")[1]
    data = await state.get_data()
    review_id = data["review_id"]
    
    try:
        client = get_api_client()
        review = await client.update_review(review_id, media_type=media_type)
        await state.clear()
        await callback.message.edit_text(format_review_updated(review), parse_mode="HTML")
    except Exception as e:
        await state.clear()
        await callback.message.edit_text(format_error(str(e)), parse_mode="HTML")
    
    await callback.answer()


@router.callback_query(ReviewEditStates.edit_rating, F.data.startswith("rating:"))
async def edit_rating(callback: CallbackQuery, state: FSMContext) -> None:
    """Update rating."""
    if not callback.data or not callback.message:
        return
    
    rating = int(callback.data.split(":")[1])
    data = await state.get_data()
    review_id = data["review_id"]
    
    try:
        client = get_api_client()
        review = await client.update_review(review_id, rating=rating)
        await state.clear()
        await callback.message.edit_text(format_review_updated(review), parse_mode="HTML")
    except Exception as e:
        await state.clear()
        await callback.message.edit_text(format_error(str(e)), parse_mode="HTML")
    
    await callback.answer()


@router.callback_query(ReviewEditStates.edit_contains_spoilers, F.data.startswith("spoilers:"))
async def edit_spoilers(callback: CallbackQuery, state: FSMContext) -> None:
    """Update spoilers flag."""
    if not callback.data or not callback.message:
        return
    
    contains_spoilers = callback.data.split(":")[1] == "yes"
    data = await state.get_data()
    review_id = data["review_id"]
    
    try:
        client = get_api_client()
        review = await client.update_review(review_id, contains_spoilers=contains_spoilers)
        await state.clear()
        await callback.message.edit_text(format_review_updated(review), parse_mode="HTML")
    except Exception as e:
        await state.clear()
        await callback.message.edit_text(format_error(str(e)), parse_mode="HTML")
    
    await callback.answer()


@router.message(ReviewEditStates.edit_media_title)
async def edit_media_title(message: Message, state: FSMContext) -> None:
    """Update media title."""
    if not message.text:
        await message.answer("Please enter a title.")
        return
    
    data = await state.get_data()
    review_id = data["review_id"]
    
    try:
        client = get_api_client()
        review = await client.update_review(review_id, media_title=message.text.strip())
        await state.clear()
        await message.answer(format_review_updated(review), parse_mode="HTML")
    except Exception as e:
        await state.clear()
        await handle_api_error(message, e)


@router.callback_query(ReviewEditStates.edit_media_year, F.data == "skip")
async def edit_media_year_skip(callback: CallbackQuery, state: FSMContext) -> None:
    """Remove media year."""
    if not callback.message:
        return
    
    data = await state.get_data()
    review_id = data["review_id"]
    
    try:
        client = get_api_client()
        # Use _clear_fields to explicitly set media_year to None
        review = await client.update_review(review_id, _clear_fields=["media_year"])
        await state.clear()
        await callback.message.edit_text(format_review_updated(review), parse_mode="HTML")
    except Exception as e:
        await state.clear()
        await callback.message.edit_text(format_error(str(e)), parse_mode="HTML")
    
    await callback.answer()


@router.message(ReviewEditStates.edit_media_year)
async def edit_media_year(message: Message, state: FSMContext) -> None:
    """Update media year."""
    if not message.text:
        await message.answer("Please enter a year.")
        return
    
    try:
        year = int(message.text.strip())
        if year < 1800 or year > 2100:
            await message.answer("Please enter a valid year (1800-2100).")
            return
    except ValueError:
        await message.answer("Please enter a valid year number.")
        return
    
    data = await state.get_data()
    review_id = data["review_id"]
    
    try:
        client = get_api_client()
        review = await client.update_review(review_id, media_year=year)
        await state.clear()
        await message.answer(format_review_updated(review), parse_mode="HTML")
    except Exception as e:
        await state.clear()
        await handle_api_error(message, e)


@router.message(ReviewEditStates.edit_text)
async def edit_text(message: Message, state: FSMContext) -> None:
    """Update review text."""
    if not message.text:
        await message.answer("Please enter review text.")
        return
    
    data = await state.get_data()
    review_id = data["review_id"]
    
    try:
        client = get_api_client()
        review = await client.update_review(review_id, text=message.text.strip())
        await state.clear()
        await message.answer(format_review_updated(review), parse_mode="HTML")
    except Exception as e:
        await state.clear()
        await handle_api_error(message, e)


# ============== DELETE REVIEW ==============

@router.message(Command("review_delete"))
async def cmd_review_delete(message: Message, command: CommandObject, state: FSMContext) -> None:
    """Delete a review with confirmation."""
    if not message.from_user:
        return
    
    if not rate_limiter.is_allowed(message.from_user.id):
        retry_after = int(rate_limiter.get_retry_after(message.from_user.id))
        await message.answer(
            format_error(f"Too many requests. Please wait {retry_after} seconds."),
            parse_mode="HTML",
        )
        return
    
    if not command.args:
        await message.answer(
            "Usage: <code>/review_delete &lt;id&gt;</code>\n\nExample: <code>/review_delete 1</code>",
            parse_mode="HTML",
        )
        return
    
    try:
        review_id = int(command.args.strip())
    except ValueError:
        await message.answer(format_error("Invalid review ID."), parse_mode="HTML")
        return
    
    # Verify the review exists
    try:
        client = get_api_client()
        review = await client.get_review(review_id)
    except Exception as e:
        await handle_api_error(message, e)
        return
    
    await state.clear()
    await state.set_state(ReviewDeleteStates.confirm)
    await state.update_data(review_id=review_id)
    
    await message.answer(
        f"⚠️ <b>Delete Review #{review_id}?</b>\n\n"
        f"Title: {review.get('media_title', 'Unknown')}\n\n"
        "This action cannot be undone.",
        reply_markup=confirmation_keyboard("delete"),
        parse_mode="HTML",
    )


@router.callback_query(ReviewDeleteStates.confirm, F.data.startswith("delete:"))
async def confirm_delete(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle delete confirmation."""
    if not callback.data or not callback.message:
        return
    
    action = callback.data.split(":")[1]
    data = await state.get_data()
    review_id = data["review_id"]
    
    await state.clear()
    
    if action == "no":
        await callback.message.edit_text("❌ Delete cancelled.")
        await callback.answer()
        return
    
    try:
        client = get_api_client()
        await client.delete_review(review_id)
        await callback.message.edit_text(format_review_deleted(review_id), parse_mode="HTML")
    except Exception as e:
        await callback.message.edit_text(format_error(str(e)), parse_mode="HTML")
    
    await callback.answer()
