"""
database.py

Responsible for:
- SQLite connection management
- Database / table creation
- Low-level row access (no business logic lives here)
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

# app.db sits at the project root, one level above backend/
DB_PATH = Path(__file__).resolve().parent.parent / "app.db"


@contextmanager
def get_connection():
    """Yields a SQLite connection with row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Creates all required tables if they do not already exist."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                filename          TEXT NOT NULL,
                original_filename TEXT,
                image_path        TEXT NOT NULL,
                timestamp         TEXT NOT NULL DEFAULT (datetime('now')),
                brightness        REAL,
                blur              REAL,
                output            TEXT,
                processed         INTEGER NOT NULL DEFAULT 0,
                camera_id         TEXT,
                location          TEXT
            )
            """
        )


def row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}
