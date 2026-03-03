"""Saved filters endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services import saved_filter_service

router = APIRouter(prefix="/api/saved-filters", tags=["saved-filters"])


class FilterCreate(BaseModel):
    name: str
    filters: str  # JSON string


@router.post("")
async def create_filter(data: FilterCreate):
    """Save a named filter."""
    f = saved_filter_service.create_filter(data.name, data.filters)
    return {"message": "Filter saved", "filter": f}


@router.get("")
async def list_filters():
    """List all saved filters."""
    filters = saved_filter_service.list_filters()
    return {"filters": filters}


@router.delete("/{filter_id}")
async def delete_filter(filter_id: int):
    """Delete a saved filter."""
    deleted = saved_filter_service.delete_filter(filter_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Saved filter not found")
    return {"message": "Filter deleted"}
