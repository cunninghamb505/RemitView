"""Claim query and detail service."""
from app.database import get_db
from app.parser.codes import lookup_status, lookup_group, lookup_carc


WORKFLOW_STATUSES = [
    "new", "in-review", "needs-appeal", "appeal-sent",
    "follow-up", "resolved", "written-off",
]


def list_claims(
    file_id: int | None = None,
    status: str | None = None,
    workflow_status: str | None = None,
    search: str | None = None,
    sort_by: str = "id",
    sort_dir: str = "asc",
    page: int = 1,
    page_size: int = 25,
) -> dict:
    """List claims with filtering, sorting, and pagination."""
    db = get_db()
    try:
        conditions = []
        params = []

        if file_id:
            conditions.append("c.file_id = ?")
            params.append(file_id)
        if status:
            conditions.append("c.clp_status_code = ?")
            params.append(status)
        if workflow_status:
            conditions.append("c.workflow_status = ?")
            params.append(workflow_status)
        if search:
            conditions.append(
                "(c.clp_claim_id LIKE ? OR c.patient_name LIKE ? OR c.rendering_provider_name LIKE ?)"
            )
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # Allowed sort columns
        allowed_sorts = {
            "id": "c.id",
            "claim_id": "c.clp_claim_id",
            "status": "c.clp_status_code",
            "charge": "c.clp_total_charge",
            "payment": "c.clp_total_payment",
            "patient": "c.patient_name",
            "provider": "c.rendering_provider_name",
            "date": "c.claim_date_start",
            "workflow": "c.workflow_status",
        }
        sort_col = allowed_sorts.get(sort_by, "c.id")
        direction = "DESC" if sort_dir.lower() == "desc" else "ASC"

        # Count total
        count_row = db.execute(
            f"SELECT COUNT(*) as cnt FROM claims c {where}", params
        ).fetchone()
        total = count_row["cnt"]

        # Fetch page
        offset = (page - 1) * page_size
        rows = db.execute(f"""
            SELECT c.*, f.filename,
                   (SELECT COUNT(*) FROM service_lines sl WHERE sl.claim_id = c.id) as service_line_count
            FROM claims c
            JOIN edi_files f ON f.id = c.file_id
            {where}
            ORDER BY {sort_col} {direction}
            LIMIT ? OFFSET ?
        """, params + [page_size, offset]).fetchall()

        claims = []
        for r in rows:
            d = dict(r)
            d["status_description"] = lookup_status(d.get("clp_status_code", ""))
            claims.append(d)

        total_pages = max(1, (total + page_size - 1) // page_size)

        return {
            "claims": claims,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    finally:
        db.close()


def get_claim_detail(claim_id: int) -> dict | None:
    """Get full claim detail with service lines and adjustments."""
    db = get_db()
    try:
        # Get claim
        claim = db.execute("""
            SELECT c.*, f.filename
            FROM claims c
            JOIN edi_files f ON f.id = c.file_id
            WHERE c.id = ?
        """, (claim_id,)).fetchone()

        if not claim:
            return None

        result = dict(claim)
        result["status_description"] = lookup_status(result.get("clp_status_code", ""))

        # Get claim-level adjustments
        adj_rows = db.execute(
            "SELECT * FROM claim_adjustments WHERE claim_id = ?", (claim_id,)
        ).fetchall()
        result["adjustments"] = []
        for a in adj_rows:
            ad = dict(a)
            ad["group_description"] = lookup_group(ad.get("group_code", ""))
            ad["reason_description"] = lookup_carc(ad.get("reason_code", ""))
            result["adjustments"].append(ad)

        # Get service lines
        svc_rows = db.execute(
            "SELECT * FROM service_lines WHERE claim_id = ? ORDER BY id", (claim_id,)
        ).fetchall()
        result["service_lines"] = []
        for s in svc_rows:
            sd = dict(s)
            # Get service-level adjustments
            sadj_rows = db.execute(
                "SELECT * FROM service_adjustments WHERE service_line_id = ?", (sd["id"],)
            ).fetchall()
            sd["adjustments"] = []
            for sa in sadj_rows:
                sad = dict(sa)
                sad["group_description"] = lookup_group(sad.get("group_code", ""))
                sad["reason_description"] = lookup_carc(sad.get("reason_code", ""))
                sd["adjustments"].append(sad)
            result["service_lines"].append(sd)

        return result
    finally:
        db.close()


def update_workflow_status(claim_id: int, new_status: str, note: str = "") -> dict | None:
    """Update a claim's workflow status and log the change."""
    if new_status not in WORKFLOW_STATUSES:
        return None
    db = get_db()
    try:
        claim = db.execute("SELECT workflow_status FROM claims WHERE id = ?", (claim_id,)).fetchone()
        if not claim:
            return None
        old_status = claim["workflow_status"] or "new"
        db.execute("UPDATE claims SET workflow_status = ? WHERE id = ?", (new_status, claim_id))
        db.execute(
            "INSERT INTO workflow_history (claim_id, old_status, new_status, note) VALUES (?, ?, ?, ?)",
            (claim_id, old_status, new_status, note),
        )
        db.commit()
        return {"claim_id": claim_id, "old_status": old_status, "new_status": new_status}
    finally:
        db.close()


def get_workflow_history(claim_id: int) -> list[dict]:
    """Get workflow status history for a claim."""
    db = get_db()
    try:
        rows = db.execute(
            "SELECT * FROM workflow_history WHERE claim_id = ? ORDER BY changed_at DESC",
            (claim_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()
