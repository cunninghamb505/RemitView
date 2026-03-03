"""CSV export service."""
import csv
import io
from app.database import get_db
from app.parser.codes import lookup_status


def export_claims_csv(file_id: int | None = None) -> str:
    """Export claims to CSV format.

    Returns CSV content as a string.
    """
    db = get_db()
    try:
        conditions = []
        params = []
        if file_id:
            conditions.append("c.file_id = ?")
            params.append(file_id)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        rows = db.execute(f"""
            SELECT c.*, f.filename
            FROM claims c
            JOIN edi_files f ON f.id = c.file_id
            {where}
            ORDER BY c.id
        """, params).fetchall()

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Claim ID", "File", "Status Code", "Status", "Patient Name",
            "Patient ID", "Rendering Provider", "Provider ID",
            "Total Charge", "Total Payment", "Total Adjustments",
            "Plan Code", "Date Start", "Date End", "Date Received",
        ])

        for r in rows:
            d = dict(r)
            writer.writerow([
                d.get("clp_claim_id", ""),
                d.get("filename", ""),
                d.get("clp_status_code", ""),
                lookup_status(d.get("clp_status_code", "")),
                d.get("patient_name", ""),
                d.get("patient_id", ""),
                d.get("rendering_provider_name", ""),
                d.get("rendering_provider_id", ""),
                d.get("clp_total_charge", 0),
                d.get("clp_total_payment", 0),
                d.get("total_adjustments", 0),
                d.get("clp_plan_code", ""),
                d.get("claim_date_start", ""),
                d.get("claim_date_end", ""),
                d.get("claim_received_date", ""),
            ])

        return output.getvalue()
    finally:
        db.close()
