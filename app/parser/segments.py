"""Per-segment parsers for EDI X12 835 segments."""
from app.parser.delimiters import Delimiters


def parse_isa(elements: list[str], delimiters: Delimiters) -> dict:
    """Parse ISA (Interchange Control Header) segment."""
    return {
        "sender_qualifier": _get(elements, 5, ""),
        "sender_id": _get(elements, 6, "").strip(),
        "receiver_qualifier": _get(elements, 7, ""),
        "receiver_id": _get(elements, 8, "").strip(),
        "date": _get(elements, 9, ""),
        "time": _get(elements, 10, ""),
        "control_number": _get(elements, 13, "").strip(),
    }


def parse_gs(elements: list[str], delimiters: Delimiters) -> dict:
    """Parse GS (Functional Group Header) segment."""
    return {
        "functional_id": _get(elements, 1, ""),
        "sender_code": _get(elements, 2, ""),
        "receiver_code": _get(elements, 3, ""),
        "date": _get(elements, 4, ""),
        "control_number": _get(elements, 6, ""),
    }


def parse_bpr(elements: list[str], delimiters: Delimiters) -> dict:
    """Parse BPR (Financial Information) segment."""
    return {
        "transaction_type": _get(elements, 1, ""),
        "amount": _to_float(_get(elements, 2, "0")),
        "credit_debit": _get(elements, 3, ""),
        "payment_method": _get(elements, 4, ""),
        "payment_date": _get(elements, 16, ""),
    }


def parse_trn(elements: list[str], delimiters: Delimiters) -> dict:
    """Parse TRN (Reassociation Trace Number) segment."""
    return {
        "reference": _get(elements, 2, ""),
        "originator": _get(elements, 3, ""),
    }


def parse_per(elements: list[str], delimiters: Delimiters) -> dict:
    """Parse PER (Administrative Contact) segment."""
    result = {
        "contact_name": _get(elements, 2, ""),
        "contact_phone": "",
        "contact_email": "",
    }
    # PER segment has qualifier/value pairs starting at element 3
    i = 3
    while i + 1 < len(elements):
        qualifier = elements[i]
        value = elements[i + 1] if i + 1 < len(elements) else ""
        if qualifier == "TE":
            result["contact_phone"] = value
        elif qualifier == "EM":
            result["contact_email"] = value
        i += 2
    return result


def parse_n1(elements: list[str], delimiters: Delimiters) -> dict:
    """Parse N1 (Name) segment — used for payer/payee/patient/provider."""
    return {
        "entity_id": _get(elements, 1, ""),
        "name": _get(elements, 2, ""),
        "id_qualifier": _get(elements, 3, ""),
        "id": _get(elements, 4, ""),
    }


def parse_nm1(elements: list[str], delimiters: Delimiters) -> dict:
    """Parse NM1 (Individual or Organizational Name) segment."""
    return {
        "entity_id": _get(elements, 1, ""),
        "entity_type": _get(elements, 2, ""),
        "last_name": _get(elements, 3, ""),
        "first_name": _get(elements, 4, ""),
        "middle_name": _get(elements, 5, ""),
        "suffix": _get(elements, 6, ""),
        "id_qualifier": _get(elements, 8, ""),
        "id": _get(elements, 9, ""),
    }


def parse_clp(elements: list[str], delimiters: Delimiters) -> dict:
    """Parse CLP (Claim Payment Information) segment."""
    return {
        "claim_id": _get(elements, 1, ""),
        "status_code": _get(elements, 2, ""),
        "total_charge": _to_float(_get(elements, 3, "0")),
        "total_payment": _to_float(_get(elements, 4, "0")),
        "patient_responsibility": _to_float(_get(elements, 5, "0")),
        "plan_code": _get(elements, 6, ""),
        "filing_indicator": _get(elements, 6, ""),
        "drg_code": _get(elements, 7, ""),
        "drg_weight": _to_float(_get(elements, 8, "0")),
        "facility_type": _get(elements, 9, ""),
    }


def parse_cas(elements: list[str], delimiters: Delimiters) -> list[dict]:
    """Parse CAS (Claim Adjustment) segment.

    Handles multi-trio format: CAS*group*reason1*amount1*qty1*reason2*amount2*qty2...
    Up to 6 reason/amount/quantity trios per segment.
    """
    adjustments = []
    group_code = _get(elements, 1, "")

    # Trios start at index 2, each trio is 3 elements: reason, amount, quantity
    i = 2
    while i < len(elements) and elements[i]:
        reason_code = elements[i]
        amount = _to_float(_get(elements, i + 1, "0"))
        quantity = _to_float(_get(elements, i + 2, "0"))
        adjustments.append({
            "group_code": group_code,
            "reason_code": reason_code,
            "amount": amount,
            "quantity": quantity,
        })
        i += 3

    return adjustments


def parse_svc(elements: list[str], delimiters: Delimiters) -> dict:
    """Parse SVC (Service Payment Information) segment.

    SVC01 is a composite element: procedure_qualifier:procedure_code:modifier1:modifier2...
    """
    composite = _get(elements, 1, "")
    parts = composite.split(delimiters.sub_element) if composite else [""]

    procedure_code = parts[1] if len(parts) > 1 else parts[0]
    modifiers = parts[2:] if len(parts) > 2 else []
    modifiers = [m for m in modifiers if m]  # filter empty

    # Check if first part is a qualifier (HC, AD, ER, etc.)
    qualifier = parts[0] if len(parts) > 1 else ""

    return {
        "procedure_qualifier": qualifier,
        "procedure_code": procedure_code,
        "procedure_modifiers": ":".join(modifiers) if modifiers else "",
        "charge_amount": _to_float(_get(elements, 2, "0")),
        "payment_amount": _to_float(_get(elements, 3, "0")),
        "revenue_code": _get(elements, 4, ""),
        "units": _to_float(_get(elements, 5, "0")),
        "original_procedure": _get(elements, 6, ""),
    }


def parse_dtm(elements: list[str], delimiters: Delimiters) -> dict:
    """Parse DTM (Date/Time Reference) segment."""
    return {
        "qualifier": _get(elements, 1, ""),
        "date": _get(elements, 2, ""),
    }


def parse_ref(elements: list[str], delimiters: Delimiters) -> dict:
    """Parse REF (Reference Identification) segment."""
    return {
        "qualifier": _get(elements, 1, ""),
        "value": _get(elements, 2, ""),
    }


def parse_plb(elements: list[str], delimiters: Delimiters) -> list[dict]:
    """Parse PLB (Provider Level Balance) segment.

    PLB*provider_id*fiscal_period*reason1*amount1*reason2*amount2...
    """
    adjustments = []
    provider_id = _get(elements, 1, "")
    fiscal_period = _get(elements, 2, "")

    # Reason/amount pairs start at index 3
    i = 3
    while i + 1 < len(elements) and elements[i]:
        reason_raw = elements[i]
        # Reason might be composite (reason:reference)
        reason_code = reason_raw.split(delimiters.sub_element)[0] if reason_raw else ""
        amount = _to_float(_get(elements, i + 1, "0"))
        adjustments.append({
            "provider_id": provider_id,
            "fiscal_period_end": fiscal_period,
            "reason_code": reason_code,
            "amount": amount,
        })
        i += 2

    return adjustments


def parse_amt(elements: list[str], delimiters: Delimiters) -> dict:
    """Parse AMT (Monetary Amount) segment."""
    return {
        "qualifier": _get(elements, 1, ""),
        "amount": _to_float(_get(elements, 2, "0")),
    }


def parse_qty(elements: list[str], delimiters: Delimiters) -> dict:
    """Parse QTY (Quantity) segment."""
    return {
        "qualifier": _get(elements, 1, ""),
        "quantity": _to_float(_get(elements, 2, "0")),
    }


def _get(lst: list, index: int, default: str = "") -> str:
    """Safely get element from list."""
    try:
        return lst[index] if index < len(lst) else default
    except (IndexError, TypeError):
        return default


def _to_float(value: str) -> float:
    """Convert string to float, returning 0.0 on failure."""
    try:
        return float(value) if value else 0.0
    except (ValueError, TypeError):
        return 0.0
