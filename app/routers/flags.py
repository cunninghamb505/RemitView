"""Claim flag endpoints."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.services import flag_service


router = APIRouter(prefix="/api/flags", tags=["flags"])


class FlagCreate(BaseModel):
    claim_id: int
    flag_type: str = "review"
    note: str = ""


class FlagUpdate(BaseModel):
    note: str | None = None
    flag_type: str | None = None


@router.post("")
async def create_flag(data: FlagCreate):
    """Create a new flag on a claim."""
    flag = flag_service.create_flag(data.claim_id, data.flag_type, data.note)
    return {"message": "Flag created", "flag": flag}


@router.get("")
async def list_flags(
    claim_id: int | None = Query(None),
    resolved: bool | None = Query(None),
):
    """List flags."""
    flags = flag_service.list_flags(claim_id=claim_id, resolved=resolved)
    return {"flags": flags}


@router.patch("/{flag_id}")
async def update_flag(flag_id: int, data: FlagUpdate):
    """Update a flag."""
    flag = flag_service.update_flag(flag_id, note=data.note, flag_type=data.flag_type)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    return {"flag": flag}


@router.patch("/{flag_id}/resolve")
async def resolve_flag(flag_id: int):
    """Mark a flag as resolved."""
    flag = flag_service.resolve_flag(flag_id)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    return {"flag": flag}


@router.delete("/{flag_id}")
async def delete_flag(flag_id: int):
    """Delete a flag."""
    deleted = flag_service.delete_flag(flag_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Flag not found")
    return {"message": "Flag deleted"}
