import json
import hashlib
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import qrcode
import io

try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))
    FONT_NORMAL = 'DejaVuSans'
    FONT_BOLD = 'DejaVuSans-Bold'
except Exception:
    FONT_NORMAL = 'Helvetica'
    FONT_BOLD = 'Helvetica-Bold'

class EnterpriseReportCanvas(canvas.Canvas):
    def __init__(self, *args, data_context=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_context = data_context or {}
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, total_pages):
        self.saveState()
        
        self.setFillColor(colors.HexColor("#0F172A"))
        self.rect(0, 252 * mm, 210 * mm, 45 * mm, fill=1, stroke=0)

        self.setFont(FONT_BOLD, 18)
        self.setFillColor(colors.HexColor("#C084FC"))
        self.drawString(15 * mm, 283 * mm, "SOURCEJET AI")

        self.setFont(FONT_BOLD, 8)
        self.setFillColor(colors.HexColor("#94A3B8"))
        self.drawString(15 * mm, 276 * mm, "GLOBAL QUALITY CONTROL & FACTORY AUDIT TERMINAL")
        self.drawString(15 * mm, 271 * mm, "OFFICIAL INSPECTION REPORT — ISO 2859-1 (AQL 2.5)")

        insp_id = self.data_context.get("inspection_id", "N/A")
        verify_url = f"https://sourcejet.ai/verify?id={insp_id}"
        
        qr = qrcode.QRCode(box_size=3, border=1)
        qr.add_data(verify_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        img_buffer = io.BytesIO()
        qr_img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        
        self.drawInlineImage(img_buffer, 172 * mm, 256 * mm, width=24 * mm, height=24 * mm)
        self.setFont(FONT_NORMAL, 6)
        self.setFillColor(colors.HexColor("#CBD5E1"))
        self.drawCentredString(184 * mm, 253 * mm, "SCAN TO VERIFY")

        stamp_x, stamp_y = 175 * mm, 55 * mm
        self.setStrokeColor(colors.HexColor("#4F46E5"))
        self.setLineWidth(0.8)
        self.circle(stamp_x, stamp_y, 14 * mm, stroke=1, fill=0)
        self.circle(stamp_x, stamp_y, 12.5 * mm, stroke=1, fill=0)

        self.setFont(FONT_BOLD, 5.5)
        self.setFillColor(colors.HexColor("#4F46E5"))
        self.drawCentredString(stamp_x, stamp_y + 6 * mm, "SOURCEJET AI")
        self.setFont(FONT_BOLD, 6.5)
        self.drawCentredString(stamp_x, stamp_y + 1 * mm, "OFFICIAL SEAL")
        self.setFont(FONT_NORMAL, 5)
        self.drawCentredString(stamp_x, stamp_y - 4 * mm, "VERIFIED AUDIT")

        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(15 * mm, 18 * mm, 195 * mm, 18 * mm)

        self.setFont(FONT_NORMAL, 6.5)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(15 * mm, 14 * mm, "DISCLAIMER: This report reflects findings at the time and place of inspection only within client instructions.")
        self.drawString(15 * mm, 10.5 * mm, "SourceJet AI is not liable for transport damages or latent manufacturing defects after field intervention.")

        doc_hash = self.data_context.get("data_hash", "UNKNOWN")
        self.setFont(FONT_BOLD, 6.5)
        self.drawString(15 * mm, 7 * mm, f"DOCUMENT INTEGRITY HASH: {doc_hash}")
        self.drawRightString(195 * mm, 7 * mm, f"Page {self._pageNumber} of {total_pages}")

        self.restoreState()

def build_pdf_report(data_json, output_pdf_path):
    raw_bytes = json.dumps(data_json, sort_keys=True).encode('utf-8')
    data_hash = hashlib.sha256(raw_bytes).hexdigest().upper()
    data_json["data_hash"] = data_hash

    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=50 * mm,
        bottomMargin=25 * mm
    )

    styles = getSampleStyleSheet()
    
    style_title = ParagraphStyle(
        'DocTitle', parent=styles['Normal'],
        fontName=FONT_BOLD, fontSize=12,
        textColor=colors.HexColor("#0F172A"), spaceAfter=4
    )
    style_label = ParagraphStyle(
        'MetaLabel', parent=styles['Normal'],
        fontName=FONT_BOLD, fontSize=8,
        textColor=colors.HexColor("#475569")
    )
    style_value = ParagraphStyle(
        'MetaValue', parent=styles['Normal'],
        fontName=FONT_NORMAL, fontSize=8,
        textColor=colors.HexColor("#0F172A")
    )
    style_body = ParagraphStyle(
        'BodyTextCustom', parent=styles['Normal'],
        fontName=FONT_NORMAL, fontSize=8.5,
        textColor=colors.HexColor("#334155"), leading=11
    )

    story = []

    story.append(Paragraph(f"FACTORY INSPECTION REPORT: {data_json.get('factory_name', '').upper()}", style_title))
    story.append(Spacer(1, 2 * mm))

    meta_table_data = [
        [
            Paragraph("Client Org:", style_label), Paragraph(data_json.get("client_name", "-"), style_value),
            Paragraph("Scheduled Date:", style_label), Paragraph(data_json.get("scheduled_date", "-"), style_value)
        ],
        [
            Paragraph("Assigned Inspector:", style_label), Paragraph(data_json.get("inspector_name", "-"), style_value),
            Paragraph("Inspection Type:", style_label), Paragraph(data_json.get("inspection_type", "-"), style_value)
        ],
        [
            Paragraph("City & Region:", style_label), Paragraph(f"{data_json.get('country', '')} • {data_json.get('city', '')}", style_value),
            Paragraph("Status:", style_label), Paragraph(data_json.get("status", "-").upper(), style_value)
        ],
        [
            Paragraph("Facility Address:", style_label), Paragraph(data_json.get("address_chinese", "-"), style_value),
            "", ""
        ]
    ]

    t_meta = Table(meta_table_data, colWidths=[35 * mm, 55 * mm, 35 * mm, 55 * mm])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (1, 3), (3, 3)),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("1. INSPECTION SPECIFICATIONS & REQS (ТЗ)", style_title))
    story.append(Spacer(1, 1 * mm))
    tz_text = data_json.get("requirements", {}).get("notes", "Спецификации не указаны.")
    story.append(Paragraph(tz_text, style_body))
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("2. QUALITY AUDIT CHECKLIST (ISO 2859-1 STANDARD)", style_title))
    story.append(Spacer(1, 2 * mm))

    checklist = data_json.get("checklist", [])
    chk_table_data = [[
        Paragraph("<b>Status</b>", style_label),
        Paragraph("<b>Control Parameter / Description</b>", style_label)
    ]]

    for item in checklist:
        status_code = "[ PASS ]" if item.get("passed") else "[ FAIL ]"
        status_color = "#16A34A" if item.get("passed") else "#DC2626"
        
        style_chk_status = ParagraphStyle(
            'ChkStatus', parent=style_label,
            fontName=FONT_BOLD, textColor=colors.HexColor(status_color)
        )
        chk_table_data.append([
            Paragraph(status_code, style_chk_status),
            Paragraph(item.get("task", ""), style_body)
        ])

    t_chk = Table(chk_table_data, colWidths=[25 * mm, 155 * mm])
    t_chk.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_chk)
    story.append(Spacer(1, 8 * mm))

    verdict_status = data_json.get("status", "").lower()
    is_pass = "completed" in verdict_status or "pass" in verdict_status
    verdict_text = "PASSED / APPROVED FOR SHIPMENT" if is_pass else "FAILED / ISSUES DETECTED"
    bg_color = colors.HexColor("#F0FDF4") if is_pass else colors.HexColor("#FEF2F2")
    border_color = colors.HexColor("#BBF7D0") if is_pass else colors.HexColor("#FECACA")
    text_color = colors.HexColor("#166534") if is_pass else colors.HexColor("#991B1B")

    style_verdict = ParagraphStyle(
        'VerdictText', parent=styles['Normal'],
        fontName=FONT_BOLD, fontSize=10, textColor=text_color
    )

    verdict_box = Table([[
        Paragraph(f"FINAL INSPECTION VERDICT: {verdict_text}", style_verdict)
    ]], colWidths=[130 * mm])

    verdict_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_color),
        ('BOX', (0, 0), (-1, -1), 1, border_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))

    story.append(KeepTogether([verdict_box]))

    def make_canvas(*args, **kwargs):
        return EnterpriseReportCanvas(*args, data_context=data_json, **kwargs)

    doc.build(story, canvasmaker=make_canvas)
