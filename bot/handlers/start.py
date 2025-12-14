"""Start and help command handlers."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.utils.formatting import HELP_TEXT, WELCOME_TEXT

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    await message.answer(WELCOME_TEXT, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    await message.answer(HELP_TEXT, parse_mode="HTML")
