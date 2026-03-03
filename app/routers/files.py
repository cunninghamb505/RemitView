"""File upload, sample loading, listing, and deletion endpoints."""
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services import file_service
from app.services.claim_matching_service import import_837_and_match
from app.parser.sample_835 import SAMPLES
from app.parser.pdf_parser import parse_pdf_remittance
from app.config import settings

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and parse an 835 file (EDI or PDF)."""
    if settings.DEMO_MODE:
        raise HTTPException(status_code=403, detail="Uploads disabled in demo mode")
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    filename = file.filename.lower()

    # PDF remittance
    if filename.endswith(".pdf"):
        try:
            parsed = parse_pdf_remittance(content)
            file_id = file_service.parse_and_store_parsed(
                parsed, file.filename,
                source_type="pdf",
                pdf_notes=parsed.get("pdf_parsing_notes", ""),
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF parse error: {str(e)}")
        return {"message": "PDF remittance parsed and stored", "id": file_id}

    # EDI 835 file
    raw = content.decode("utf-8", errors="replace")
    if "ISA" not in raw[:100]:
        raise HTTPException(status_code=400, detail="Not a valid EDI X12 file (no ISA header)")

    try:
        file_id = file_service.parse_and_store(raw, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parse error: {str(e)}")

    return {"message": "File uploaded and parsed successfully", "id": file_id}


@router.post("/upload-837")
async def upload_837(file: UploadFile = File(...)):
    """Upload an 837 claim file and match against existing 835 data."""
    if settings.DEMO_MODE:
        raise HTTPException(status_code=403, detail="Uploads disabled in demo mode")
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    raw = content.decode("utf-8", errors="replace")
    if "ISA" not in raw[:100]:
        raise HTTPException(status_code=400, detail="Not a valid EDI X12 file")

    try:
        result = import_837_and_match(raw, file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"837 parse error: {str(e)}")

    return result


@router.post("/load-sample")
async def load_sample():
    """Load built-in sample 835 files (3 different payers)."""
    file_ids = []
    try:
        for filename, content in SAMPLES:
            file_id = file_service.parse_and_store(content, filename)
            file_ids.append(file_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading samples: {str(e)}")

    return {"message": f"{len(file_ids)} sample files loaded successfully", "ids": file_ids}


@router.get("")
async def list_files():
    """List all loaded files."""
    files = file_service.list_files()
    return {"files": files}


@router.delete("/{file_id}")
async def delete_file(file_id: int):
    """Delete a file and all its data."""
    if settings.DEMO_MODE:
        raise HTTPException(status_code=403, detail="Deleting files disabled in demo mode")
    deleted = file_service.delete_file(file_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="File not found")
    return {"message": "File deleted successfully"}
