"""Application settings service."""
from app.database import get_db


def get_setting(key: str) -> str | None:
    """Get a setting value by key."""
    db = get_db()
    try:
        row = db.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None
    finally:
        db.close()


def set_setting(key: str, value: str) -> dict:
    """Set a setting value."""
    db = get_db()
    try:
        db.execute("""
            INSERT INTO app_settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
        """, (key, value))
        db.commit()
        return {"key": key, "value": value}
    finally:
        db.close()


def get_all_settings() -> dict:
    """Get all settings as a dictionary."""
    db = get_db()
    try:
        rows = db.execute("SELECT key, value FROM app_settings").fetchall()
        return {r["key"]: r["value"] for r in rows}
    finally:
        db.close()
