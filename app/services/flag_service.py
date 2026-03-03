"""Claim flagging and notes service."""
from app.database import get_db


def create_flag(claim_id: int, flag_type: str = "review", note: str = "") -> dict:
    """Create a flag on a claim."""
    db = get_db()
    try:
        cursor = db.execute("""
            INSERT INTO claim_flags (claim_id, flag_type, note)
            VALUES (?, ?, ?)
        """, (claim_id, flag_type, note))
        db.commit()
        flag = db.execute("SELECT * FROM claim_flags WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(flag)
    finally:
        db.close()


def list_flags(claim_id: int | None = None, resolved: bool | None = None) -> list[dict]:
    """List flags, optionally filtered by claim or resolved status."""
    db = get_db()
    try:
        conditions = []
        params = []

        if claim_id is not None:
            conditions.append("cf.claim_id = ?")
            params.append(claim_id)
        if resolved is True:
            conditions.append("cf.resolved_at IS NOT NULL")
        elif resolved is False:
            conditions.append("cf.resolved_at IS NULL")

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        rows = db.execute(f"""
            SELECT cf.*, c.clp_claim_id, c.patient_name
            FROM claim_flags cf
            JOIN claims c ON c.id = cf.claim_id
            {where}
            ORDER BY cf.created_at DESC
        """, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


def update_flag(flag_id: int, note: str | None = None, flag_type: str | None = None) -> dict | None:
    """Update a flag's note or type."""
    db = get_db()
    try:
        updates = []
        params = []
        if note is not None:
            updates.append("note = ?")
            params.append(note)
        if flag_type is not None:
            updates.append("flag_type = ?")
            params.append(flag_type)
        if not updates:
            flag = db.execute("SELECT * FROM claim_flags WHERE id = ?", (flag_id,)).fetchone()
            return dict(flag) if flag else None

        params.append(flag_id)
        db.execute(f"UPDATE claim_flags SET {', '.join(updates)} WHERE id = ?", params)
        db.commit()
        flag = db.execute("SELECT * FROM claim_flags WHERE id = ?", (flag_id,)).fetchone()
        return dict(flag) if flag else None
    finally:
        db.close()


def resolve_flag(flag_id: int) -> dict | None:
    """Mark a flag as resolved."""
    db = get_db()
    try:
        db.execute(
            "UPDATE claim_flags SET resolved_at = CURRENT_TIMESTAMP WHERE id = ?",
            (flag_id,)
        )
        db.commit()
        flag = db.execute("SELECT * FROM claim_flags WHERE id = ?", (flag_id,)).fetchone()
        return dict(flag) if flag else None
    finally:
        db.close()


def delete_flag(flag_id: int) -> bool:
    """Delete a flag."""
    db = get_db()
    try:
        cursor = db.execute("DELETE FROM claim_flags WHERE id = ?", (flag_id,))
        db.commit()
        return cursor.rowcount > 0
    finally:
        db.close()
