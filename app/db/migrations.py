"""Database migrations for schema updates that create_all() cannot handle."""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def run_migrations(engine: Engine) -> None:
    """Run database migrations.

    This handles schema changes that SQLAlchemy's create_all() cannot manage,
    such as altering column types on existing tables.
    """
    _migrate_author_telegram_id_to_bigint(engine)


def _migrate_author_telegram_id_to_bigint(engine: Engine) -> None:
    """Migrate author_telegram_id column from INTEGER to BIGINT if needed.

    Telegram user IDs can exceed the INTEGER range (max 2,147,483,647),
    so we need BIGINT to store them properly.
    """
    inspector = inspect(engine)

    # Check if the reviews table exists
    if "reviews" not in inspector.get_table_names():
        return  # Table doesn't exist yet, create_all will create it correctly

    # Get column info for the reviews table
    columns = inspector.get_columns("reviews")
    for col in columns:
        if col["name"] == "author_telegram_id":
            # Check if the column type needs to be upgraded
            col_type = str(col["type"]).upper()
            # PostgreSQL uses INTEGER, SQLite uses INTEGER
            # We need to alter to BIGINT only for PostgreSQL
            if "BIGINT" not in col_type and "postgresql" in engine.dialect.name:
                with engine.begin() as conn:
                    conn.execute(
                        text(
                            "ALTER TABLE reviews "
                            "ALTER COLUMN author_telegram_id TYPE BIGINT"
                        )
                    )
            break
