"""Basic 837 claim parser — extracts claim IDs, expected payments, and procedure codes
for matching against 835 remittance data."""
from app.parser.delimiters import detect_delimiters


def parse_837(raw: str) -> list[dict]:
    """Parse an 837 claim file and extract key data for matching.

    Returns a list of claims with:
    - claim_id
    - expected_payment (total charges from CLM segment)
    - dx_codes (from HI segments)
    - procedure_codes (from SV1/SV2 segments)
    """
    delimiters = detect_delimiters(raw)
    seg_sep = delimiters.segment
    elem_sep = delimiters.element
    sub_sep = delimiters.sub_element

    segments = [s.strip() for s in raw.split(seg_sep) if s.strip()]
    claims = []
    current_claim = None

    for seg in segments:
        elements = seg.split(elem_sep)
        seg_id = elements[0].strip()

        if seg_id == "CLM":
            # Save previous claim
            if current_claim:
                claims.append(current_claim)
            claim_id = elements[1] if len(elements) > 1 else ""
            charge = 0
            try:
                charge = float(elements[2]) if len(elements) > 2 else 0
            except (ValueError, TypeError):
                pass
            current_claim = {
                "claim_id": claim_id,
                "expected_payment": charge,
                "dx_codes": [],
                "procedure_codes": [],
            }

        elif seg_id == "HI" and current_claim:
            # Health information — diagnosis codes
            for elem in elements[1:]:
                parts = elem.split(sub_sep)
                if len(parts) >= 2:
                    current_claim["dx_codes"].append(parts[1])

        elif seg_id in ("SV1", "SV2") and current_claim:
            # Service line — procedure code
            if len(elements) > 1:
                comp = elements[1].split(sub_sep)
                if len(comp) >= 2:
                    current_claim["procedure_codes"].append(comp[1])

    if current_claim:
        claims.append(current_claim)

    return claims
