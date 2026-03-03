"""Batch operations service for claims."""
import csv
import io
from app.database import get_db


def batch_flag(claim_ids: list[int], flag_type: str, note: str) -> int:
    """Flag multiple claims in a single transaction. Returns count of flags created."""
    db = get_db()
    try:
        count = 0
        for cid in claim_ids:
            db.execute(
                "INSERT INTO claim_flags (claim_id, flag_type, note) VALUES (?, ?, ?)",
                (cid, flag_type, note),
            )
            count += 1
        db.commit()
        return count
    finally:
        db.close()


def batch_resolve_flags(claim_ids: list[int]) -> int:
    """Resolve all open flags on selected claims. Returns count resolved."""
    if not claim_ids:
        return 0
    db = get_db()
    try:
        placeholders = ",".join("?" for _ in claim_ids)
        cursor = db.execute(
            f"UPDATE claim_flags SET resolved_at = CURRENT_TIMESTAMP "
            f"WHERE claim_id IN ({placeholders}) AND resolved_at IS NULL",
            claim_ids,
        )
        db.commit()
        return cursor.rowcount
    finally:
        db.close()


def batch_export_csv(claim_ids: list[int]) -> str:
    """Export selected claims as CSV string."""
    if not claim_ids:
        return ""
    db = get_db()
    try:
        placeholders = ",".join("?" for _ in claim_ids)
        rows = db.execute(
            f"""SELECT c.id, c.clp_claim_id, c.clp_status_code, c.clp_total_charge,
                       c.clp_total_payment, c.patient_name, c.rendering_provider_name,
                       c.claim_date_start, c.claim_date_end, c.workflow_status,
                       f.filename
                FROM claims c
                JOIN edi_files f ON f.id = c.file_id
                WHERE c.id IN ({placeholders})
                ORDER BY c.id""",
            claim_ids,
        ).fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID", "Claim ID", "Status", "Charges", "Payment",
            "Patient", "Provider", "Date Start", "Date End",
            "Workflow Status", "Filename",
        ])
        for r in rows:
            writer.writerow([
                r["id"], r["clp_claim_id"], r["clp_status_code"],
                r["clp_total_charge"], r["clp_total_payment"],
                r["patient_name"], r["rendering_provider_name"],
                r["claim_date_start"], r["claim_date_end"],
                r["workflow_status"], r["filename"],
            ])
        return output.getvalue()
    finally:
        db.close()
