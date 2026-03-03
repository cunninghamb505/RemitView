"""837-835 claim matching service."""
from app.database import get_db
from app.parser.parser_837 import parse_837


def import_837_and_match(raw_content: str, filename: str) -> dict:
    """Parse an 837 file and match claims against existing 835 data.

    Returns match results with variance analysis.
    """
    claims_837 = parse_837(raw_content)
    db = get_db()
    try:
        matched = []
        unmatched = []

        for c837 in claims_837:
            # Find matching 835 claim by claim ID
            row = db.execute("""
                SELECT c.id, c.clp_claim_id, c.clp_total_charge, c.clp_total_payment,
                       c.patient_name, c.clp_status_code
                FROM claims c
                WHERE c.clp_claim_id = ?
                ORDER BY c.id DESC LIMIT 1
            """, (c837["claim_id"],)).fetchone()

            if row:
                r = dict(row)
                expected = c837["expected_payment"]
                actual = r["clp_total_payment"] or 0
                variance = actual - expected
                variance_pct = (variance / expected * 100) if expected > 0 else 0

                # Store 837 data
                db.execute("""
                    INSERT OR REPLACE INTO claim_837_data (claim_id, expected_payment, dx_codes, procedure_codes)
                    VALUES (?, ?, ?, ?)
                """, (
                    r["id"],
                    expected,
                    ",".join(c837.get("dx_codes", [])),
                    ",".join(c837.get("procedure_codes", [])),
                ))

                matched.append({
                    "claim_id": c837["claim_id"],
                    "expected_payment": expected,
                    "actual_payment": actual,
                    "variance": variance,
                    "variance_pct": round(variance_pct, 1),
                    "status_code": r["clp_status_code"],
                    "patient_name": r["patient_name"],
                    "flagged": abs(variance_pct) > 10,
                })
            else:
                unmatched.append({
                    "claim_id": c837["claim_id"],
                    "expected_payment": c837["expected_payment"],
                })

        db.commit()

        return {
            "filename": filename,
            "total_837_claims": len(claims_837),
            "matched_count": len(matched),
            "unmatched_count": len(unmatched),
            "matched": matched,
            "unmatched": unmatched,
        }
    finally:
        db.close()
