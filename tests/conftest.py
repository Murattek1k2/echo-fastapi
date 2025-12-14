"""Test fixtures and configuration."""

import os
import shutil
import tempfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app

# Use in-memory SQLite database for testing with StaticPool to share connection
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def temp_uploads_dir() -> Generator[str, None, None]:
    """Create a temporary uploads directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def client(db_session: Session, temp_uploads_dir: str) -> Generator[TestClient, None, None]:
    """Create a test client with a fresh database and temporary uploads directory."""
    # Import the router module to patch UPLOADS_DIR
    from app.api.routers import reviews
    
    # Store original value
    original_uploads_dir = reviews.UPLOADS_DIR
    
    # Override UPLOADS_DIR for the router
    reviews.UPLOADS_DIR = temp_uploads_dir
    
    def override_get_db() -> Generator[Session, None, None]:
        """Override get_db for testing using the test session."""
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    
    # Restore original value
    reviews.UPLOADS_DIR = original_uploads_dir
