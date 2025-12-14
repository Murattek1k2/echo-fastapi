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

## Docker Deployment

The application can be deployed using Docker with PostgreSQL as the database.

### Prerequisites

- Docker and Docker Compose installed

### Quick Start

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your Telegram bot token:
   ```
   BOT_TOKEN=your_telegram_bot_token_here
   ```

3. Build and run all services:
   ```bash
   docker compose up --build
   ```

This starts three services:
- **db**: PostgreSQL database (port 5432)
- **api**: FastAPI Reviews API (port 8000)
- **bot**: Telegram bot

The API will be available at `http://localhost:8000/docs`.

### Services Overview

| Service | Description | Port |
|---------|-------------|------|
| db | PostgreSQL 16 database | 5432 |
| api | FastAPI Reviews API | 8000 |
| bot | Telegram Bot | - |

### Data Persistence

- **Database**: PostgreSQL data is stored in `./.data/postgres/`
- **Uploads**: Review images are stored in `./uploads/`

### Environment Variables

Key environment variables for Docker:

| Variable | Service | Description |
|----------|---------|-------------|
| `DATABASE_URL` | api | PostgreSQL connection string |
| `API_ENV` | api | Environment (development/production) |
| `BOT_TOKEN` | bot | Telegram Bot API token |
| `API_BASE_URL` | bot | API URL (http://api:8000 in Docker) |

### Running in Detached Mode

```bash
docker compose up -d --build
```

### Viewing Logs

```bash
docker compose logs -f
```

### Stopping Services

```bash
docker compose down
```

### Rebuilding After Changes

```bash
docker compose up --build
```

### Production Notes

- Change the default PostgreSQL password in `docker-compose.yml`
- Set proper `SECRET_KEY` for production
- Consider using environment variables or secrets management for sensitive data

## GitLab CI/CD Pipeline

The repository includes a GitLab CI/CD pipeline (`.gitlab-ci.yml`) that automates testing, building, and deployment.

### Pipeline Stages

1. **test**: Runs pytest with uv caching
2. **build**: Builds and pushes Docker images for api and bot to Docker Hub
3. **deploy**: Deploys to production server via SSH

### GitLab CI Variables (Required)

Configure these variables in **GitLab → Settings → CI/CD → Variables** (masked and protected):

| Variable | Description | Example |
|----------|-------------|---------|
| `DOCKERHUB_USERNAME` | Docker Hub username | `myusername` |
| `DOCKERHUB_TOKEN` | Docker Hub access token (not password) | `dckr_pat_...` |
| `SSH_PRIVATE_KEY` | SSH private key for deployment user | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `DEPLOY_HOST` | Server IP or hostname | `192.168.1.100` or `myserver.com` |
| `DEPLOY_USER` | SSH username on the server | `deploy` |
| `DEPLOY_PATH` | Path to compose file on server | `/opt/echo-reviews` |

#### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEPLOY_PORT` | SSH port | `22` |
| `COMPOSE_FILE` | Compose file name | `docker-compose.prod.yml` |

### One-Time Server Setup

Run these commands on your deployment server:

```bash
# 1. Create deployment directory
sudo mkdir -p /opt/echo-reviews
sudo chown $USER:$USER /opt/echo-reviews

# 2. Copy production compose file (do this once, or update via git/scp)
cd /opt/echo-reviews
# Copy docker-compose.prod.yml to this directory

# 3. Create environment file with secrets
cat > .env << 'EOF'
# Required
DOCKERHUB_USERNAME=your-dockerhub-username
BOT_TOKEN=your-telegram-bot-token
POSTGRES_PASSWORD=your-secure-postgres-password

# Optional
POSTGRES_DB=reviews
POSTGRES_USER=postgres
LOG_LEVEL=INFO
BOT_IMAGE_MODE=reupload
EOF

# 4. Create data directories
mkdir -p .data/postgres uploads

# 5. Ensure Docker is installed
docker --version
docker compose version

# 6. (Optional) Pre-pull images to speed up first deployment
docker compose -f docker-compose.prod.yml pull
```

### Production Compose File

The `docker-compose.prod.yml` file uses Docker Hub images instead of building locally:

```yaml
api:
  image: ${DOCKERHUB_USERNAME}/echo-reviews-api:latest
  
bot:
  image: ${DOCKERHUB_USERNAME}/echo-reviews-bot:latest
```

### Deploy Script

A deployment script is available at `scripts/deploy.sh` for manual or automated deployments:

```bash
# On the server
cd /opt/echo-reviews
./scripts/deploy.sh
```

### Docker Hub Image Tags

Each build pushes two tags:
- `latest` - Always points to the most recent build
- `<commit-sha>` - Short commit SHA for rollback capability