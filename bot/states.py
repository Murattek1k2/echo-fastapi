"""FSM states for bot conversation flows."""

from aiogram.fsm.state import State, StatesGroup


class ReviewCreateStates(StatesGroup):
    """States for creating a new review."""

    media_type = State()
    media_title = State()
    media_year = State()
    rating = State()
    contains_spoilers = State()
    text = State()


class ReviewEditStates(StatesGroup):
    """States for editing a review."""

    select_field = State()
    edit_media_type = State()
    edit_media_title = State()
    edit_media_year = State()
    edit_rating = State()
    edit_contains_spoilers = State()
    edit_text = State()


class ReviewDeleteStates(StatesGroup):
    """States for deleting a review."""

    confirm = State()
