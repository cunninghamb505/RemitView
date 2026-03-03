"""Dashboard aggregate statistics endpoint."""
from fastapi import APIRouter, Query
from app.services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(file_id: int | None = Query(None)):
    """Get aggregate dashboard statistics."""
    return dashboard_service.get_dashboard_stats(file_id=file_id)
