"""Message formatting utilities for Telegram bot."""

import html
from typing import Any


def escape_html(text: str) -> str:
    """Escape HTML special characters for Telegram messages."""
    return html.escape(text)


def format_media_type(media_type: str) -> str:
    """Format media type with emoji."""
    emoji_map = {
        "movie": "🎬",
        "tv": "📺",
        "book": "📖",
        "play": "🎭",
    }
    emoji = emoji_map.get(media_type, "📝")
    return f"{emoji} {media_type.title()}"


def format_rating(rating: int) -> str:
    """Format rating with stars."""
    stars = "⭐" * min(rating, 5)
    if rating > 5:
        stars += "🌟" * (rating - 5)
    return f"{stars} {rating}/10"


def format_spoilers(contains_spoilers: bool) -> str:
    """Format spoilers flag."""
    if contains_spoilers:
        return "⚠️ Contains spoilers"
    return "✅ No spoilers"


def format_review_summary(review: dict[str, Any]) -> str:
    """Format a brief review summary for list view.
    
    Args:
        review: Review data dictionary
        
    Returns:
        Formatted HTML string
    """
    review_id = review.get("id", "?")
    title = escape_html(review.get("media_title", "Unknown"))
    media_type = review.get("media_type", "unknown")
    rating = review.get("rating", 0)
    author = escape_html(review.get("author_name", "Anonymous"))
    
    return (
        f"<b>#{review_id}</b> {format_media_type(media_type)}\n"
        f"<b>{title}</b>\n"
        f"{format_rating(rating)} by {author}"
    )


def format_review_detail(review: dict[str, Any]) -> str:
    """Format a detailed review view.
    
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
    author = escape_html(review.get("author_name", "Anonymous"))
    text = escape_html(review.get("text", ""))
    contains_spoilers = review.get("contains_spoilers", False)
    created_at = review.get("created_at", "")
    updated_at = review.get("updated_at", "")
    image_url = review.get("image_url")
    
    # Format year
    year_str = f" ({year})" if year else ""
    
    # Format dates (just date part)
    created_date = created_at[:10] if created_at else ""
    updated_date = updated_at[:10] if updated_at else ""
    
    lines = [
        f"<b>Review #{review_id}</b>",
        "",
        f"{format_media_type(media_type)}: <b>{title}</b>{year_str}",
        format_rating(rating),
        format_spoilers(contains_spoilers),
        "",
        f"<i>{text}</i>",
        "",
        f"👤 Author: {author}",
    ]
    
    if created_date:
        lines.append(f"📅 Created: {created_date}")
    if updated_date and updated_date != created_date:
        lines.append(f"✏️ Updated: {updated_date}")
    if image_url:
        lines.append(f"🖼️ Has image attached")
    
    return "\n".join(lines)


def format_review_created(review: dict[str, Any]) -> str:
    """Format message for newly created review.
    
    Args:
        review: Review data dictionary
        
    Returns:
        Formatted HTML string
    """
    review_id = review.get("id", "?")
    title = escape_html(review.get("media_title", "Unknown"))
    
    return (
        f"✅ <b>Review created successfully!</b>\n\n"
        f"ID: <code>{review_id}</code>\n"
        f"Title: {title}\n\n"
        f"Use <code>/review {review_id}</code> to view it."
    )


def format_review_updated(review: dict[str, Any]) -> str:
    """Format message for updated review.
    
    Args:
        review: Review data dictionary
        
    Returns:
        Formatted HTML string
    """
    review_id = review.get("id", "?")
    
    return (
        f"✅ <b>Review #{review_id} updated successfully!</b>\n\n"
        f"Use <code>/review {review_id}</code> to view it."
    )


def format_review_deleted(review_id: int) -> str:
    """Format message for deleted review.
    
    Args:
        review_id: Deleted review ID
        
    Returns:
        Formatted HTML string
    """
    return f"🗑️ <b>Review #{review_id} has been deleted.</b>"


def format_error(message: str) -> str:
    """Format error message.
    
    Args:
        message: Error message
        
    Returns:
        Formatted HTML string
    """
    return f"❌ <b>Error:</b> {escape_html(message)}"


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


# Help message content
HELP_TEXT = """
<b>📝 Reviews Bot Commands</b>

<b>Basic Commands:</b>
/start - Welcome message and quick start
/help - Show this help message

<b>Review Management:</b>
/review_new - Create a new review (guided flow)
/reviews - List recent reviews
/reviews movie - List only movie reviews
/reviews min_rating=8 - List reviews with rating ≥ 8
/reviews author=username - List reviews by author

<b>Single Review:</b>
/review &lt;id&gt; - View a specific review
/review_edit &lt;id&gt; - Edit a review
/review_delete &lt;id&gt; - Delete a review

<b>Image Upload:</b>
Reply to a review message with a photo to attach an image.

<b>Examples:</b>
<code>/review 1</code> - View review #1
<code>/review_edit 5</code> - Edit review #5
<code>/reviews movie</code> - List all movie reviews
"""

WELCOME_TEXT = """
👋 <b>Welcome to the Reviews Bot!</b>

This bot helps you manage reviews for movies, TV shows, books, and plays.

<b>Quick Start:</b>
• Use /review_new to create your first review
• Use /reviews to browse existing reviews
• Use /help for all available commands

Happy reviewing! 🌟
"""
