"""Claims list and detail endpoints."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.services import claim_service

router = APIRouter(prefix="/api/claims", tags=["claims"])


class WorkflowUpdate(BaseModel):
    status: str
    note: str = ""


@router.get("")
async def list_claims(
    file_id: int | None = Query(None),
    status: str | None = Query(None),
    workflow_status: str | None = Query(None),
    search: str | None = Query(None),
    sort_by: str = Query("id"),
    sort_dir: str = Query("asc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
):
    """List claims with filtering, sorting, and pagination."""
    return claim_service.list_claims(
        file_id=file_id,
        status=status,
        workflow_status=workflow_status,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )


@router.get("/{claim_id}")
async def get_claim(claim_id: int):
    """Get full claim detail."""
    detail = claim_service.get_claim_detail(claim_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Claim not found")
    return detail


@router.patch("/{claim_id}/workflow")
async def update_workflow(claim_id: int, data: WorkflowUpdate):
    """Update workflow status for a claim."""
    result = claim_service.update_workflow_status(claim_id, data.status, data.note)
    if not result:
        raise HTTPException(status_code=404, detail="Claim not found")
    return result


@router.get("/{claim_id}/workflow-history")
async def get_workflow_history(claim_id: int):
    """Get workflow status change history for a claim."""
    history = claim_service.get_workflow_history(claim_id)
    return {"history": history}
