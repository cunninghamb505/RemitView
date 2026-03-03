"""Analytics service for denial trends, payer comparisons, and adjustment summaries."""
from app.database import get_db
from app.parser.codes import lookup_group, lookup_carc, lookup_status


def get_denial_trends(
    group_by: str = "reason",
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """Get denial/adjustment trends over time, grouped by reason, payer, or provider."""
    db = get_db()
    try:
        conditions = []
        params = []

        if start_date:
            conditions.append("c.claim_date_start >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("c.claim_date_start <= ?")
            params.append(end_date)

        where = f"AND {' AND '.join(conditions)}" if conditions else ""

        if group_by == "payer":
            query = f"""
                SELECT f.payer_name as group_key,
                       SUBSTR(c.claim_date_start, 1, 6) as period,
                       SUM(sa.amount) as total_amount,
                       COUNT(DISTINCT c.id) as claim_count
                FROM service_adjustments sa
                JOIN service_lines sl ON sl.id = sa.service_line_id
                JOIN claims c ON c.id = sl.claim_id
                JOIN edi_files f ON f.id = c.file_id
                WHERE c.claim_date_start IS NOT NULL AND c.claim_date_start != ''
                {where}
                GROUP BY f.payer_name, period
                ORDER BY period, f.payer_name
            """
        elif group_by == "provider":
            query = f"""
                SELECT c.rendering_provider_name as group_key,
                       SUBSTR(c.claim_date_start, 1, 6) as period,
                       SUM(sa.amount) as total_amount,
                       COUNT(DISTINCT c.id) as claim_count
                FROM service_adjustments sa
                JOIN service_lines sl ON sl.id = sa.service_line_id
                JOIN claims c ON c.id = sl.claim_id
                WHERE c.claim_date_start IS NOT NULL AND c.claim_date_start != ''
                {where}
                GROUP BY c.rendering_provider_name, period
                ORDER BY period, c.rendering_provider_name
            """
        else:  # reason
            query = f"""
                SELECT (sa.group_code || '-' || sa.reason_code) as group_key,
                       SUBSTR(c.claim_date_start, 1, 6) as period,
                       SUM(sa.amount) as total_amount,
                       COUNT(*) as claim_count
                FROM service_adjustments sa
                JOIN service_lines sl ON sl.id = sa.service_line_id
                JOIN claims c ON c.id = sl.claim_id
                WHERE c.claim_date_start IS NOT NULL AND c.claim_date_start != ''
                {where}
                GROUP BY sa.group_code, sa.reason_code, period
                ORDER BY period, group_key
            """

        rows = db.execute(query, params).fetchall()

        # Organize into series
        periods = sorted(set(dict(r)["period"] for r in rows))
        series_map = {}
        for r in rows:
            d = dict(r)
            key = d["group_key"] or "Unknown"
            if key not in series_map:
                series_map[key] = {}
            series_map[key][d["period"]] = {
                "amount": d["total_amount"],
                "count": d["claim_count"],
            }

        # Limit to top 8 series by total amount
        totals = {k: sum(v.get("amount", 0) for v in vals.values()) for k, vals in series_map.items()}
        top_keys = sorted(totals, key=totals.get, reverse=True)[:8]

        # Format periods as readable dates
        formatted_periods = []
        for p in periods:
            if len(p) >= 6:
                formatted_periods.append(f"{p[:4]}-{p[4:6]}")
            else:
                formatted_periods.append(p)

        series = []
        for key in top_keys:
            data = series_map[key]
            label = key
            if group_by == "reason" and "-" in key:
                parts = key.split("-", 1)
                desc = lookup_carc(parts[1])
                label = f"{key}: {desc[:40]}"
            series.append({
                "label": label,
                "amounts": [data.get(p, {}).get("amount", 0) for p in periods],
                "counts": [data.get(p, {}).get("count", 0) for p in periods],
            })

        return {
            "periods": formatted_periods,
            "series": series,
            "group_by": group_by,
        }
    finally:
        db.close()


def get_payer_comparison() -> dict:
    """Compare payers by payment rate and top denial reasons."""
    db = get_db()
    try:
        payer_rows = db.execute("""
            SELECT f.payer_name,
                   COUNT(c.id) as total_claims,
                   SUM(c.clp_total_charge) as total_charges,
                   SUM(c.clp_total_payment) as total_payments,
                   SUM(CASE WHEN c.clp_status_code = '4' THEN 1 ELSE 0 END) as denied_count,
                   AVG(c.clp_total_payment) as avg_payment
            FROM claims c
            JOIN edi_files f ON f.id = c.file_id
            GROUP BY f.payer_name
            ORDER BY total_payments DESC
        """).fetchall()

        payers = []
        for r in payer_rows:
            d = dict(r)
            d["payer_name"] = d["payer_name"] or "Unknown"
            charges = d["total_charges"] or 0
            d["payment_rate"] = round((d["total_payments"] or 0) / charges * 100, 1) if charges > 0 else 0
            d["denial_rate"] = round((d["denied_count"] or 0) / d["total_claims"] * 100, 1) if d["total_claims"] > 0 else 0

            # Top denial reasons for this payer
            reason_rows = db.execute("""
                SELECT sa.group_code, sa.reason_code, SUM(sa.amount) as total_amount, COUNT(*) as count
                FROM service_adjustments sa
                JOIN service_lines sl ON sl.id = sa.service_line_id
                JOIN claims c ON c.id = sl.claim_id
                JOIN edi_files f ON f.id = c.file_id
                WHERE f.payer_name = ?
                GROUP BY sa.group_code, sa.reason_code
                ORDER BY total_amount DESC
                LIMIT 5
            """, (r["payer_name"],)).fetchall()

            d["top_reasons"] = []
            for rr in reason_rows:
                rd = dict(rr)
                rd["reason_description"] = lookup_carc(rd["reason_code"])
                rd["group_description"] = lookup_group(rd["group_code"])
                d["top_reasons"].append(rd)

            payers.append(d)

        return {"payers": payers}
    finally:
        db.close()


def get_adjustment_summary() -> dict:
    """Get combined adjustment summary across claim and service levels."""
    db = get_db()
    try:
        # Group code totals (union of claim + service adjustments)
        group_rows = db.execute("""
            SELECT group_code, SUM(amount) as total_amount, COUNT(*) as count
            FROM (
                SELECT group_code, amount FROM claim_adjustments
                UNION ALL
                SELECT group_code, amount FROM service_adjustments
            )
            GROUP BY group_code
            ORDER BY total_amount DESC
        """).fetchall()

        group_summary = []
        for r in group_rows:
            d = dict(r)
            d["group_description"] = lookup_group(d["group_code"])
            group_summary.append(d)

        # Detailed reason code breakdown
        detail_rows = db.execute("""
            SELECT group_code, reason_code, SUM(amount) as total_amount, COUNT(*) as count
            FROM (
                SELECT group_code, reason_code, amount FROM claim_adjustments
                UNION ALL
                SELECT group_code, reason_code, amount FROM service_adjustments
            )
            GROUP BY group_code, reason_code
            ORDER BY total_amount DESC
            LIMIT 25
        """).fetchall()

        details = []
        for r in detail_rows:
            d = dict(r)
            d["group_description"] = lookup_group(d["group_code"])
            d["reason_description"] = lookup_carc(d["reason_code"])
            details.append(d)

        return {
            "group_summary": group_summary,
            "details": details,
        }
    finally:
        db.close()
