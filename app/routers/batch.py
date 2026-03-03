"""Batch claim action endpoints."""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services import batch_service

router = APIRouter(prefix="/api/batch", tags=["batch"])


class BatchFlag(BaseModel):
    claim_ids: list[int]
    flag_type: str = "review"
    note: str = ""


class BatchIds(BaseModel):
    claim_ids: list[int]


@router.post("/flag")
async def batch_flag(data: BatchFlag):
    """Flag multiple claims at once."""
    count = batch_service.batch_flag(data.claim_ids, data.flag_type, data.note)
    return {"message": f"Flagged {count} claims", "count": count}


@router.post("/export-csv")
async def batch_export_csv(data: BatchIds):
    """Export selected claims as CSV."""
    csv_content = batch_service.batch_export_csv(data.claim_ids)
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=claims_export.csv"},
    )


@router.post("/resolve-flags")
async def batch_resolve_flags(data: BatchIds):
    """Resolve all open flags on selected claims."""
    count = batch_service.batch_resolve_flags(data.claim_ids)
    return {"message": f"Resolved {count} flags", "count": count}
