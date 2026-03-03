"""Database maintenance service — backup, restore, wipe, reset."""
import os
import sqlite3
import tempfile
from pathlib import Path
from app.config import settings
from app.database import init_db, get_db


def create_backup() -> str:
    """Safely copy the database to a temp file using the SQLite backup API. Returns temp path."""
    src = sqlite3.connect(settings.DB_PATH)
    fd, tmp_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    dst = sqlite3.connect(tmp_path)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    return tmp_path


def restore_backup(uploaded_path: str):
    """Validate and replace the current database with an uploaded backup."""
    # Validate it's a real SQLite database
    try:
        test_conn = sqlite3.connect(uploaded_path)
        test_conn.execute("SELECT count(*) FROM sqlite_master")
        test_conn.close()
    except sqlite3.DatabaseError:
        raise ValueError("Uploaded file is not a valid SQLite database")

    # Checkpoint WAL on current DB if it exists
    if os.path.exists(settings.DB_PATH):
        try:
            conn = sqlite3.connect(settings.DB_PATH)
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()
        except Exception:
            pass

    # Replace the database file
    import shutil
    shutil.copy2(uploaded_path, settings.DB_PATH)

    # Remove WAL/SHM files if present
    for suffix in ("-wal", "-shm"):
        wal_path = settings.DB_PATH + suffix
        if os.path.exists(wal_path):
            os.remove(wal_path)

    # Reinitialize
    init_db()


def get_db_info() -> dict:
    """Return database stats: file size and row counts per table."""
    db_path = Path(settings.DB_PATH)
    file_size = db_path.stat().st_size if db_path.exists() else 0

    db = get_db()
    try:
        tables = {}
        rows = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        for r in rows:
            name = r["name"]
            count = db.execute(f"SELECT COUNT(*) as cnt FROM [{name}]").fetchone()["cnt"]
            tables[name] = count
        return {"file_size": file_size, "tables": tables}
    finally:
        db.close()


def wipe_data():
    """Delete all file/claim data. Preserves app_settings and api_keys."""
    db = get_db()
    try:
        # These cascade to claims, adjustments, service lines, flags, etc.
        db.execute("DELETE FROM edi_files")
        db.execute("DELETE FROM saved_filters")
        db.execute("DELETE FROM workflow_history")
        db.execute("DELETE FROM claim_notes")
        db.commit()
    finally:
        db.close()


def factory_reset():
    """Drop all tables and reinitialize the database."""
    db = sqlite3.connect(settings.DB_PATH)
    try:
        tables = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        for (name,) in tables:
            db.execute(f"DROP TABLE IF EXISTS [{name}]")
        db.commit()
    finally:
        db.close()
    init_db()
