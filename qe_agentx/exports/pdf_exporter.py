"""Export release-traceable test cases as a PDF report."""

from __future__ import annotations

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class PdfExporter:
    def export(self, state: dict) -> bytes:
        release = state.get("release_traceability") or {}
        styles = getSampleStyleSheet()
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer, pagesize=A4, rightMargin=16 * mm, leftMargin=16 * mm,
            topMargin=14 * mm, bottomMargin=14 * mm,
        )
        content = [Paragraph("Release Information", styles["Title"]), Spacer(1, 4 * mm)]
        fields = [
            ("Jira Key", "jira_key"), ("Jira Type", "jira_type"),
            ("Sprint", "sprint"), ("Sprint Status", "sprint_status"),
            ("CW Release", "cw_release"), ("FA Release Version", "fa_release_version"),
            ("Fix Version", "fix_version"), ("Planned Release Date", "planned_release_date"),
            ("Environment", "environment"),
        ]
        table = Table(
            [
                [
                    Paragraph(escape(label), styles["BodyText"]),
                    Paragraph(escape(str(release.get(key, ""))), styles["BodyText"]),
                ]
                for label, key in fields
            ],
            colWidths=[48 * mm, 122 * mm],
        )
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F5F5F5")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        content.extend([table, Spacer(1, 6 * mm)])
        if release.get("availability_message"):
            content.extend([Paragraph(escape(release["availability_message"]), styles["BodyText"]), Spacer(1, 4 * mm)])

        content.append(Paragraph("Test Cases", styles["Heading1"]))
        cycle = state.get("test_cycle") or {}
        executions = {
            item.get("tc_id"): item for item in (cycle.get("executions") or [])
        }
        trace = (
            f"Sprint: {release.get('sprint', '')} | CW Release: {release.get('cw_release', '')} | "
            f"FA Release: {release.get('fa_release_version', '')}"
        )
        for test_case in state.get("test_cases") or []:
            execution = executions.get(test_case.get("tc_id"), {})
            content.extend([
                Paragraph(
                    escape(f"{test_case.get('tc_id', '')} - {test_case.get('title', '')}"),
                    styles["Heading2"],
                ),
                Paragraph(escape(trace), styles["BodyText"]),
                Paragraph(
                    escape(
                        f"Status: {execution.get('status', 'NOT_EXECUTED')} | "
                        f"Comments: {execution.get('execution_comments', '') or 'None'}"
                    ),
                    styles["BodyText"],
                ),
                Paragraph(
                    escape(
                        "Evidence: "
                        + (", ".join(item.get("filename", "") for item in execution.get("evidence", [])) or "None")
                    ),
                    styles["BodyText"],
                ),
                Spacer(1, 3 * mm),
            ])
        readiness = cycle.get("readiness_summary") or {}
        content.extend([
            Paragraph("Release Readiness Summary", styles["Heading1"]),
            Paragraph(
                escape(
                    f"Risk: {readiness.get('risk_assessment', '')} | "
                    f"Recommendation: {readiness.get('release_recommendation', 'NOT READY')}"
                ),
                styles["BodyText"],
            ),
        ])
        document.build(content)
        return buffer.getvalue()
