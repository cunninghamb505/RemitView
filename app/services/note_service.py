"""Claim notes CRUD service."""
from app.database import get_db


def create_note(claim_id: int, content: str) -> dict:
    """Add a note to a claim."""
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO claim_notes (claim_id, content) VALUES (?, ?)",
            (claim_id, content),
        )
        db.commit()
        row = db.execute("SELECT * FROM claim_notes WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row)
    finally:
        db.close()


def list_notes(claim_id: int) -> list[dict]:
    """List notes for a claim in reverse chronological order."""
    db = get_db()
    try:
        rows = db.execute(
            "SELECT * FROM claim_notes WHERE claim_id = ? ORDER BY created_at DESC",
            (claim_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


def delete_note(note_id: int) -> bool:
    """Delete a note by ID."""
    db = get_db()
    try:
        cursor = db.execute("DELETE FROM claim_notes WHERE id = ?", (note_id,))
        db.commit()
        return cursor.rowcount > 0
    finally:
        db.close()
