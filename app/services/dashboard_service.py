"""Dashboard aggregate statistics service."""
from app.database import get_db
from app.parser.codes import lookup_status, lookup_carc, lookup_group


def get_dashboard_stats(file_id: int | None = None) -> dict:
    """Get aggregate dashboard statistics, optionally filtered by file."""
    db = get_db()
    try:
        file_filter = ""
        params: list = []
        if file_id:
            file_filter = "WHERE c.file_id = ?"
            params = [file_id]

        # Totals
        totals = db.execute(f"""
            SELECT
                COALESCE(SUM(c.clp_total_payment), 0) as total_payments,
                COALESCE(SUM(c.clp_total_charge), 0) as total_charges,
                COUNT(c.id) as total_claims
            FROM claims c
            {file_filter}
        """, params).fetchone()

        # Total adjustments (from claim + service level)
        adj_filter = ""
        adj_params: list = []
        if file_id:
            adj_filter = "WHERE c.file_id = ?"
            adj_params = [file_id]

        adj_total = db.execute(f"""
            SELECT COALESCE(SUM(ca.amount), 0) as total
            FROM claim_adjustments ca
            JOIN claims c ON c.id = ca.claim_id
            {adj_filter}
        """, adj_params).fetchone()

        svc_adj_total = db.execute(f"""
            SELECT COALESCE(SUM(sa.amount), 0) as total
            FROM service_adjustments sa
            JOIN service_lines sl ON sl.id = sa.service_line_id
            JOIN claims c ON c.id = sl.claim_id
            {adj_filter}
        """, adj_params).fetchone()

        total_adjustments = (adj_total["total"] or 0) + (svc_adj_total["total"] or 0)

        # Claims by status
        status_rows = db.execute(f"""
            SELECT c.clp_status_code as status_code, COUNT(*) as count
            FROM claims c
            {file_filter}
            GROUP BY c.clp_status_code
            ORDER BY count DESC
        """, params).fetchall()
        claims_by_status = []
        for r in status_rows:
            claims_by_status.append({
                "status_code": r["status_code"],
                "status_description": lookup_status(r["status_code"]),
                "count": r["count"],
            })

        # Top denial reasons (CAS reason codes with highest total amounts)
        denial_rows = db.execute(f"""
            SELECT sa.group_code, sa.reason_code,
                   SUM(sa.amount) as total_amount, COUNT(*) as count
            FROM service_adjustments sa
            JOIN service_lines sl ON sl.id = sa.service_line_id
            JOIN claims c ON c.id = sl.claim_id
            {adj_filter}
            GROUP BY sa.group_code, sa.reason_code
            ORDER BY total_amount DESC
            LIMIT 10
        """, adj_params).fetchall()
        top_denial_reasons = []
        for r in denial_rows:
            top_denial_reasons.append({
                "group_code": r["group_code"],
                "group_description": lookup_group(r["group_code"]),
                "reason_code": r["reason_code"],
                "reason_description": lookup_carc(r["reason_code"]),
                "total_amount": r["total_amount"],
                "count": r["count"],
            })

        # Top adjustments (claim-level)
        claim_adj_rows = db.execute(f"""
            SELECT ca.group_code, ca.reason_code,
                   SUM(ca.amount) as total_amount, COUNT(*) as count
            FROM claim_adjustments ca
            JOIN claims c ON c.id = ca.claim_id
            {adj_filter}
            GROUP BY ca.group_code, ca.reason_code
            ORDER BY total_amount DESC
            LIMIT 10
        """, adj_params).fetchall()
        top_adjustments = []
        for r in claim_adj_rows:
            top_adjustments.append({
                "group_code": r["group_code"],
                "group_description": lookup_group(r["group_code"]),
                "reason_code": r["reason_code"],
                "reason_description": lookup_carc(r["reason_code"]),
                "total_amount": r["total_amount"],
                "count": r["count"],
            })

        # File count
        file_count_row = db.execute("SELECT COUNT(*) as cnt FROM edi_files").fetchone()

        return {
            "total_payments": totals["total_payments"],
            "total_charges": totals["total_charges"],
            "total_adjustments": total_adjustments,
            "total_claims": totals["total_claims"],
            "claims_by_status": claims_by_status,
            "top_denial_reasons": top_denial_reasons,
            "top_adjustments": top_adjustments,
            "file_count": file_count_row["cnt"],
        }
    finally:
        db.close()
