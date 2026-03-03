"""File comparison endpoint."""
from fastapi import APIRouter, Query, HTTPException
from app.database import get_db
from app.parser.codes import lookup_status

router = APIRouter(prefix="/api/compare", tags=["compare"])


@router.get("")
async def compare_files(
    file1: int = Query(..., description="First file ID"),
    file2: int = Query(..., description="Second file ID"),
):
    """Compare claims between two files. Returns added, removed, and changed claims."""
    db = get_db()
    try:
        # Verify files exist
        for fid in (file1, file2):
            f = db.execute("SELECT id, filename FROM edi_files WHERE id = ?", (fid,)).fetchone()
            if not f:
                raise HTTPException(status_code=404, detail=f"File {fid} not found")

        file1_info = dict(db.execute("SELECT id, filename FROM edi_files WHERE id = ?", (file1,)).fetchone())
        file2_info = dict(db.execute("SELECT id, filename FROM edi_files WHERE id = ?", (file2,)).fetchone())

        # Get claims from both files
        claims1 = db.execute("""
            SELECT * FROM claims WHERE file_id = ? ORDER BY clp_claim_id
        """, (file1,)).fetchall()
        claims2 = db.execute("""
            SELECT * FROM claims WHERE file_id = ? ORDER BY clp_claim_id
        """, (file2,)).fetchall()

        map1 = {dict(c)["clp_claim_id"]: dict(c) for c in claims1}
        map2 = {dict(c)["clp_claim_id"]: dict(c) for c in claims2}

        ids1 = set(map1.keys())
        ids2 = set(map2.keys())

        removed = []
        for cid in sorted(ids1 - ids2):
            c = map1[cid]
            c["status_description"] = lookup_status(c.get("clp_status_code", ""))
            removed.append(c)

        added = []
        for cid in sorted(ids2 - ids1):
            c = map2[cid]
            c["status_description"] = lookup_status(c.get("clp_status_code", ""))
            added.append(c)

        changed = []
        for cid in sorted(ids1 & ids2):
            c1 = map1[cid]
            c2 = map2[cid]
            diffs = []
            for field in ("clp_status_code", "clp_total_charge", "clp_total_payment",
                          "patient_name", "rendering_provider_name", "total_adjustments"):
                v1 = c1.get(field)
                v2 = c2.get(field)
                if v1 != v2:
                    diffs.append({"field": field, "old": v1, "new": v2})
            if diffs:
                c2["status_description"] = lookup_status(c2.get("clp_status_code", ""))
                changed.append({"claim_id": cid, "diffs": diffs, "file1_claim": c1, "file2_claim": c2})

        return {
            "file1": file1_info,
            "file2": file2_info,
            "removed": removed,
            "added": added,
            "changed": changed,
            "summary": {
                "file1_count": len(claims1),
                "file2_count": len(claims2),
                "removed_count": len(removed),
                "added_count": len(added),
                "changed_count": len(changed),
                "unchanged_count": len(ids1 & ids2) - len(changed),
            },
        }
    finally:
        db.close()
