"""Claim notes endpoints."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.services import note_service

router = APIRouter(prefix="/api/notes", tags=["notes"])


class NoteCreate(BaseModel):
    claim_id: int
    content: str


@router.post("")
async def create_note(data: NoteCreate):
    """Add a note to a claim."""
    note = note_service.create_note(data.claim_id, data.content)
    return {"message": "Note created", "note": note}


@router.get("")
async def list_notes(claim_id: int = Query(...)):
    """List notes for a claim."""
    notes = note_service.list_notes(claim_id)
    return {"notes": notes}


@router.delete("/{note_id}")
async def delete_note(note_id: int):
    """Delete a note."""
    deleted = note_service.delete_note(note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted"}
