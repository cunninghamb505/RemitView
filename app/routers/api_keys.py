"""API key management endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import get_db
from app.auth import generate_api_key, hash_key

router = APIRouter(prefix="/api/keys", tags=["api-keys"])


class KeyCreate(BaseModel):
    key_name: str
    permissions: str = "read"


@router.post("")
async def create_key(data: KeyCreate):
    """Create a new API key. Returns the key once — store it securely."""
    raw_key = generate_api_key()
    key_hash = hash_key(raw_key)

    db = get_db()
    try:
        cursor = db.execute("""
            INSERT INTO api_keys (key_name, key_hash, permissions)
            VALUES (?, ?, ?)
        """, (data.key_name, key_hash, data.permissions))
        db.commit()
        return {
            "message": "API key created. Save this key — it will not be shown again.",
            "id": cursor.lastrowid,
            "key": raw_key,
            "key_name": data.key_name,
        }
    finally:
        db.close()


@router.get("")
async def list_keys():
    """List all API keys (without revealing the actual keys)."""
    db = get_db()
    try:
        rows = db.execute("""
            SELECT id, key_name, permissions, created_at, last_used_at, is_active
            FROM api_keys ORDER BY created_at DESC
        """).fetchall()
        return {"keys": [dict(r) for r in rows]}
    finally:
        db.close()


@router.delete("/{key_id}")
async def delete_key(key_id: int):
    """Deactivate an API key."""
    db = get_db()
    try:
        cursor = db.execute(
            "UPDATE api_keys SET is_active = 0 WHERE id = ?", (key_id,)
        )
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Key not found")
        return {"message": "API key deactivated"}
    finally:
        db.close()
