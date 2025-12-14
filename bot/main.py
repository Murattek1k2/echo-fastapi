"""Main entry point for the Telegram bot."""

import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import get_settings
from bot.handlers import images, reviews, start
from bot.logging_config import get_logger, setup_logging


async def main() -> None:
    """Run the bot."""
    # Load settings
    settings = get_settings()
    
    # Setup logging
    setup_logging(settings.log_level)
    logger = get_logger(__name__)
    
    logger.info("Starting Reviews Bot...")
    logger.info("API Base URL: %s", settings.api_base_url)
    
    # Initialize bot and dispatcher
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    
    # Register routers
    dp.include_router(start.router)
    dp.include_router(reviews.router)
    dp.include_router(images.router)
    
    # Start polling
    logger.info("Bot is running. Press Ctrl+C to stop.")
    try:
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        logger.info("Bot stopped.")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
        sys.exit(0)
