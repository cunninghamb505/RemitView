"""Developer view — inspect and edit raw inbound file content."""
from fastapi import APIRouter, HTTPException
from app.services import file_service
from app.config import settings

router = APIRouter(prefix="/api/developer", tags=["developer"])


@router.get("/files")
async def list_files():
    """List all files with metadata (no raw content for performance)."""
    files = file_service.list_files()
    return {"files": files}


@router.get("/files/{file_id}/raw")
async def get_raw_content(file_id: int):
    """Get the raw EDI content for a specific file."""
    result = file_service.get_raw_content(file_id)
    if not result:
        raise HTTPException(status_code=404, detail="File not found")
    return result


@router.put("/files/{file_id}/raw")
async def update_raw_content(file_id: int, body: dict):
    """Update the raw content of a file and re-parse it.

    Body: { "raw_content": "ISA*00*..." }
    """
    if settings.DEMO_MODE:
        raise HTTPException(status_code=403, detail="Editing disabled in demo mode")
    raw = body.get("raw_content", "")
    if not raw:
        raise HTTPException(status_code=400, detail="raw_content is required")

    if "ISA" not in raw[:100]:
        raise HTTPException(status_code=400, detail="Content does not appear to be valid EDI (no ISA header)")

    try:
        file_id = file_service.update_raw_content(file_id, raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Re-parse error: {str(e)}")

    return {"status": "ok", "message": "File updated and re-parsed", "file_id": file_id}
