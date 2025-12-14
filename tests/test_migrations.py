"""Tests for database migrations."""

from sqlalchemy import inspect

from app.db.migrations import run_migrations
from app.db.session import Base
from tests.conftest import engine


def test_run_migrations_on_sqlite() -> None:
    """Test that migrations run without error on SQLite (no-op for SQLite)."""
    # Create tables first
    Base.metadata.create_all(bind=engine)
    
    try:
        # SQLite doesn't need the migration, but it should run without error
        run_migrations(engine)
        
        # Verify the table structure is correct
        inspector = inspect(engine)
        columns = inspector.get_columns("reviews")
        
        # Find author_telegram_id column
        telegram_id_col = None
        for col in columns:
            if col["name"] == "author_telegram_id":
                telegram_id_col = col
                break
        
        # Column should exist (either from create_all or already present)
        # The test just verifies that migrations don't break anything
        assert telegram_id_col is not None
    finally:
        # Clean up
        Base.metadata.drop_all(bind=engine)
