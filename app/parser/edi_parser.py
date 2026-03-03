"""State-machine EDI X12 835 parser.

Walks segments sequentially, tracking context (file-level, claim-level,
service-line-level) to correctly assign CAS adjustments and DTM dates.
"""
from app.parser.delimiters import detect_delimiters
from app.parser import segments as seg


def parse_835(raw: str) -> dict:
    """Parse an EDI 835 file into a structured dictionary.

    Returns:
        {
            "envelope": { ISA/GS fields },
            "header": { BPR/TRN/PER fields },
            "payer": { N1 PR fields },
            "payee": { N1 PE fields },
            "claims": [ { CLP fields, nm1s, dates, adjustments, service_lines } ],
            "provider_adjustments": [ PLB entries ],
        }
    """
    delimiters = detect_delimiters(raw)

    # Split into segments, stripping whitespace
    raw_segments = raw.split(delimiters.segment)
    segment_list = []
    for s in raw_segments:
        s = s.strip()
        if s:
            segment_list.append(s)

    result = {
        "envelope": {},
        "header": {},
        "payer": {},
        "payee": {},
        "claims": [],
        "provider_adjustments": [],
    }

    # State tracking
    current_claim = None
    current_service = None
    in_header = True  # Before first CLP

    for raw_seg in segment_list:
        elements = raw_seg.split(delimiters.element)
        seg_id = elements[0].strip()

        if seg_id == "ISA":
            isa = seg.parse_isa(elements, delimiters)
            result["envelope"].update(isa)

        elif seg_id == "GS":
            gs = seg.parse_gs(elements, delimiters)
            result["envelope"].update({f"gs_{k}": v for k, v in gs.items()})

        elif seg_id == "BPR":
            bpr = seg.parse_bpr(elements, delimiters)
            result["header"].update(bpr)

        elif seg_id == "TRN":
            trn = seg.parse_trn(elements, delimiters)
            result["header"].update(trn)

        elif seg_id == "PER":
            per = seg.parse_per(elements, delimiters)
            result["header"].update(per)

        elif seg_id == "N1":
            n1 = seg.parse_n1(elements, delimiters)
            if n1["entity_id"] == "PR":
                result["payer"] = n1
            elif n1["entity_id"] == "PE":
                result["payee"] = n1

        elif seg_id == "CLP":
            # Save previous claim if exists
            if current_claim is not None:
                _finalize_claim(current_claim, current_service)
                result["claims"].append(current_claim)

            in_header = False
            clp = seg.parse_clp(elements, delimiters)
            current_claim = {
                **clp,
                "patient": {},
                "rendering_provider": {},
                "crossover_payer": {},
                "dates": {},
                "adjustments": [],
                "service_lines": [],
            }
            current_service = None

        elif seg_id == "NM1":
            if current_claim is None:
                continue
            nm1 = seg.parse_nm1(elements, delimiters)
            entity = nm1["entity_id"]
            if entity == "QC":  # Patient
                current_claim["patient"] = nm1
            elif entity == "82":  # Rendering provider
                current_claim["rendering_provider"] = nm1
            elif entity == "TT":  # Crossover payer
                current_claim["crossover_payer"] = nm1

        elif seg_id == "SVC":
            if current_claim is None:
                continue
            # Finalize previous service if exists
            if current_service is not None:
                current_claim["service_lines"].append(current_service)

            svc = seg.parse_svc(elements, delimiters)
            current_service = {
                **svc,
                "adjustments": [],
                "dates": {},
                "control_number": "",
                "rendering_provider_id": "",
            }

        elif seg_id == "CAS":
            cas_list = seg.parse_cas(elements, delimiters)
            if current_service is not None:
                # Service-level CAS
                current_service["adjustments"].extend(cas_list)
            elif current_claim is not None:
                # Claim-level CAS (before any SVC in this claim)
                current_claim["adjustments"].extend(cas_list)

        elif seg_id == "DTM":
            dtm = seg.parse_dtm(elements, delimiters)
            qualifier = dtm["qualifier"]
            date_val = dtm["date"]

            if current_service is not None:
                if qualifier == "472":
                    current_service["dates"]["service_date"] = date_val
                elif qualifier == "150":
                    current_service["dates"]["service_start"] = date_val
                elif qualifier == "151":
                    current_service["dates"]["service_end"] = date_val
            elif current_claim is not None:
                if qualifier == "232":
                    current_claim["dates"]["claim_start"] = date_val
                elif qualifier == "233":
                    current_claim["dates"]["claim_end"] = date_val
                elif qualifier == "050":
                    current_claim["dates"]["received"] = date_val
            elif in_header:
                result["header"][f"dtm_{qualifier}"] = date_val

        elif seg_id == "REF":
            ref = seg.parse_ref(elements, delimiters)
            if current_service is not None and ref["qualifier"] == "6R":
                current_service["control_number"] = ref["value"]
            elif current_service is not None and ref["qualifier"] == "LU":
                current_service["rendering_provider_id"] = ref["value"]

        elif seg_id == "AMT":
            # AMT at service level — mostly informational
            pass

        elif seg_id == "PLB":
            plb_list = seg.parse_plb(elements, delimiters)
            result["provider_adjustments"].extend(plb_list)

        elif seg_id in ("SE", "GE", "IEA", "ST", "LX", "QTY"):
            # Envelope/control segments — skip
            pass

    # Finalize last claim
    if current_claim is not None:
        _finalize_claim(current_claim, current_service)
        result["claims"].append(current_claim)

    return result


def _finalize_claim(claim: dict, current_service: dict | None):
    """Append any pending service line to the claim."""
    if current_service is not None:
        claim["service_lines"].append(current_service)
