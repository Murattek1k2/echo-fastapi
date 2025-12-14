#!/bin/bash
# Deploy script for Echo Reviews application
# This script is designed to be run on the deployment server
# It pulls the latest Docker images and restarts the services

set -euo pipefail

# Configuration (can be overridden by environment variables)
DEPLOY_PATH="${DEPLOY_PATH:-/opt/echo-reviews}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
DOCKERHUB_USERNAME="${DOCKERHUB_USERNAME:-}"
DOCKERHUB_TOKEN="${DOCKERHUB_TOKEN:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Change to deployment directory
log_info "Changing to deployment directory: ${DEPLOY_PATH}"
cd "${DEPLOY_PATH}"

# Login to Docker Hub if credentials are provided
if [[ -n "${DOCKERHUB_USERNAME}" ]] && [[ -n "${DOCKERHUB_TOKEN}" ]]; then
    log_info "Logging in to Docker Hub..."
    echo "${DOCKERHUB_TOKEN}" | docker login -u "${DOCKERHUB_USERNAME}" --password-stdin
else
    log_warn "Docker Hub credentials not provided, skipping login"
fi

# Pull latest images
log_info "Pulling latest Docker images..."
docker compose -f "${COMPOSE_FILE}" pull

# Restart services
log_info "Restarting services with docker compose..."
docker compose -f "${COMPOSE_FILE}" up -d

# Prune unused images (optional, keeps disk usage low)
log_info "Pruning unused Docker images..."
if ! docker image prune -f; then
    log_warn "Image pruning failed (non-critical), continuing..."
fi

# Show running containers
log_info "Deployment complete! Running containers:"
docker compose -f "${COMPOSE_FILE}" ps

log_info "Deployment finished successfully!"
