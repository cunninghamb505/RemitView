"""Global search service — searches patients, claim IDs, and procedure codes."""
from app.database import get_db
from app.parser.codes import lookup_status


def global_search(query: str, limit: int = 50) -> dict:
    """Search across claims, patients, and procedure codes."""
    if not query or len(query) < 2:
        return {"results": [], "total": 0}

    db = get_db()
    try:
        search = f"%{query}%"
        results = []

        # Search claims by claim ID
        claim_rows = db.execute("""
            SELECT c.id, c.clp_claim_id, c.clp_status_code, c.patient_name,
                   c.clp_total_charge, c.clp_total_payment, f.filename
            FROM claims c
            JOIN edi_files f ON f.id = c.file_id
            WHERE c.clp_claim_id LIKE ?
            ORDER BY c.id DESC
            LIMIT ?
        """, (search, limit)).fetchall()

        for r in claim_rows:
            d = dict(r)
            results.append({
                "type": "claim",
                "id": d["id"],
                "title": f"Claim {d['clp_claim_id']}",
                "subtitle": f"{d['patient_name'] or 'Unknown'} — {lookup_status(d['clp_status_code'])}",
                "detail": f"${d['clp_total_payment']:,.2f} / ${d['clp_total_charge']:,.2f}",
                "link": f"#/claims/{d['id']}",
            })

        # Search by patient name
        patient_rows = db.execute("""
            SELECT c.id, c.clp_claim_id, c.clp_status_code, c.patient_name,
                   c.clp_total_charge, c.clp_total_payment, f.filename
            FROM claims c
            JOIN edi_files f ON f.id = c.file_id
            WHERE c.patient_name LIKE ? AND c.clp_claim_id NOT LIKE ?
            ORDER BY c.id DESC
            LIMIT ?
        """, (search, search, limit)).fetchall()

        for r in patient_rows:
            d = dict(r)
            results.append({
                "type": "patient",
                "id": d["id"],
                "title": d["patient_name"] or "Unknown",
                "subtitle": f"Claim {d['clp_claim_id']} — {lookup_status(d['clp_status_code'])}",
                "detail": f"${d['clp_total_payment']:,.2f}",
                "link": f"#/claims/{d['id']}",
            })

        # Search by procedure code
        proc_rows = db.execute("""
            SELECT sl.id, sl.procedure_code, sl.charge_amount, sl.payment_amount,
                   c.id as claim_id, c.clp_claim_id, c.patient_name
            FROM service_lines sl
            JOIN claims c ON c.id = sl.claim_id
            WHERE sl.procedure_code LIKE ?
            ORDER BY sl.id DESC
            LIMIT ?
        """, (search, limit)).fetchall()

        for r in proc_rows:
            d = dict(r)
            results.append({
                "type": "procedure",
                "id": d["claim_id"],
                "title": f"Procedure {d['procedure_code']}",
                "subtitle": f"Claim {d['clp_claim_id']} — {d['patient_name'] or 'Unknown'}",
                "detail": f"${d['payment_amount']:,.2f} / ${d['charge_amount']:,.2f}",
                "link": f"#/claims/{d['claim_id']}",
            })

        return {
            "results": results[:limit],
            "total": len(results),
            "query": query,
        }
    finally:
        db.close()
