"""Inline and reply keyboards for bot interactions."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def media_type_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for selecting media type."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎬 Movie", callback_data="media_type:movie"),
                InlineKeyboardButton(text="📺 TV", callback_data="media_type:tv"),
            ],
            [
                InlineKeyboardButton(text="📖 Book", callback_data="media_type:book"),
                InlineKeyboardButton(text="🎭 Play", callback_data="media_type:play"),
            ],
        ]
    )


def spoilers_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for spoilers yes/no."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚠️ Yes, contains spoilers", callback_data="spoilers:yes"),
                InlineKeyboardButton(text="✅ No spoilers", callback_data="spoilers:no"),
            ],
        ]
    )


def skip_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with skip option."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Skip", callback_data="skip")],
        ]
    )


def confirmation_keyboard(action: str = "delete") -> InlineKeyboardMarkup:
    """Create confirmation keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yes", callback_data=f"{action}:yes"),
                InlineKeyboardButton(text="❌ No", callback_data=f"{action}:no"),
            ],
        ]
    )


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
    buttons = []
    
    # Previous button
    if offset > 0:
        prev_offset = max(0, offset - limit)
        cb_data = f"page:{prev_offset}:{limit}"
        if filter_param:
            cb_data += f":{filter_param}"
        buttons.append(InlineKeyboardButton(text="⬅️ Previous", callback_data=cb_data))
    
    # Next button (show if we got a full page of results)
    if total_shown >= limit:
        next_offset = offset + limit
        cb_data = f"page:{next_offset}:{limit}"
        if filter_param:
            cb_data += f":{filter_param}"
        buttons.append(InlineKeyboardButton(text="➡️ Next", callback_data=cb_data))
    
    if not buttons:
        return InlineKeyboardMarkup(inline_keyboard=[])
    
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


def edit_field_keyboard(review_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for selecting which field to edit."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Title", callback_data=f"edit:{review_id}:media_title"),
                InlineKeyboardButton(text="🎬 Type", callback_data=f"edit:{review_id}:media_type"),
            ],
            [
                InlineKeyboardButton(text="📅 Year", callback_data=f"edit:{review_id}:media_year"),
                InlineKeyboardButton(text="⭐ Rating", callback_data=f"edit:{review_id}:rating"),
            ],
            [
                InlineKeyboardButton(text="⚠️ Spoilers", callback_data=f"edit:{review_id}:contains_spoilers"),
                InlineKeyboardButton(text="📄 Text", callback_data=f"edit:{review_id}:text"),
            ],
            [
                InlineKeyboardButton(text="❌ Cancel", callback_data="edit:cancel"),
            ],
        ]
    )


def rating_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for rating selection (1-10)."""
    buttons = []
    row = []
    for i in range(1, 11):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"rating:{i}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)
