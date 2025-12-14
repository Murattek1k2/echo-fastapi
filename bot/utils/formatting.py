"""Message formatting utilities for Telegram bot."""

import html
from typing import Any

from bot.i18n import ru


def escape_html(text: str) -> str:
    """Escape HTML special characters for Telegram messages."""
    return html.escape(text)


def format_media_type(media_type: str) -> str:
    """Format media type with emoji (Russian)."""
    return ru.FMT_MEDIA_TYPE.get(media_type, f"📝 {media_type.title()}")


def format_media_type_short(media_type: str) -> str:
    """Format media type without emoji (Russian)."""
    return ru.FMT_MEDIA_TYPE_SHORT.get(media_type, media_type.title())


def format_rating(rating: int) -> str:
    """Format rating with stars."""
    stars = "⭐" * min(rating, 5)
    if rating > 5:
        stars += "🌟" * (rating - 5)
    return ru.FMT_RATING.format(stars, rating)


def format_spoilers(contains_spoilers: bool) -> str:
    """Format spoilers flag (Russian)."""
    if contains_spoilers:
        return ru.FMT_SPOILERS_YES
    return ru.FMT_SPOILERS_NO


def format_review_summary(review: dict[str, Any]) -> str:
    """Format a brief review summary for list view (Russian).
    
    Args:
        review: Review data dictionary
        
    Returns:
        Formatted HTML string
    """
    review_id = review.get("id", "?")
    title = escape_html(review.get("media_title", "Unknown"))
    media_type = review.get("media_type", "unknown")
    rating = review.get("rating", 0)
    author = escape_html(review.get("author_name", "Аноним"))
    
    return ru.FMT_REVIEW_SUMMARY.format(
        id=review_id,
        media_type=format_media_type(media_type),
        title=title,
        rating=format_rating(rating),
        author=author,
    )


def format_review_detail(review: dict[str, Any]) -> str:
    """Format a detailed review view (Russian).
    
    Args:
        review: Review data dictionary
        
    Returns:
        Formatted HTML string
    """
    review_id = review.get("id", "?")
    title = escape_html(review.get("media_title", "Unknown"))
    media_type = review.get("media_type", "unknown")
    year = review.get("media_year")
    rating = review.get("rating", 0)
    author = escape_html(review.get("author_name", "Аноним"))
    text = escape_html(review.get("text", ""))
    contains_spoilers = review.get("contains_spoilers", False)
    created_at = review.get("created_at", "")
    updated_at = review.get("updated_at", "")
    
    # Format year
    year_str = f" ({year})" if year else ""
    
    # Format dates (just date part)
    created_date = created_at[:10] if created_at else ""
    updated_date = updated_at[:10] if updated_at else ""
    
    created_str = ru.FMT_CREATED.format(created_date) if created_date else ""
    updated_str = ""
    if updated_date and updated_date != created_date:
        updated_str = "\n" + ru.FMT_UPDATED.format(updated_date)
    
    return ru.FMT_REVIEW_DETAIL.format(
        id=review_id,
        media_type=format_media_type(media_type),
        title=title,
        year=year_str,
        rating=format_rating(rating),
        spoilers=format_spoilers(contains_spoilers),
        text=text,
        author=ru.FMT_AUTHOR.format(author),
        created=created_str,
        updated=updated_str,
    )


def format_photo_caption(review: dict[str, Any]) -> str:
    """Format a short caption for photo message (max 1024 chars, Russian).
    
    Args:
        review: Review data dictionary
        
    Returns:
        Formatted HTML string suitable for photo caption
    """
    title = escape_html(review.get("media_title", ""))
    media_type = review.get("media_type", "")
    year = review.get("media_year")
    rating = review.get("rating", 0)
    
    year_str = f"({year})" if year else ""
    media_type_str = format_media_type_short(media_type)
    
    caption = ru.FMT_PHOTO_CAPTION.format(
        title=title,
        media_type=media_type_str,
        year=year_str,
        rating=format_rating(rating),
    )
    
    # Ensure caption is within Telegram's limit
    if len(caption) > 1024:
        caption = caption[:1020] + "..."
    
    return caption


def format_review_created(review: dict[str, Any]) -> str:
    """Format message for newly created review (Russian).
    
    Args:
        review: Review data dictionary
        
    Returns:
        Formatted HTML string
    """
    review_id = review.get("id", "?")
    title = escape_html(review.get("media_title", "Unknown"))
    
    return ru.MSG_REVIEW_CREATED.format(id=review_id, title=title)


def format_review_updated(review: dict[str, Any]) -> str:
    """Format message for updated review (Russian).
    
    Args:
        review: Review data dictionary
        
    Returns:
        Formatted HTML string
    """
    review_id = review.get("id", "?")
    return ru.MSG_REVIEW_UPDATED.format(review_id)


def format_review_deleted(review_id: int) -> str:
    """Format message for deleted review (Russian).
    
    Args:
        review_id: Deleted review ID
        
    Returns:
        Formatted HTML string
    """
    return ru.MSG_REVIEW_DELETED.format(review_id)


def format_error(message: str) -> str:
    """Format error message (Russian).
    
    Args:
        message: Error message
        
    Returns:
        Formatted HTML string
    """
    return f"❌ <b>Ошибка:</b> {escape_html(message)}"


def get_author_name(user: Any) -> str:
    """Get author name from Telegram user.
    
    Uses username if available, else first_name + last_name, else tg_{user_id}.
    
    Args:
        user: Telegram User object
        
    Returns:
        Author name string
    """
    if user.username:
        return user.username
    
    name_parts = []
    if user.first_name:
        name_parts.append(user.first_name)
    if user.last_name:
        name_parts.append(user.last_name)
    
    if name_parts:
        return " ".join(name_parts)
    
    return f"tg_{user.id}"


# Help and welcome text (Russian)
HELP_TEXT = ru.HELP_TEXT
WELCOME_TEXT = ru.WELCOME_TEXT
