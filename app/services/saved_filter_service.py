"""Saved filters CRUD service."""
from app.database import get_db


def create_filter(name: str, filters: str) -> dict:
    """Save a named filter (filters is a JSON string)."""
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO saved_filters (name, filters) VALUES (?, ?)",
            (name, filters),
        )
        db.commit()
        row = db.execute("SELECT * FROM saved_filters WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row)
    finally:
        db.close()


def list_filters() -> list[dict]:
    """List all saved filters ordered by creation date."""
    db = get_db()
    try:
        rows = db.execute(
            "SELECT * FROM saved_filters ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


def delete_filter(filter_id: int) -> bool:
    """Delete a saved filter by ID."""
    db = get_db()
    try:
        cursor = db.execute("DELETE FROM saved_filters WHERE id = ?", (filter_id,))
        db.commit()
        return cursor.rowcount > 0
    finally:
        db.close()
