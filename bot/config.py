"""Bot configuration using pydantic-settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Bot configuration settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Required settings
    bot_token: str = Field(..., description="Telegram Bot API token")
    api_base_url: str = Field(
        default="http://localhost:8000",
        description="Base URL for the Reviews API",
    )

    # Optional settings
    request_timeout: float = Field(
        default=30.0,
        description="Timeout for API requests in seconds",
    )
    admin_chat_id: int | None = Field(
        default=None,
        description="Admin chat ID for error notifications",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    bot_image_mode: str = Field(
        default="reupload",
        description="Image mode: 'url' to send URL directly, 'reupload' to download and re-upload",
    )


def get_settings() -> Settings:
    """Get bot settings instance."""
    return Settings()
