"""File upload, parsing, and storage service."""
import sqlite3
from app.database import get_db
from app.parser.edi_parser import parse_835


def parse_and_store(raw_content: str, filename: str) -> int:
    """Parse an 835 file and store all data in the database.

    Returns the file ID.
    """
    parsed = parse_835(raw_content)
    db = get_db()
    try:
        file_id = _store_file(db, parsed, filename)
        _store_claims(db, file_id, parsed["claims"])
        _store_provider_adjustments(db, file_id, parsed["provider_adjustments"])
        db.commit()
        return file_id
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def list_files() -> list[dict]:
    """List all loaded files with claim counts."""
    db = get_db()
    try:
        rows = db.execute("""
            SELECT f.*, COUNT(c.id) as claim_count
            FROM edi_files f
            LEFT JOIN claims c ON c.file_id = f.id
            GROUP BY f.id
            ORDER BY f.uploaded_at DESC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


def delete_file(file_id: int) -> bool:
    """Delete a file and all related data (CASCADE)."""
    db = get_db()
    try:
        cursor = db.execute("DELETE FROM edi_files WHERE id = ?", (file_id,))
        db.commit()
        return cursor.rowcount > 0
    finally:
        db.close()


def _store_file(db: sqlite3.Connection, parsed: dict, filename: str) -> int:
    """Store file envelope and header data."""
    env = parsed["envelope"]
    hdr = parsed["header"]
    payer = parsed["payer"]
    payee = parsed["payee"]

    cursor = db.execute("""
        INSERT INTO edi_files (
            filename, isa_sender_id, isa_receiver_id, isa_date, isa_control_number,
            gs_functional_id, gs_sender_code, gs_receiver_code, gs_date, gs_control_number,
            bpr_transaction_type, bpr_amount, bpr_credit_debit, bpr_payment_method, bpr_payment_date,
            trn_reference, trn_originator,
            payer_name, payer_id, payee_name, payee_id, payee_npi,
            contact_name, contact_phone, contact_email
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        filename,
        env.get("sender_id", ""),
        env.get("receiver_id", ""),
        env.get("date", ""),
        env.get("control_number", ""),
        env.get("gs_functional_id", ""),
        env.get("gs_sender_code", ""),
        env.get("gs_receiver_code", ""),
        env.get("gs_date", ""),
        env.get("gs_control_number", ""),
        hdr.get("transaction_type", ""),
        hdr.get("amount", 0),
        hdr.get("credit_debit", ""),
        hdr.get("payment_method", ""),
        hdr.get("payment_date", ""),
        hdr.get("reference", ""),
        hdr.get("originator", ""),
        payer.get("name", ""),
        payer.get("id", ""),
        payee.get("name", ""),
        payee.get("id", ""),
        payee.get("id", ""),  # NPI is the PE N1 id for XX qualifier
        hdr.get("contact_name", ""),
        hdr.get("contact_phone", ""),
        hdr.get("contact_email", ""),
    ))
    return cursor.lastrowid


def _store_claims(db: sqlite3.Connection, file_id: int, claims: list[dict]):
    """Store all claims, their adjustments, and service lines."""
    for claim in claims:
        patient = claim.get("patient", {})
        provider = claim.get("rendering_provider", {})
        crossover = claim.get("crossover_payer", {})
        dates = claim.get("dates", {})

        # Build patient name
        patient_name = ""
        if patient.get("last_name"):
            patient_name = patient["last_name"]
            if patient.get("first_name"):
                patient_name = f"{patient['first_name']} {patient_name}"

        # Build provider name
        provider_name = ""
        if provider.get("last_name"):
            provider_name = provider["last_name"]
            if provider.get("first_name"):
                provider_name = f"{provider['first_name']} {provider_name}"

        # Calculate total adjustments
        total_adj = sum(a.get("amount", 0) for a in claim.get("adjustments", []))

        cursor = db.execute("""
            INSERT INTO claims (
                file_id, clp_claim_id, clp_status_code, clp_total_charge, clp_total_payment,
                clp_plan_code, clp_filing_indicator, clp_drg_code, clp_drg_weight, clp_facility_type,
                patient_name, patient_id, patient_first_name, patient_last_name,
                rendering_provider_name, rendering_provider_id,
                crossover_payer_name, crossover_payer_id,
                claim_date_start, claim_date_end, claim_received_date,
                total_adjustments
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_id,
            claim.get("claim_id", ""),
            claim.get("status_code", ""),
            claim.get("total_charge", 0),
            claim.get("total_payment", 0),
            claim.get("plan_code", ""),
            claim.get("filing_indicator", ""),
            claim.get("drg_code", ""),
            claim.get("drg_weight", 0),
            claim.get("facility_type", ""),
            patient_name,
            patient.get("id", ""),
            patient.get("first_name", ""),
            patient.get("last_name", ""),
            provider_name,
            provider.get("id", ""),
            crossover.get("name", ""),
            crossover.get("id", ""),
            dates.get("claim_start", ""),
            dates.get("claim_end", ""),
            dates.get("received", ""),
            total_adj,
        ))
        claim_id = cursor.lastrowid

        # Store claim-level adjustments
        for adj in claim.get("adjustments", []):
            db.execute("""
                INSERT INTO claim_adjustments (claim_id, group_code, reason_code, amount, quantity)
                VALUES (?, ?, ?, ?, ?)
            """, (claim_id, adj["group_code"], adj["reason_code"], adj["amount"], adj["quantity"]))

        # Store service lines
        for svc in claim.get("service_lines", []):
            svc_dates = svc.get("dates", {})
            svc_cursor = db.execute("""
                INSERT INTO service_lines (
                    claim_id, procedure_code, procedure_modifiers, revenue_code,
                    charge_amount, payment_amount, units,
                    date_start, date_end, control_number, rendering_provider_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                claim_id,
                svc.get("procedure_code", ""),
                svc.get("procedure_modifiers", ""),
                svc.get("revenue_code", ""),
                svc.get("charge_amount", 0),
                svc.get("payment_amount", 0),
                svc.get("units", 0),
                svc_dates.get("service_date", svc_dates.get("service_start", "")),
                svc_dates.get("service_end", ""),
                svc.get("control_number", ""),
                svc.get("rendering_provider_id", ""),
            ))
            svc_id = svc_cursor.lastrowid

            # Store service-level adjustments
            for adj in svc.get("adjustments", []):
                db.execute("""
                    INSERT INTO service_adjustments (service_line_id, group_code, reason_code, amount, quantity)
                    VALUES (?, ?, ?, ?, ?)
                """, (svc_id, adj["group_code"], adj["reason_code"], adj["amount"], adj["quantity"]))


def _store_provider_adjustments(db: sqlite3.Connection, file_id: int, adjustments: list[dict]):
    """Store PLB provider-level adjustments."""
    for adj in adjustments:
        db.execute("""
            INSERT INTO provider_adjustments (file_id, provider_id, fiscal_period_end, reason_code, amount)
            VALUES (?, ?, ?, ?, ?)
        """, (file_id, adj["provider_id"], adj["fiscal_period_end"], adj["reason_code"], adj["amount"]))
