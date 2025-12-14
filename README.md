# echo-fastapi

A FastAPI application using Poetry and Python 3.12, featuring a Reviews API and a Telegram bot.

## Requirements

- Python 3.12+
- Poetry

## Installation

```bash
poetry install
```

## Running the API

```bash
poetry run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## Running the Telegram Bot

1. Copy the example environment file and configure it:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your Telegram bot token (get one from [@BotFather](https://t.me/BotFather)):
   ```
   BOT_TOKEN=your_telegram_bot_token_here
   API_BASE_URL=http://localhost:8000
   ```

3. Start the API server (in one terminal):
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

4. Start the bot (in another terminal):
   ```bash
   poetry run python -m bot.main
   ```

### Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and quick start |
| `/help` | Show all available commands |
| `/review_new` | Create a new review (guided flow) |
| `/reviews` | List recent reviews |
| `/reviews movie` | List only movie reviews |
| `/reviews min_rating=8` | List reviews with rating ≥ 8 |
| `/review <id>` | View a specific review |
| `/review_edit <id>` | Edit a review |
| `/review_delete <id>` | Delete a review |

**Image Upload:** Reply to a review message with a photo to attach an image.

## Running Tests

```bash
poetry run pytest
```

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`