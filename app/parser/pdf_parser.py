"""PDF remittance advice parser using pdfplumber."""
import pdfplumber
import io
from app.parser.pdf_patterns import PATTERNS, parse_money


def parse_pdf_remittance(pdf_bytes: bytes) -> dict:
    """Parse a PDF remittance advice and extract data in a structure
    compatible with the EDI parser output.

    Returns a dict with envelope, header, payer, payee, claims, provider_adjustments,
    and a pdf_parsing_notes field with extraction details.
    """
    notes = []
    full_text = ""

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    if not full_text.strip():
        raise ValueError("Could not extract text from PDF")

    notes.append(f"Extracted {len(full_text)} characters from PDF")

    # Extract header info
    check_number = _find(PATTERNS["check_number"], full_text)
    check_date = _find(PATTERNS["check_date"], full_text)
    check_amount = _find(PATTERNS["check_amount"], full_text)
    payer_name = _find(PATTERNS["payer_name"], full_text)
    provider_name = _find(PATTERNS["provider_name"], full_text)
    provider_npi = _find(PATTERNS["provider_npi"], full_text)

    # Build header
    header = {
        "transaction_type": "I",
        "amount": parse_money(check_amount) if check_amount else 0,
        "credit_debit": "C",
        "payment_method": "CHK",
        "payment_date": check_date or "",
        "reference": check_number or "",
        "originator": "",
        "contact_name": "",
        "contact_phone": "",
        "contact_email": "",
    }

    # Build envelope (minimal for PDF sources)
    envelope = {
        "sender_id": "",
        "receiver_id": "",
        "date": "",
        "control_number": check_number or "",
        "gs_functional_id": "",
        "gs_sender_code": "",
        "gs_receiver_code": "",
        "gs_date": "",
        "gs_control_number": "",
    }

    payer = {"name": payer_name or "Unknown Payer", "id": ""}
    payee = {"name": provider_name or "Unknown Provider", "id": provider_npi or ""}

    # Extract claims
    claims = []
    claim_matches = list(PATTERNS["claim_line"].finditer(full_text))

    if claim_matches:
        notes.append(f"Found {len(claim_matches)} claim lines")
        for m in claim_matches:
            claim = {
                "claim_id": m.group("claim_id"),
                "status_code": "1",  # Assume processed
                "total_charge": parse_money(m.group("charge")),
                "total_payment": parse_money(m.group("payment")),
                "plan_code": "",
                "filing_indicator": "",
                "drg_code": "",
                "drg_weight": 0,
                "facility_type": "",
                "patient": {
                    "last_name": m.group("patient").strip(),
                    "first_name": "",
                    "id": "",
                },
                "rendering_provider": {
                    "last_name": provider_name or "",
                    "first_name": "",
                    "id": provider_npi or "",
                },
                "crossover_payer": {"name": "", "id": ""},
                "dates": {},
                "adjustments": [],
                "service_lines": [],
            }
            claims.append(claim)
    else:
        notes.append("No structured claim lines found — created placeholder claim")
        if check_amount:
            claims.append({
                "claim_id": check_number or "PDF-001",
                "status_code": "1",
                "total_charge": parse_money(check_amount),
                "total_payment": parse_money(check_amount),
                "plan_code": "",
                "filing_indicator": "",
                "drg_code": "",
                "drg_weight": 0,
                "facility_type": "",
                "patient": {"last_name": "See PDF", "first_name": "", "id": ""},
                "rendering_provider": {"last_name": provider_name or "", "first_name": "", "id": provider_npi or ""},
                "crossover_payer": {"name": "", "id": ""},
                "dates": {},
                "adjustments": [],
                "service_lines": [],
            })

    # Try to extract adjustments
    adj_matches = list(PATTERNS["adjustment"].finditer(full_text))
    if adj_matches and claims:
        notes.append(f"Found {len(adj_matches)} adjustment entries")
        for m in adj_matches:
            adj = {
                "group_code": m.group("group"),
                "reason_code": m.group("reason"),
                "amount": parse_money(m.group("amount")),
                "quantity": 0,
            }
            claims[0]["adjustments"].append(adj)

    return {
        "envelope": envelope,
        "header": header,
        "payer": payer,
        "payee": payee,
        "claims": claims,
        "provider_adjustments": [],
        "pdf_parsing_notes": "; ".join(notes),
    }


def _find(pattern, text: str) -> str | None:
    """Find first match group in text."""
    m = pattern.search(text)
    return m.group(1).strip() if m else None
