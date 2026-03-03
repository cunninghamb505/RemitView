"""CSV export endpoint."""
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
import io
from app.services import export_service

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/claims")
async def export_claims(file_id: int | None = Query(None)):
    """Export claims as CSV download."""
    csv_content = export_service.export_claims_csv(file_id=file_id)

    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=claims_export.csv"},
    )
