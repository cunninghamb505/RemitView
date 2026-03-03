"""CARC/RARC code lookup endpoints."""
from fastapi import APIRouter, Query
from app.parser.codes import CARC_CODES, RARC_CODES

router = APIRouter(prefix="/api/codes", tags=["codes"])


@router.get("/carc")
async def search_carc(search: str = Query("")):
    """Search CARC codes."""
    return _search_codes(CARC_CODES, search)


@router.get("/rarc")
async def search_rarc(search: str = Query("")):
    """Search RARC codes."""
    return _search_codes(RARC_CODES, search)


def _search_codes(code_dict: dict, search: str) -> dict:
    """Search a code dictionary by code or description."""
    search_lower = search.lower().strip()
    results = []
    for code, desc in code_dict.items():
        if not search_lower or search_lower in code.lower() or search_lower in desc.lower():
            results.append({"code": code, "description": desc})

    return {"codes": results, "total": len(results)}
