"""Simple in-memory rate limiter for anti-spam protection."""

import time
from collections import defaultdict
from typing import NamedTuple


class RateLimitEntry(NamedTuple):
    """Rate limit entry for a user."""
    
    count: int
    window_start: float


class RateLimiter:
    """Simple in-memory rate limiter.
    
    Limits users to a maximum number of requests per time window.
    """
    
    def __init__(
        self,
        max_requests: int = 30,
        window_seconds: float = 60.0,
    ) -> None:
        """Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._entries: dict[int, RateLimitEntry] = defaultdict(
            lambda: RateLimitEntry(0, time.time())
        )
    
    def is_allowed(self, user_id: int) -> bool:
        """Check if a user is allowed to make a request.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if the request is allowed
        """
        now = time.time()
        entry = self._entries[user_id]
        
        # Check if we're in a new window
        if now - entry.window_start >= self.window_seconds:
            # Reset the window
            self._entries[user_id] = RateLimitEntry(1, now)
            return True
        
        # Check if we've exceeded the limit
        if entry.count >= self.max_requests:
            return False
        
        # Increment the counter
        self._entries[user_id] = RateLimitEntry(entry.count + 1, entry.window_start)
        return True
    
    def get_retry_after(self, user_id: int) -> float:
        """Get seconds until rate limit resets for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Seconds until the window resets
        """
        entry = self._entries.get(user_id)
        if entry is None:
            return 0.0
        
        elapsed = time.time() - entry.window_start
        remaining = self.window_seconds - elapsed
        return max(0.0, remaining)
    
    def cleanup(self) -> None:
        """Remove expired entries to free memory."""
        now = time.time()
        expired_users = [
            user_id
            for user_id, entry in self._entries.items()
            if now - entry.window_start >= self.window_seconds * 2
        ]
        for user_id in expired_users:
            del self._entries[user_id]


# Global rate limiter instance
rate_limiter = RateLimiter()
