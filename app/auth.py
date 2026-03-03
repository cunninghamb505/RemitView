"""API key authentication middleware."""
import hashlib
import secrets
from fastapi import Request, HTTPException
from app.database import get_db


def generate_api_key() -> str:
    """Generate a random API key."""
    return f"rv_{secrets.token_hex(24)}"


def hash_key(key: str) -> str:
    """Hash an API key with SHA256."""
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(request: Request) -> dict | None:
    """Verify an API key from the Authorization header.

    Returns the key record if valid, None if no header present.
    Raises HTTPException if the key is invalid.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = auth_header[7:]
    key_hash = hash_key(token)

    db = get_db()
    try:
        row = db.execute(
            "SELECT * FROM api_keys WHERE key_hash = ? AND is_active = 1", (key_hash,)
        ).fetchone()

        if not row:
            raise HTTPException(status_code=401, detail="Invalid or inactive API key")

        # Update last used timestamp
        db.execute(
            "UPDATE api_keys SET last_used_at = CURRENT_TIMESTAMP WHERE id = ?", (row["id"],)
        )
        db.commit()

        return dict(row)
    finally:
        db.close()
