"""Database maintenance endpoints — backup, restore, wipe, reset."""
import os
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime
from app.config import settings
from app.services import maintenance_service

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


class ConfirmAction(BaseModel):
    confirm: str


@router.get("/backup")
async def download_backup():
    """Download a safe copy of the database."""
    tmp_path = maintenance_service.create_backup()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return FileResponse(
        tmp_path,
        media_type="application/octet-stream",
        filename=f"remitview_backup_{timestamp}.db",
        background=None,
    )


@router.post("/restore")
async def restore_backup(file: UploadFile = File(...)):
    """Restore database from an uploaded .db file."""
    if settings.DEMO_MODE:
        raise HTTPException(status_code=403, detail="Restore is disabled in demo mode")

    # Save uploaded file to temp location
    import tempfile
    fd, tmp_path = tempfile.mkstemp(suffix=".db")
    try:
        content = await file.read()
        os.write(fd, content)
        os.close(fd)
        maintenance_service.restore_backup(tmp_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return {"message": "Database restored successfully"}


@router.get("/db-info")
async def db_info():
    """Return database stats (file size, table row counts)."""
    return maintenance_service.get_db_info()


@router.post("/wipe")
async def wipe_data(data: ConfirmAction):
    """Delete all file data. Requires confirm='WIPE'."""
    if settings.DEMO_MODE:
        raise HTTPException(status_code=403, detail="Wipe is disabled in demo mode")
    if data.confirm != "WIPE":
        raise HTTPException(status_code=400, detail="Must confirm with 'WIPE'")
    maintenance_service.wipe_data()
    return {"message": "All data has been wiped"}


@router.post("/reset")
async def factory_reset(data: ConfirmAction):
    """Full factory reset. Requires confirm='RESET'."""
    if settings.DEMO_MODE:
        raise HTTPException(status_code=403, detail="Reset is disabled in demo mode")
    if data.confirm != "RESET":
        raise HTTPException(status_code=400, detail="Must confirm with 'RESET'")
    maintenance_service.factory_reset()
    return {"message": "Factory reset complete"}
