"""Inline and reply keyboards for bot interactions."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.i18n import ru


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Create main menu reply keyboard."""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=ru.BTN_ADD_REVIEW))
    builder.row(
        KeyboardButton(text=ru.BTN_FEED),
        KeyboardButton(text=ru.BTN_FIND),
    )
    builder.row(
        KeyboardButton(text=ru.BTN_SETTINGS),
        KeyboardButton(text=ru.BTN_HELP),
    )
    return builder.as_markup(resize_keyboard=True, is_persistent=True)


def media_type_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for selecting media type."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=ru.BTN_MOVIE, callback_data="media_type:movie"),
        InlineKeyboardButton(text=ru.BTN_TV, callback_data="media_type:tv"),
    )
    builder.row(
        InlineKeyboardButton(text=ru.BTN_BOOK, callback_data="media_type:book"),
        InlineKeyboardButton(text=ru.BTN_PLAY, callback_data="media_type:play"),
    )
    return builder.as_markup()


def spoilers_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for spoilers yes/no."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=ru.BTN_SPOILERS_YES, callback_data="spoilers:yes"),
        InlineKeyboardButton(text=ru.BTN_SPOILERS_NO, callback_data="spoilers:no"),
    )
    return builder.as_markup()


def skip_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with skip option."""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=ru.BTN_SKIP, callback_data="skip"))
    return builder.as_markup()


def confirmation_keyboard(action: str = "delete") -> InlineKeyboardMarkup:
    """Create confirmation keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=ru.BTN_YES, callback_data=f"{action}:yes"),
        InlineKeyboardButton(text=ru.BTN_NO, callback_data=f"{action}:no"),
    )
    return builder.as_markup()


def add_image_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for optional image upload step."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=ru.BTN_ADD_PHOTO, callback_data="add_photo:yes"),
        InlineKeyboardButton(text=ru.BTN_SKIP, callback_data="add_photo:skip"),
    )
    return builder.as_markup()


def pagination_keyboard(
    offset: int,
    limit: int,
    total_shown: int,
    filter_param: str = "",
) -> InlineKeyboardMarkup:
    """Create pagination keyboard for review listing.
    
    Args:
        offset: Current offset
        limit: Items per page
        total_shown: Number of items shown on current page
        filter_param: Optional filter parameter string (e.g., "media_type=movie")
    """
    builder = InlineKeyboardBuilder()
    
    # Navigation row
    nav_buttons = []
    if offset > 0:
        prev_offset = max(0, offset - limit)
        cb_data = f"page:{prev_offset}:{limit}"
        if filter_param:
            cb_data += f":{filter_param}"
        nav_buttons.append(InlineKeyboardButton(text=ru.BTN_PREV, callback_data=cb_data))
    
    if total_shown >= limit:
        next_offset = offset + limit
        cb_data = f"page:{next_offset}:{limit}"
        if filter_param:
            cb_data += f":{filter_param}"
        nav_buttons.append(InlineKeyboardButton(text=ru.BTN_NEXT, callback_data=cb_data))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Filter row
    builder.row(
        InlineKeyboardButton(text=ru.BTN_FILTER, callback_data="filter:open"),
        InlineKeyboardButton(text=ru.BTN_RESET, callback_data="filter:reset"),
    )
    
    return builder.as_markup()


def filter_menu_keyboard() -> InlineKeyboardMarkup:
    """Create filter menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=ru.BTN_MOVIE, callback_data="filter:type:movie"),
        InlineKeyboardButton(text=ru.BTN_TV, callback_data="filter:type:tv"),
    )
    builder.row(
        InlineKeyboardButton(text=ru.BTN_BOOK, callback_data="filter:type:book"),
        InlineKeyboardButton(text=ru.BTN_PLAY, callback_data="filter:type:play"),
    )
    builder.row(
        InlineKeyboardButton(text=ru.BTN_MIN_RATING.format(5), callback_data="filter:rating:5"),
        InlineKeyboardButton(text=ru.BTN_MIN_RATING.format(7), callback_data="filter:rating:7"),
        InlineKeyboardButton(text=ru.BTN_MIN_RATING.format(9), callback_data="filter:rating:9"),
    )
    builder.row(
        InlineKeyboardButton(text=ru.BTN_FILTER_MY_ONLY, callback_data="filter:my"),
    )
    builder.row(
        InlineKeyboardButton(text=ru.BTN_CANCEL, callback_data="filter:cancel"),
    )
    return builder.as_markup()


def find_method_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for selecting find method."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=ru.BTN_FIND_BY_ID, callback_data="find:by_id"),
        InlineKeyboardButton(text=ru.BTN_FIND_BY_TITLE, callback_data="find:by_title"),
    )
    builder.row(
        InlineKeyboardButton(text=ru.BTN_CANCEL, callback_data="find:cancel"),
    )
    return builder.as_markup()


def review_actions_keyboard(review_id: int, has_image: bool = False) -> InlineKeyboardMarkup:
    """Create keyboard with review action buttons."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=ru.BTN_EDIT, callback_data=f"action:{review_id}:edit"),
        InlineKeyboardButton(text=ru.BTN_DELETE, callback_data=f"action:{review_id}:delete"),
    )
    builder.row(
        InlineKeyboardButton(text=ru.BTN_PHOTO, callback_data=f"action:{review_id}:photo"),
    )
    return builder.as_markup()


def photo_submenu_keyboard(review_id: int, has_image: bool = False) -> InlineKeyboardMarkup:
    """Create photo submenu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=ru.BTN_UPLOAD_PHOTO, callback_data=f"photo:{review_id}:upload"),
    )
    if has_image:
        builder.row(
            InlineKeyboardButton(text=ru.BTN_DELETE_PHOTO, callback_data=f"photo:{review_id}:delete"),
        )
    builder.row(
        InlineKeyboardButton(text=ru.BTN_CANCEL, callback_data=f"photo:{review_id}:cancel"),
    )
    return builder.as_markup()


def edit_field_keyboard(review_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for selecting which field to edit."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=ru.BTN_EDIT_TITLE, callback_data=f"edit:{review_id}:media_title"),
        InlineKeyboardButton(text=ru.BTN_EDIT_TYPE, callback_data=f"edit:{review_id}:media_type"),
    )
    builder.row(
        InlineKeyboardButton(text=ru.BTN_EDIT_YEAR, callback_data=f"edit:{review_id}:media_year"),
        InlineKeyboardButton(text=ru.BTN_EDIT_RATING, callback_data=f"edit:{review_id}:rating"),
    )
    builder.row(
        InlineKeyboardButton(text=ru.BTN_EDIT_SPOILERS, callback_data=f"edit:{review_id}:contains_spoilers"),
        InlineKeyboardButton(text=ru.BTN_EDIT_TEXT, callback_data=f"edit:{review_id}:text"),
    )
    builder.row(
        InlineKeyboardButton(text=ru.BTN_CANCEL, callback_data="edit:cancel"),
    )
    return builder.as_markup()


def rating_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for rating selection (1-10)."""
    builder = InlineKeyboardBuilder()
    # First row: 1-5
    for i in range(1, 6):
        builder.add(InlineKeyboardButton(text=str(i), callback_data=f"rating:{i}"))
    # Second row: 6-10
    for i in range(6, 11):
        builder.add(InlineKeyboardButton(text=str(i), callback_data=f"rating:{i}"))
    builder.adjust(5, 5)
    return builder.as_markup()
