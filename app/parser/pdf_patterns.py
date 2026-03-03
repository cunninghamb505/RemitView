"""Regex patterns for parsing PDF remittance advice documents."""
import re

# Common payer PDF format patterns
PATTERNS = {
    # Payment/check info
    "check_number": re.compile(r"(?:Check|Payment|Trace)\s*(?:#|Number|No\.?)\s*[:\s]*(\S+)", re.IGNORECASE),
    "check_date": re.compile(r"(?:Check|Payment)\s*Date\s*[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", re.IGNORECASE),
    "check_amount": re.compile(r"(?:Check|Payment|Total\s+Payment)\s*(?:Amount)?\s*[:\s]*\$?([\d,]+\.?\d*)", re.IGNORECASE),

    # Payer info
    "payer_name": re.compile(r"(?:Payer|Insurance|Plan)\s*(?:Name)?\s*[:\s]*(.+?)(?:\n|$)", re.IGNORECASE),

    # Provider info
    "provider_name": re.compile(r"(?:Provider|Payee)\s*(?:Name)?\s*[:\s]*(.+?)(?:\n|$)", re.IGNORECASE),
    "provider_npi": re.compile(r"(?:NPI|Provider\s*ID)\s*[:\s]*(\d{10})", re.IGNORECASE),

    # Claim-level patterns
    "claim_line": re.compile(
        r"(?P<claim_id>\S+)\s+"
        r"(?P<patient>[A-Z][A-Za-z\s,]+?)\s+"
        r"(?P<charge>[\d,]+\.\d{2})\s+"
        r"(?P<payment>[\d,]+\.\d{2})",
        re.MULTILINE,
    ),

    # Service line patterns
    "service_line": re.compile(
        r"(?P<procedure>\d{5})\s*"
        r"(?P<modifier>[A-Z0-9]{2})?\s+"
        r"(?P<charge>[\d,]+\.\d{2})\s+"
        r"(?P<allowed>[\d,]+\.\d{2})?\s*"
        r"(?P<payment>[\d,]+\.\d{2})",
        re.MULTILINE,
    ),

    # Adjustment patterns
    "adjustment": re.compile(
        r"(?P<group>[A-Z]{2})\s*-?\s*(?P<reason>\d{1,3})\s+"
        r"(?P<amount>-?[\d,]+\.\d{2})",
        re.MULTILINE,
    ),

    # Date patterns
    "date_of_service": re.compile(
        r"(?:DOS|Date\s*of\s*Service|Service\s*Date)\s*[:\s]*"
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        re.IGNORECASE,
    ),

    # Patient info
    "patient_name": re.compile(
        r"(?:Patient|Member|Subscriber)\s*(?:Name)?\s*[:\s]*"
        r"([A-Z][A-Za-z\s,]+?)(?:\s{2,}|\n|$)",
        re.IGNORECASE,
    ),
    "patient_id": re.compile(
        r"(?:Patient|Member|Subscriber)\s*(?:ID|#|Number)\s*[:\s]*(\S+)",
        re.IGNORECASE,
    ),
}


def parse_money(val: str) -> float:
    """Parse a money string like '1,234.56' to float."""
    if not val:
        return 0.0
    return float(val.replace(",", ""))
