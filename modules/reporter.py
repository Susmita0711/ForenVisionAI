import os
from datetime import datetime
from io import BytesIO
from typing import Dict, Any

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    REPORTLAB_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency fallback
    colors = None
    letter = None
    getSampleStyleSheet = None
    Paragraph = None
    SimpleDocTemplate = None
    Spacer = None
    Table = None
    TableStyle = None
    REPORTLAB_AVAILABLE = False


def generate_pdf(case_data: Dict[str, Any], output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if not REPORTLAB_AVAILABLE:
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(f"ForenVision-AI Case Report\nCase Number: {case_data.get('case_number', 'N/A')}\n")
            handle.write(f"Title: {case_data.get('title', 'N/A')}\n")
            handle.write(f"Summary: {case_data.get('summary', 'N/A')}\n")
        return output_path

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=case_data.get("title", "ForenVision-AI Case"))
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("ForenVision-AI Case Report", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Case Number: {case_data.get('case_number', 'N/A')}", styles["Heading2"]))
    story.append(Paragraph(f"Title: {case_data.get('title', 'N/A')}", styles["BodyText"]))
    story.append(Paragraph(f"Category: {case_data.get('category', 'N/A')}", styles["BodyText"]))
    story.append(Paragraph(f"Status: {case_data.get('status', 'N/A')}", styles["BodyText"]))
    story.append(Paragraph(f"Created At: {case_data.get('created_at', datetime.utcnow().isoformat())}", styles["BodyText"]))
    story.append(Spacer(1, 12))

    summary = case_data.get("summary") or "No summary available."
    story.append(Paragraph("Summary", styles["Heading2"]))
    story.append(Paragraph(summary, styles["BodyText"]))
    story.append(Spacer(1, 12))

    table_data = [
        ["Attribute", "Value"],
        ["Evidence Path", case_data.get("evidence_path") or "N/A"],
        ["Fingerprint Score", str(case_data.get("fingerprint_score", "N/A"))],
        ["Sketch Profile", str(case_data.get("sketch_profile") or "N/A")],
    ]
    table = Table(table_data, colWidths=[140, 360])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("padding", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    with open(output_path, "wb") as handle:
        handle.write(buffer.getvalue())
    return output_path
