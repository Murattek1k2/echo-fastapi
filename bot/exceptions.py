"""Custom exceptions for API client errors."""


class ApiError(Exception):
    """Base exception for API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize API error."""
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ApiNotFound(ApiError):
    """Resource not found (404)."""

    def __init__(self, message: str = "Resource not found") -> None:
        """Initialize not found error."""
        super().__init__(message, status_code=404)


class ApiValidationError(ApiError):
    """Validation error (422)."""

    def __init__(self, message: str = "Validation error", details: list | None = None) -> None:
        """Initialize validation error."""
        self.details = details or []
        super().__init__(message, status_code=422)


class ApiUnavailable(ApiError):
    """API is unavailable (connection error, timeout, 5xx)."""

    def __init__(self, message: str = "API is temporarily unavailable") -> None:
        """Initialize unavailable error."""
        super().__init__(message, status_code=503)


class ApiBadRequest(ApiError):
    """Bad request (400)."""

    def __init__(self, message: str = "Bad request") -> None:
        """Initialize bad request error."""
        super().__init__(message, status_code=400)
