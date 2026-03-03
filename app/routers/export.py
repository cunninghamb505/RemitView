"""Export endpoints — CSV, Excel, PDF."""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse, Response
import io
from app.services import export_service, excel_export_service, pdf_service

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


@router.get("/excel")
async def export_excel(file_id: int = Query(...)):
    """Export a file's complete data as Excel."""
    try:
        excel_bytes = excel_export_service.export_file_to_excel(file_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=remitview_export_{file_id}.xlsx"},
    )


@router.get("/pdf/claim/{claim_id}")
async def export_claim_pdf(claim_id: int):
    """Generate a PDF report for a single claim."""
    try:
        pdf_bytes = pdf_service.generate_claim_pdf(claim_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=claim_{claim_id}.pdf"},
    )


@router.get("/pdf/file/{file_id}")
async def export_file_pdf(file_id: int):
    """Generate a PDF summary report for a file."""
    try:
        pdf_bytes = pdf_service.generate_file_pdf(file_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=file_report_{file_id}.pdf"},
    )
