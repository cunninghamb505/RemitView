"""PDF report generation service using reportlab."""
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from app.database import get_db
from app.parser.codes import lookup_status, lookup_group, lookup_carc
from app.config import APP_NAME, APP_VERSION, APP_AUTHOR


def _make_doc(buffer, title):
    """Create a PDF document with standard margins."""
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=0.5 * inch, rightMargin=0.5 * inch,
        topMargin=0.5 * inch, bottomMargin=0.5 * inch,
        title=title, author=APP_AUTHOR,
    )
    return doc


def _header_style():
    styles = getSampleStyleSheet()
    return styles


def _make_table(headers, data, col_widths=None):
    """Create a styled table."""
    all_data = [headers] + data
    t = Table(all_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0D6EFD')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DEE2E6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t


def generate_claim_pdf(claim_id: int) -> bytes:
    """Generate a PDF report for a single claim."""
    db = get_db()
    try:
        claim = db.execute("""
            SELECT c.*, f.filename, f.payer_name, f.payee_name
            FROM claims c JOIN edi_files f ON f.id = c.file_id
            WHERE c.id = ?
        """, (claim_id,)).fetchone()
        if not claim:
            raise ValueError("Claim not found")

        cd = dict(claim)
        buffer = io.BytesIO()
        doc = _make_doc(buffer, f"Claim {cd['clp_claim_id']}")
        styles = _header_style()
        story = []

        # Title
        story.append(Paragraph(f"{APP_NAME} — Claim Report", styles['Title']))
        story.append(Spacer(1, 12))

        # Claim info table
        info_data = [
            ["Claim ID", cd.get("clp_claim_id", ""), "Status", f"{cd.get('clp_status_code', '')} - {lookup_status(cd.get('clp_status_code', ''))}"],
            ["Patient", cd.get("patient_name", ""), "Provider", cd.get("rendering_provider_name", "")],
            ["Charges", f"${cd.get('clp_total_charge', 0):,.2f}", "Payment", f"${cd.get('clp_total_payment', 0):,.2f}"],
            ["Plan Code", cd.get("clp_plan_code", ""), "DRG", cd.get("clp_drg_code", "")],
            ["Payer", cd.get("payer_name", ""), "Payee", cd.get("payee_name", "")],
            ["File", cd.get("filename", ""), "", ""],
        ]
        t = Table(info_data, colWidths=[1.2 * inch, 2.3 * inch, 1.2 * inch, 2.3 * inch])
        t.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DEE2E6')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8F9FA')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#F8F9FA')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 16))

        # Service lines
        svcs = db.execute(
            "SELECT * FROM service_lines WHERE claim_id = ? ORDER BY id", (claim_id,)
        ).fetchall()
        if svcs:
            story.append(Paragraph("Service Lines", styles['Heading2']))
            story.append(Spacer(1, 6))
            svc_data = []
            for s in svcs:
                sd = dict(s)
                svc_data.append([
                    sd.get("procedure_code", ""),
                    sd.get("procedure_modifiers", ""),
                    f"${sd.get('charge_amount', 0):,.2f}",
                    f"${sd.get('payment_amount', 0):,.2f}",
                    str(sd.get("units", "")),
                ])
            story.append(_make_table(
                ["Procedure", "Modifiers", "Charge", "Payment", "Units"],
                svc_data,
            ))
            story.append(Spacer(1, 16))

        # Adjustments
        adjs = db.execute(
            "SELECT * FROM claim_adjustments WHERE claim_id = ?", (claim_id,)
        ).fetchall()
        svc_adjs = []
        for s in svcs:
            sd = dict(s)
            rows = db.execute(
                "SELECT * FROM service_adjustments WHERE service_line_id = ?", (sd["id"],)
            ).fetchall()
            for r in rows:
                rd = dict(r)
                rd["_proc"] = sd.get("procedure_code", "")
                svc_adjs.append(rd)

        all_adjs = []
        for a in adjs:
            ad = dict(a)
            all_adjs.append([
                "Claim",
                ad.get("group_code", ""),
                ad.get("reason_code", ""),
                lookup_carc(ad.get("reason_code", "")),
                f"${ad.get('amount', 0):,.2f}",
            ])
        for sa in svc_adjs:
            all_adjs.append([
                f"Svc ({sa.get('_proc', '')})",
                sa.get("group_code", ""),
                sa.get("reason_code", ""),
                lookup_carc(sa.get("reason_code", "")),
                f"${sa.get('amount', 0):,.2f}",
            ])

        if all_adjs:
            story.append(Paragraph("Adjustments", styles['Heading2']))
            story.append(Spacer(1, 6))
            story.append(_make_table(
                ["Level", "Group", "Code", "Description", "Amount"],
                all_adjs,
            ))

        # Footer
        story.append(Spacer(1, 24))
        story.append(Paragraph(
            f"Generated by {APP_NAME} v{APP_VERSION} — {APP_AUTHOR}",
            ParagraphStyle('footer', fontSize=7, textColor=colors.HexColor('#6C757D')),
        ))

        doc.build(story)
        return buffer.getvalue()
    finally:
        db.close()


def generate_file_pdf(file_id: int) -> bytes:
    """Generate a PDF summary report for an entire file."""
    db = get_db()
    try:
        file_row = db.execute("SELECT * FROM edi_files WHERE id = ?", (file_id,)).fetchone()
        if not file_row:
            raise ValueError("File not found")

        fi = dict(file_row)
        buffer = io.BytesIO()
        doc = _make_doc(buffer, f"File Report - {fi['filename']}")
        styles = _header_style()
        story = []

        story.append(Paragraph(f"{APP_NAME} — File Report", styles['Title']))
        story.append(Paragraph(fi.get("filename", ""), styles['Heading2']))
        story.append(Spacer(1, 12))

        # File summary
        info_data = [
            ["Payer", fi.get("payer_name", ""), "Payee", fi.get("payee_name", "")],
            ["Payment", f"${fi.get('bpr_amount', 0):,.2f}", "Date", fi.get("bpr_payment_date", "")],
            ["Method", fi.get("bpr_payment_method", ""), "Reference", fi.get("trn_reference", "")],
        ]
        t = Table(info_data, colWidths=[1.2 * inch, 2.3 * inch, 1.2 * inch, 2.3 * inch])
        t.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DEE2E6')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8F9FA')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#F8F9FA')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 16))

        # Claims table
        claims = db.execute(
            "SELECT * FROM claims WHERE file_id = ? ORDER BY id", (file_id,)
        ).fetchall()
        if claims:
            story.append(Paragraph(f"Claims ({len(claims)})", styles['Heading2']))
            story.append(Spacer(1, 6))
            claim_data = []
            for c in claims:
                cd = dict(c)
                claim_data.append([
                    cd.get("clp_claim_id", ""),
                    cd.get("clp_status_code", ""),
                    cd.get("patient_name", ""),
                    f"${cd.get('clp_total_charge', 0):,.2f}",
                    f"${cd.get('clp_total_payment', 0):,.2f}",
                ])
            story.append(_make_table(
                ["Claim ID", "Status", "Patient", "Charges", "Payment"],
                claim_data,
            ))

        # Footer
        story.append(Spacer(1, 24))
        story.append(Paragraph(
            f"Generated by {APP_NAME} v{APP_VERSION} — {APP_AUTHOR}",
            ParagraphStyle('footer', fontSize=7, textColor=colors.HexColor('#6C757D')),
        ))

        doc.build(story)
        return buffer.getvalue()
    finally:
        db.close()
