from __future__ import annotations

from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _fonts() -> tuple[str, str]:
    candidates = [
        (Path("C:/Windows/Fonts/arial.ttf"), Path("C:/Windows/Fonts/arialbd.ttf")),
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
        (
            Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
        ),
    ]
    for regular, bold in candidates:
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont("CareerRegular", str(regular)))
            pdfmetrics.registerFont(TTFont("CareerBold", str(bold)))
            return "CareerRegular", "CareerBold"
    return "Helvetica", "Helvetica-Bold"


def _safe(value) -> str:
    return (
        str(value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_career_track_pdf(*, result: dict, model_name: str, document_name: str) -> bytes:
    regular, bold = _fonts()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title="MONGOOSE AI Career Track Report",
        author=settings.REPORT_BRAND_NAME,
    )
    base = getSampleStyleSheet()
    styles = {
        "brand": ParagraphStyle(
            "CareerBrand",
            parent=base["Normal"],
            fontName=bold,
            fontSize=10,
            textColor=colors.HexColor("#18B981"),
            alignment=TA_CENTER,
            spaceAfter=5,
        ),
        "title": ParagraphStyle(
            "CareerTitle",
            parent=base["Title"],
            fontName=bold,
            fontSize=23,
            leading=28,
            textColor=colors.HexColor("#172033"),
            alignment=TA_CENTER,
        ),
        "heading": ParagraphStyle(
            "CareerHeading",
            parent=base["Heading2"],
            fontName=bold,
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#172033"),
            spaceBefore=10,
            spaceAfter=6,
        ),
        "subheading": ParagraphStyle(
            "CareerSubheading",
            parent=base["Heading3"],
            fontName=bold,
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#334155"),
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "CareerBody",
            parent=base["BodyText"],
            fontName=regular,
            fontSize=10,
            leading=15,
            textColor=colors.HexColor("#334155"),
        ),
        "small": ParagraphStyle(
            "CareerSmall",
            parent=base["BodyText"],
            fontName=regular,
            fontSize=8,
            leading=12,
            textColor=colors.HexColor("#64748B"),
        ),
    }

    story = [
        Paragraph(settings.REPORT_BRAND_NAME, styles["brand"]),
        Paragraph("Professional Career Assessment", styles["title"]),
        Spacer(1, 5 * mm),
    ]
    meta = [
        ["Дата", timezone.localtime().strftime("%d.%m.%Y %H:%M")],
        ["Документ", document_name or "Загруженное резюме"],
        ["Целевая роль", result.get("target_role", "Не указана")],
        ["Модель", model_name or "Не указана"],
        ["Готовность", f"{result.get('readiness_percent', 0)}%"],
    ]
    story.append(
        Table(
            meta,
            colWidths=[42 * mm, 121 * mm],
            style=TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), regular),
                    ("FONTNAME", (0, 0), (0, -1), bold),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#5B7CFA")),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F7FF")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9E2FF")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5EAFA")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            ),
        )
    )
    story.append(Spacer(1, 7 * mm))

    def section(title: str) -> None:
        story.append(Paragraph(title, styles["heading"]))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#D9E2FF")))
        story.append(Spacer(1, 3 * mm))

    def list_items(items: list[str], empty: str = "Не указано") -> None:
        if items:
            for item in items:
                story.append(Paragraph(f"• {_safe(item)}", styles["body"]))
        else:
            story.append(Paragraph(empty, styles["body"]))
        story.append(Spacer(1, 3 * mm))

    section("Executive Summary")
    story.append(Paragraph(_safe(result.get("profile_summary")), styles["body"]))

    section("Сильные стороны")
    list_items(result.get("strengths", []))

    section("Переносимые компетенции")
    list_items(result.get("transferable_skills", []))

    section("Критические пробелы")
    list_items(result.get("critical_gaps", []))

    section("Рекомендуемые проекты")
    list_items(result.get("recommended_projects", []))

    section("Персональный трек развития")
    for index, step in enumerate(result.get("track", []), start=1):
        order = step.get("order") or index
        story.append(Paragraph(f"{order}. {_safe(step.get('title'))}", styles["subheading"]))
        story.append(Paragraph(_safe(step.get("purpose")), styles["body"]))
        story.append(
            Paragraph(
                f"Проверяемый результат: {_safe(step.get('deliverable'))}",
                styles["body"],
            )
        )
        story.append(Spacer(1, 3 * mm))

    section("Следующая контрольная точка")
    story.append(Paragraph(_safe(result.get("next_checkpoint")), styles["body"]))

    missing = result.get("missing_information", [])
    if missing:
        section("Недостающая информация")
        list_items(missing)

    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#CBD5E1")))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(_safe(result.get("disclaimer")), styles["small"]))
    story.append(
        Paragraph(
            "Generated by MONGOOSE AI PLATFORM · Enterprise AI Workspace · v0.1",
            styles["small"],
        )
    )

    def draw_page(canvas, document) -> None:
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#172033"))
        canvas.rect(0, A4[1] - 7 * mm, A4[0], 7 * mm, fill=1, stroke=0)
        canvas.setFont(regular, 8)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Страница {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    return buffer.getvalue()
