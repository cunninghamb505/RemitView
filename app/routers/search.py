"""Global search endpoint."""
from fastapi import APIRouter, Query
from app.services import search_service

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
async def search(q: str = Query(..., min_length=2), limit: int = Query(50, le=200)):
    """Search across claims, patients, and procedure codes."""
    return search_service.global_search(q, limit=limit)
