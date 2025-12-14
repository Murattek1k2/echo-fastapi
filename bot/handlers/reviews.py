"""Review CRUD handlers with Russian UI and button-driven flows."""

from typing import Any

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot.api_client import ReviewsApiClient
from bot.config import get_settings
from bot.exceptions import ApiBadRequest, ApiNotFound, ApiUnavailable, ApiValidationError
from bot.i18n import ru
from bot.keyboards import (
    add_image_keyboard,
    confirmation_keyboard,
    edit_field_keyboard,
    filter_menu_keyboard,
    find_method_keyboard,
    main_menu_keyboard,
    media_type_keyboard,
    pagination_keyboard,
    photo_submenu_keyboard,
    rating_keyboard,
    review_actions_keyboard,
    skip_keyboard,
    spoilers_keyboard,
)
from bot.logging_config import get_logger
from bot.rate_limiter import rate_limiter
from bot.states import (
    ReviewCreateStates,
    ReviewDeleteStates,
    ReviewEditStates,
    ReviewFindStates,
    ReviewPhotoStates,
)
from bot.utils.formatting import (
    format_error,
    format_photo_caption,
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
    settings = get_settings()
    return ReviewsApiClient(settings.api_base_url, settings.request_timeout)


async def handle_api_error(message: Message, error: Exception) -> None:
    """Handle API errors with user-friendly messages (Russian)."""
    if isinstance(error, ApiNotFound):
        await message.answer(format_error(ru.ERR_REVIEW_NOT_FOUND), parse_mode="HTML")
    elif isinstance(error, ApiValidationError):
        details = "\n".join(error.details) if error.details else error.message
        await message.answer(format_error(ru.ERR_VALIDATION.format(details)), parse_mode="HTML")
    elif isinstance(error, ApiBadRequest):
        await message.answer(format_error(error.message), parse_mode="HTML")
    elif isinstance(error, ApiUnavailable):
        await message.answer(format_error(ru.ERR_API_UNAVAILABLE), parse_mode="HTML")
    else:
        logger.exception("Unexpected error")
        await message.answer(format_error(ru.ERR_UNEXPECTED), parse_mode="HTML")


async def send_review_with_image(message: Message, review: dict[str, Any], client: ReviewsApiClient) -> bool:
    """Send a review with its image. Returns True if image was sent successfully."""
    image_url = review.get("image_url")
    if not image_url:
        return False
    
    settings = get_settings()
    has_image = bool(review.get("image_url"))
    
    if settings.bot_image_mode == "reupload":
        image_data = await client.download_image(image_url)
        if image_data:
            try:
                photo = BufferedInputFile(image_data, filename="review_image.jpg")
                await message.answer_photo(
                    photo=photo,
                    caption=format_photo_caption(review),
                    parse_mode="HTML",
                )
                await message.answer(
                    format_review_detail(review),
                    parse_mode="HTML",
                    reply_markup=review_actions_keyboard(review["id"], has_image),
                )
                return True
            except Exception as e:
                logger.warning(f"Failed to send re-uploaded image: {e}")
    else:
        full_url = client.get_absolute_image_url(image_url)
        try:
            await message.answer_photo(
                photo=full_url,
                caption=format_photo_caption(review),
                parse_mode="HTML",
            )
            await message.answer(
                format_review_detail(review),
                parse_mode="HTML",
                reply_markup=review_actions_keyboard(review["id"], has_image),
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to send image by URL: {e}")
    
    return False


# ============== BUTTON HANDLERS FOR MAIN MENU ==============

@router.message(F.text == ru.BTN_ADD_REVIEW)
async def btn_add_review(message: Message, state: FSMContext) -> None:
    """Handle add review button."""
    await start_review_creation(message, state)


@router.message(F.text == ru.BTN_FEED)
async def btn_feed(message: Message) -> None:
    """Handle feed button."""
    await show_reviews_feed(message)


@router.message(F.text == ru.BTN_FIND)
async def btn_find(message: Message, state: FSMContext) -> None:
    """Handle find button."""
    await state.clear()
    await state.set_state(ReviewFindStates.select_method)
    await message.answer(
        ru.PROMPT_FIND_METHOD,
        parse_mode="HTML",
        reply_markup=find_method_keyboard(),
    )


# ============== CREATE REVIEW ==============

async def start_review_creation(message: Message, state: FSMContext) -> None:
    """Start the review creation flow."""
    if not message.from_user:
        return
    
    if not rate_limiter.is_allowed(message.from_user.id):
        retry_after = int(rate_limiter.get_retry_after(message.from_user.id))
        await message.answer(
            format_error(ru.ERR_RATE_LIMIT.format(retry_after)),
            parse_mode="HTML",
        )
        return
    
    await state.clear()
    await state.set_state(ReviewCreateStates.media_type)
    await message.answer(
        ru.PROMPT_CREATE_START,
        reply_markup=media_type_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("review_new"))
async def cmd_review_new(message: Message, state: FSMContext) -> None:
    """Start the review creation flow (command)."""
    await start_review_creation(message, state)


@router.callback_query(ReviewCreateStates.media_type, F.data.startswith("media_type:"))
async def process_media_type(callback: CallbackQuery, state: FSMContext) -> None:
    """Process media type selection."""
    if not callback.data or not callback.message:
        return
    
    media_type = callback.data.split(":")[1]
    media_type_display = ru.FMT_MEDIA_TYPE.get(media_type, media_type)
    await state.update_data(media_type=media_type)
    await state.set_state(ReviewCreateStates.media_title)
    
    await callback.message.edit_text(
        ru.PROMPT_ENTER_TITLE.format(media_type_display),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(ReviewCreateStates.media_title)
async def process_media_title(message: Message, state: FSMContext) -> None:
    """Process media title input."""
    if not message.text:
        await message.answer(ru.ERR_ENTER_TEXT_TITLE)
        return
    
    await state.update_data(media_title=message.text.strip())
    await state.set_state(ReviewCreateStates.media_year)
    
    await message.answer(
        ru.PROMPT_ENTER_YEAR,
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
        ru.PROMPT_SELECT_RATING,
        reply_markup=rating_keyboard(),
    )
    await callback.answer()


@router.message(ReviewCreateStates.media_year)
async def process_media_year(message: Message, state: FSMContext) -> None:
    """Process media year input."""
    if not message.text:
        await message.answer(ru.PROMPT_ENTER_YEAR_TEXT)
        return
    
    try:
        year = int(message.text.strip())
        if year < 1800 or year > 2100:
            await message.answer(ru.PROMPT_ENTER_VALID_YEAR)
            return
    except ValueError:
        await message.answer(ru.PROMPT_ENTER_VALID_YEAR_NUMBER)
        return
    
    await state.update_data(media_year=year)
    await state.set_state(ReviewCreateStates.rating)
    
    await message.answer(
        ru.PROMPT_SELECT_RATING,
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
        ru.PROMPT_CONTAINS_SPOILERS,
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
    
    await callback.message.edit_text(ru.PROMPT_ENTER_TEXT)
    await callback.answer()


@router.message(ReviewCreateStates.text)
async def process_review_text(message: Message, state: FSMContext) -> None:
    """Process review text and ask about image."""
    if not message.text or not message.from_user:
        await message.answer(ru.PROMPT_ENTER_TEXT_CONTENT)
        return
    
    await state.update_data(text=message.text.strip())
    await state.set_state(ReviewCreateStates.add_image)
    
    await message.answer(
        ru.PROMPT_ADD_IMAGE,
        reply_markup=add_image_keyboard(),
    )


@router.callback_query(ReviewCreateStates.add_image, F.data.startswith("add_photo:"))
async def process_add_image_choice(callback: CallbackQuery, state: FSMContext) -> None:
    """Process choice to add image or skip."""
    if not callback.data or not callback.message or not callback.from_user:
        return
    
    choice = callback.data.split(":")[1]
    
    if choice == "yes":
        await state.set_state(ReviewCreateStates.waiting_for_image)
        await callback.message.edit_text(ru.PROMPT_SEND_PHOTO)
        await callback.answer()
        return
    
    await create_review_from_state(callback.message, state, callback.from_user)
    await callback.answer()


@router.message(ReviewCreateStates.waiting_for_image, F.photo)
async def process_review_image(message: Message, state: FSMContext) -> None:
    """Process image upload during review creation."""
    if not message.photo or not message.from_user:
        return
    
    photo = message.photo[-1]
    await state.update_data(photo_file_id=photo.file_id)
    
    await create_review_from_state(message, state, message.from_user, upload_image=True)


async def create_review_from_state(
    message_or_callback: Message,
    state: FSMContext,
    user: Any,
    upload_image: bool = False,
) -> None:
    """Create review from FSM state data."""
    data = await state.get_data()
    photo_file_id = data.get("photo_file_id") if upload_image else None
    await state.clear()
    
    author_name = get_author_name(user)
    
    try:
        client = get_api_client()
        review = await client.create_review(
            author_name=author_name,
            media_type=data["media_type"],
            media_title=data["media_title"],
            rating=data["rating"],
            text=data["text"],
            media_year=data.get("media_year"),
            contains_spoilers=data.get("contains_spoilers", False),
        )
        
        if photo_file_id and hasattr(message_or_callback, "bot"):
            try:
                from aiogram import Bot
                bot: Bot = message_or_callback.bot  # type: ignore
                file = await bot.get_file(photo_file_id)
                if file.file_path:
                    file_content = await bot.download_file(file.file_path)
                    if file_content:
                        image_data = file_content.read()
                        await client.upload_review_image(
                            review_id=review["id"],
                            image_data=image_data,
                            filename=f"review_{review['id']}.jpg",
                            content_type="image/jpeg",
                        )
            except Exception as e:
                logger.warning(f"Failed to upload image: {e}")
        
        await message_or_callback.answer(
            format_review_created(review),
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
    except Exception as e:
        await handle_api_error(message_or_callback, e)


# ============== LIST REVIEWS / FEED ==============

async def show_reviews_feed(
    message: Message,
    offset: int = 0,
    limit: int = 5,
    filters: dict[str, Any] | None = None,
    filter_param: str = "",
) -> None:
    """Show reviews feed."""
    if not message.from_user:
        return
    
    if not rate_limiter.is_allowed(message.from_user.id):
        retry_after = int(rate_limiter.get_retry_after(message.from_user.id))
        await message.answer(
            format_error(ru.ERR_RATE_LIMIT.format(retry_after)),
            parse_mode="HTML",
        )
        return
    
    filters = filters or {}
    
    try:
        client = get_api_client()
        reviews = await client.list_reviews(limit=limit, offset=offset, **filters)
        
        if not reviews:
            await message.answer(ru.PROMPT_NO_REVIEWS, parse_mode="HTML")
            return
        
        lines = [ru.PROMPT_REVIEWS_HEADER]
        for review in reviews:
            lines.append(format_review_summary(review))
            lines.append("")
        
        keyboard = pagination_keyboard(offset, limit, len(reviews), filter_param)
        await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        await handle_api_error(message, e)


@router.message(Command("reviews"))
async def cmd_reviews(message: Message, command: CommandObject) -> None:
    """List reviews with optional filters (command)."""
    args = command.args or ""
    filters: dict[str, Any] = {}
    filter_param = ""
    
    if args and args.lower() in ("movie", "tv", "book", "play"):
        filters["media_type"] = args.lower()
        filter_param = f"media_type={args.lower()}"
    else:
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
    
    await show_reviews_feed(message, filters=filters, filter_param=filter_param)


@router.callback_query(F.data.startswith("page:"))
async def handle_pagination(callback: CallbackQuery) -> None:
    """Handle pagination button clicks."""
    if not callback.data or not callback.message:
        return
    
    parts = callback.data.split(":")
    offset = int(parts[1])
    limit = int(parts[2])
    filter_param = parts[3] if len(parts) > 3 else ""
    
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
            await callback.answer(ru.PROMPT_NO_MORE_REVIEWS)
            return
        
        lines = [ru.PROMPT_REVIEWS_HEADER]
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
        await callback.answer(ru.ERR_UNEXPECTED)


# ============== FILTER MENU ==============

@router.callback_query(F.data == "filter:open")
async def open_filter_menu(callback: CallbackQuery) -> None:
    """Open filter menu."""
    if not callback.message:
        return
    
    await callback.message.edit_text(
        ru.PROMPT_FILTER_MENU,
        parse_mode="HTML",
        reply_markup=filter_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("filter:type:"))
async def apply_type_filter(callback: CallbackQuery) -> None:
    """Apply media type filter."""
    if not callback.data or not callback.message:
        return
    
    media_type = callback.data.split(":")[2]
    filter_param = f"media_type={media_type}"
    
    try:
        client = get_api_client()
        reviews = await client.list_reviews(limit=5, offset=0, media_type=media_type)
        
        if not reviews:
            await callback.message.edit_text(ru.PROMPT_NO_REVIEWS, parse_mode="HTML")
            await callback.answer()
            return
        
        lines = [ru.PROMPT_REVIEWS_HEADER]
        for review in reviews:
            lines.append(format_review_summary(review))
            lines.append("")
        
        keyboard = pagination_keyboard(0, 5, len(reviews), filter_param)
        await callback.message.edit_text(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        await callback.answer()
    except Exception as e:
        logger.exception("Filter error")
        await callback.answer(ru.ERR_UNEXPECTED)


@router.callback_query(F.data.startswith("filter:rating:"))
async def apply_rating_filter(callback: CallbackQuery) -> None:
    """Apply minimum rating filter."""
    if not callback.data or not callback.message:
        return
    
    min_rating = int(callback.data.split(":")[2])
    filter_param = f"min_rating={min_rating}"
    
    try:
        client = get_api_client()
        reviews = await client.list_reviews(limit=5, offset=0, min_rating=min_rating)
        
        if not reviews:
            await callback.message.edit_text(ru.PROMPT_NO_REVIEWS, parse_mode="HTML")
            await callback.answer()
            return
        
        lines = [ru.PROMPT_REVIEWS_HEADER]
        for review in reviews:
            lines.append(format_review_summary(review))
            lines.append("")
        
        keyboard = pagination_keyboard(0, 5, len(reviews), filter_param)
        await callback.message.edit_text(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        await callback.answer()
    except Exception as e:
        logger.exception("Filter error")
        await callback.answer(ru.ERR_UNEXPECTED)


@router.callback_query(F.data == "filter:my")
async def apply_my_filter(callback: CallbackQuery) -> None:
    """Apply 'my reviews only' filter."""
    if not callback.message or not callback.from_user:
        return
    
    author_name = get_author_name(callback.from_user)
    filter_param = f"author_name={author_name}"
    
    try:
        client = get_api_client()
        reviews = await client.list_reviews(limit=5, offset=0, author_name=author_name)
        
        if not reviews:
            await callback.message.edit_text(ru.PROMPT_NO_REVIEWS, parse_mode="HTML")
            await callback.answer()
            return
        
        lines = [ru.PROMPT_REVIEWS_HEADER]
        for review in reviews:
            lines.append(format_review_summary(review))
            lines.append("")
        
        keyboard = pagination_keyboard(0, 5, len(reviews), filter_param)
        await callback.message.edit_text(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        await callback.answer()
    except Exception as e:
        logger.exception("Filter error")
        await callback.answer(ru.ERR_UNEXPECTED)


@router.callback_query(F.data == "filter:reset")
async def reset_filter(callback: CallbackQuery) -> None:
    """Reset all filters."""
    if not callback.message:
        return
    
    try:
        client = get_api_client()
        reviews = await client.list_reviews(limit=5, offset=0)
        
        if not reviews:
            await callback.message.edit_text(ru.PROMPT_NO_REVIEWS, parse_mode="HTML")
            await callback.answer()
            return
        
        lines = [ru.PROMPT_REVIEWS_HEADER]
        for review in reviews:
            lines.append(format_review_summary(review))
            lines.append("")
        
        keyboard = pagination_keyboard(0, 5, len(reviews))
        await callback.message.edit_text(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        await callback.answer()
    except Exception as e:
        logger.exception("Reset filter error")
        await callback.answer(ru.ERR_UNEXPECTED)


@router.callback_query(F.data == "filter:cancel")
async def cancel_filter(callback: CallbackQuery) -> None:
    """Cancel filter menu."""
    if not callback.message:
        return
    
    try:
        client = get_api_client()
        reviews = await client.list_reviews(limit=5, offset=0)
        
        if not reviews:
            await callback.message.edit_text(ru.PROMPT_NO_REVIEWS, parse_mode="HTML")
            await callback.answer()
            return
        
        lines = [ru.PROMPT_REVIEWS_HEADER]
        for review in reviews:
            lines.append(format_review_summary(review))
            lines.append("")
        
        keyboard = pagination_keyboard(0, 5, len(reviews))
        await callback.message.edit_text(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        await callback.answer()
    except Exception as e:
        logger.exception("Cancel filter error")
        await callback.answer(ru.ERR_UNEXPECTED)


# ============== FIND REVIEW ==============

@router.callback_query(ReviewFindStates.select_method, F.data.startswith("find:"))
async def process_find_method(callback: CallbackQuery, state: FSMContext) -> None:
    """Process find method selection."""
    if not callback.data or not callback.message:
        return
    
    method = callback.data.split(":")[1]
    
    if method == "cancel":
        await state.clear()
        await callback.message.edit_text(ru.PROMPT_EDIT_CANCELLED)
        await callback.answer()
        return
    
    if method == "by_id":
        await state.set_state(ReviewFindStates.enter_id)
        await callback.message.edit_text(ru.PROMPT_FIND_ENTER_ID)
    elif method == "by_title":
        await state.set_state(ReviewFindStates.enter_title)
        await callback.message.edit_text(ru.PROMPT_FIND_ENTER_TITLE)
    
    await callback.answer()


@router.message(ReviewFindStates.enter_id)
async def find_by_id(message: Message, state: FSMContext) -> None:
    """Find review by ID."""
    if not message.text:
        await message.answer(ru.PROMPT_FIND_INVALID_ID)
        return
    
    try:
        review_id = int(message.text.strip())
    except ValueError:
        await message.answer(ru.PROMPT_FIND_INVALID_ID)
        return
    
    await state.clear()
    await show_single_review(message, review_id)


@router.message(ReviewFindStates.enter_title)
async def find_by_title(message: Message, state: FSMContext) -> None:
    """Find reviews by title substring."""
    if not message.text:
        return
    
    search_term = message.text.strip()
    await state.clear()
    
    try:
        client = get_api_client()
        reviews = await client.list_reviews(limit=50, offset=0)
        
        matching = [r for r in reviews if search_term.lower() in r.get("media_title", "").lower()]
        
        if not matching:
            await message.answer(ru.PROMPT_NO_REVIEWS, parse_mode="HTML")
            return
        
        lines = [ru.PROMPT_REVIEWS_HEADER]
        for review in matching[:10]:
            lines.append(format_review_summary(review))
            lines.append("")
        
        await message.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        await handle_api_error(message, e)


# ============== VIEW SINGLE REVIEW ==============

async def show_single_review(message: Message, review_id: int) -> None:
    """Show a single review with image handling."""
    try:
        client = get_api_client()
        review = await client.get_review(review_id)
        
        has_image = bool(review.get("image_url"))
        
        if has_image:
            if await send_review_with_image(message, review, client):
                return
        
        await message.answer(
            format_review_detail(review),
            parse_mode="HTML",
            reply_markup=review_actions_keyboard(review_id, has_image),
        )
    except Exception as e:
        await handle_api_error(message, e)


@router.message(Command("review"))
async def cmd_review(message: Message, command: CommandObject) -> None:
    """View a single review by ID (command)."""
    if not message.from_user:
        return
    
    if not rate_limiter.is_allowed(message.from_user.id):
        retry_after = int(rate_limiter.get_retry_after(message.from_user.id))
        await message.answer(
            format_error(ru.ERR_RATE_LIMIT.format(retry_after)),
            parse_mode="HTML",
        )
        return
    
    if not command.args:
        await message.answer(
            "Использование: <code>/review &lt;id&gt;</code>\n\nПример: <code>/review 1</code>",
            parse_mode="HTML",
        )
        return
    
    try:
        review_id = int(command.args.strip())
    except ValueError:
        await message.answer(format_error(ru.ERR_INVALID_REVIEW_ID), parse_mode="HTML")
        return
    
    await show_single_review(message, review_id)


# ============== REVIEW ACTIONS ==============

@router.callback_query(F.data.startswith("action:"))
async def handle_review_action(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle review action button clicks."""
    if not callback.data or not callback.message:
        return
    
    parts = callback.data.split(":")
    review_id = int(parts[1])
    action = parts[2]
    
    if action == "edit":
        await start_review_edit(callback, state, review_id)
    elif action == "delete":
        await start_review_delete(callback, state, review_id)
    elif action == "photo":
        await show_photo_submenu(callback, state, review_id)
    
    await callback.answer()


async def start_review_edit(callback: CallbackQuery, state: FSMContext, review_id: int) -> None:
    """Start editing a review."""
    if not callback.message:
        return
    
    await state.clear()
    await state.set_state(ReviewEditStates.select_field)
    await state.update_data(review_id=review_id)
    
    await callback.message.answer(
        ru.PROMPT_EDIT_SELECT_FIELD.format(review_id),
        reply_markup=edit_field_keyboard(review_id),
        parse_mode="HTML",
    )


async def start_review_delete(callback: CallbackQuery, state: FSMContext, review_id: int) -> None:
    """Start deleting a review."""
    if not callback.message:
        return
    
    try:
        client = get_api_client()
        review = await client.get_review(review_id)
        
        await state.clear()
        await state.set_state(ReviewDeleteStates.confirm)
        await state.update_data(review_id=review_id)
        
        await callback.message.answer(
            ru.PROMPT_DELETE_CONFIRM.format(review_id, review.get("media_title", "?")),
            reply_markup=confirmation_keyboard("delete"),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.exception("Failed to get review for delete")


async def show_photo_submenu(callback: CallbackQuery, state: FSMContext, review_id: int) -> None:
    """Show photo submenu."""
    if not callback.message:
        return
    
    try:
        client = get_api_client()
        review = await client.get_review(review_id)
        has_image = bool(review.get("image_url"))
        
        await state.update_data(review_id=review_id)
        
        await callback.message.answer(
            "📷 <b>Управление фото</b>",
            reply_markup=photo_submenu_keyboard(review_id, has_image),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.exception("Failed to get review for photo menu")


# ============== PHOTO MANAGEMENT ==============

@router.callback_query(F.data.startswith("photo:"))
async def handle_photo_action(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle photo submenu actions."""
    if not callback.data or not callback.message:
        return
    
    parts = callback.data.split(":")
    review_id = int(parts[1])
    action = parts[2]
    
    if action == "upload":
        await state.set_state(ReviewPhotoStates.waiting_for_upload)
        await state.update_data(review_id=review_id)
        await callback.message.edit_text(ru.PROMPT_SEND_PHOTO)
    elif action == "delete":
        try:
            client = get_api_client()
            await client.update_review(review_id, _clear_fields=["image_path"])
            await callback.message.edit_text(ru.MSG_IMAGE_DELETED, parse_mode="HTML")
        except Exception as e:
            logger.exception("Failed to delete image")
            await callback.message.edit_text(format_error(str(e)), parse_mode="HTML")
    elif action == "cancel":
        await callback.message.delete()
    
    await callback.answer()


@router.message(ReviewPhotoStates.waiting_for_upload, F.photo)
async def upload_review_photo(message: Message, state: FSMContext) -> None:
    """Upload photo for a review."""
    if not message.photo or not message.from_user:
        return
    
    data = await state.get_data()
    review_id = data.get("review_id")
    await state.clear()
    
    if not review_id:
        await message.answer(format_error(ru.ERR_UNEXPECTED), parse_mode="HTML")
        return
    
    photo = message.photo[-1]
    
    try:
        from aiogram import Bot
        bot: Bot = message.bot  # type: ignore
        file = await bot.get_file(photo.file_id)
        if not file.file_path:
            await message.answer(format_error(ru.ERR_FAILED_TO_DOWNLOAD_IMAGE), parse_mode="HTML")
            return
        
        file_content = await bot.download_file(file.file_path)
        if not file_content:
            await message.answer(format_error(ru.ERR_FAILED_TO_DOWNLOAD_IMAGE), parse_mode="HTML")
            return
        
        image_data = file_content.read()
        
        client = get_api_client()
        await client.upload_review_image(
            review_id=review_id,
            image_data=image_data,
            filename=f"review_{review_id}.jpg",
            content_type="image/jpeg",
        )
        
        await message.answer(ru.MSG_IMAGE_UPLOADED, parse_mode="HTML")
    except Exception as e:
        logger.exception("Failed to upload image")
        await message.answer(format_error(str(e)), parse_mode="HTML")


# ============== EDIT REVIEW ==============

@router.message(Command("review_edit"))
async def cmd_review_edit(message: Message, command: CommandObject, state: FSMContext) -> None:
    """Start editing a review (command)."""
    if not message.from_user:
        return
    
    if not rate_limiter.is_allowed(message.from_user.id):
        retry_after = int(rate_limiter.get_retry_after(message.from_user.id))
        await message.answer(
            format_error(ru.ERR_RATE_LIMIT.format(retry_after)),
            parse_mode="HTML",
        )
        return
    
    if not command.args:
        await message.answer(
            "Использование: <code>/review_edit &lt;id&gt;</code>\n\nПример: <code>/review_edit 1</code>",
            parse_mode="HTML",
        )
        return
    
    try:
        review_id = int(command.args.strip())
    except ValueError:
        await message.answer(format_error(ru.ERR_INVALID_REVIEW_ID), parse_mode="HTML")
        return
    
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
        ru.PROMPT_EDIT_SELECT_FIELD.format(review_id),
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
        await callback.message.edit_text(ru.PROMPT_EDIT_CANCELLED)
        await callback.answer()
        return
    
    review_id = int(parts[1])
    field = parts[2]
    
    await state.update_data(review_id=review_id, edit_field=field)
    
    if field == "media_type":
        await state.set_state(ReviewEditStates.edit_media_type)
        await callback.message.edit_text(
            ru.PROMPT_EDIT_SELECT_TYPE,
            reply_markup=media_type_keyboard(),
        )
    elif field == "rating":
        await state.set_state(ReviewEditStates.edit_rating)
        await callback.message.edit_text(
            ru.PROMPT_EDIT_SELECT_RATING,
            reply_markup=rating_keyboard(),
        )
    elif field == "contains_spoilers":
        await state.set_state(ReviewEditStates.edit_contains_spoilers)
        await callback.message.edit_text(
            ru.PROMPT_EDIT_SPOILERS,
            reply_markup=spoilers_keyboard(),
        )
    elif field == "media_title":
        await state.set_state(ReviewEditStates.edit_media_title)
        await callback.message.edit_text(ru.PROMPT_EDIT_ENTER_TITLE)
    elif field == "media_year":
        await state.set_state(ReviewEditStates.edit_media_year)
        await callback.message.edit_text(
            ru.PROMPT_EDIT_ENTER_YEAR,
            reply_markup=skip_keyboard(),
        )
    elif field == "text":
        await state.set_state(ReviewEditStates.edit_text)
        await callback.message.edit_text(ru.PROMPT_EDIT_ENTER_TEXT)
    
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
        await message.answer(ru.PROMPT_ENTER_TITLE_TEXT)
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
        await message.answer(ru.PROMPT_ENTER_YEAR_TEXT)
        return
    
    try:
        year = int(message.text.strip())
        if year < 1800 or year > 2100:
            await message.answer(ru.PROMPT_ENTER_VALID_YEAR)
            return
    except ValueError:
        await message.answer(ru.PROMPT_ENTER_VALID_YEAR_NUMBER)
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
        await message.answer(ru.PROMPT_ENTER_TEXT_CONTENT)
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
    """Delete a review with confirmation (command)."""
    if not message.from_user:
        return
    
    if not rate_limiter.is_allowed(message.from_user.id):
        retry_after = int(rate_limiter.get_retry_after(message.from_user.id))
        await message.answer(
            format_error(ru.ERR_RATE_LIMIT.format(retry_after)),
            parse_mode="HTML",
        )
        return
    
    if not command.args:
        await message.answer(
            "Использование: <code>/review_delete &lt;id&gt;</code>\n\nПример: <code>/review_delete 1</code>",
            parse_mode="HTML",
        )
        return
    
    try:
        review_id = int(command.args.strip())
    except ValueError:
        await message.answer(format_error(ru.ERR_INVALID_REVIEW_ID), parse_mode="HTML")
        return
    
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
        ru.PROMPT_DELETE_CONFIRM.format(review_id, review.get("media_title", "?")),
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
        await callback.message.edit_text(ru.PROMPT_DELETE_CANCELLED)
        await callback.answer()
        return
    
    try:
        client = get_api_client()
        await client.delete_review(review_id)
        await callback.message.edit_text(format_review_deleted(review_id), parse_mode="HTML")
    except Exception as e:
        await callback.message.edit_text(format_error(str(e)), parse_mode="HTML")
    
    await callback.answer()
