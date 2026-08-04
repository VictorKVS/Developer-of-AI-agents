from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Protocol

from django.conf import settings
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class ReportRenderer(Protocol):
    extension: str
    content_type: str

    def render(self, *, conversation, analysis) -> bytes:
        """Render an analysis report and return its bytes."""


@dataclass(frozen=True)
class FontSet:
    regular: str
    bold: str


def _register_fonts() -> FontSet:
    candidates = [
        (
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("C:/Windows/Fonts/arialbd.ttf"),
        ),
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
        (
            Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
        ),
    ]

    for regular_path, bold_path in candidates:
        if regular_path.exists() and bold_path.exists():
            pdfmetrics.registerFont(TTFont("MongooseRegular", str(regular_path)))
            pdfmetrics.registerFont(TTFont("MongooseBold", str(bold_path)))
            return FontSet("MongooseRegular", "MongooseBold")

    return FontSet("Helvetica", "Helvetica-Bold")


class ReportLabPdfRenderer:
    extension = "pdf"
    content_type = "application/pdf"

    def __init__(self) -> None:
        self.fonts = _register_fonts()

    def render(self, *, conversation, analysis) -> bytes:
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=20 * mm,
            bottomMargin=18 * mm,
            title=f"MONGOOSE AI report {conversation.public_id}",
            author=settings.REPORT_BRAND_NAME,
        )

        styles = self._build_styles()
        story = []

        story.append(Paragraph(settings.REPORT_BRAND_NAME, styles["brand"]))
        story.append(Paragraph("Dialogue Intelligence Report", styles["title"]))
        story.append(Spacer(1, 5 * mm))
        story.append(
            Table(
                [
                    ["Дата", timezone.localtime().strftime("%d.%m.%Y %H:%M")],
                    ["Диалог", str(conversation.public_id)],
                    ["Модель", analysis.model_name],
                    ["Уверенность", f"{analysis.confidence * 100:.0f}%"],
                ],
                colWidths=[38 * mm, 125 * mm],
                style=TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, -1), self.fonts.regular),
                        ("FONTNAME", (0, 0), (0, -1), self.fonts.bold),
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

        profile = analysis.structured_data or {}
        self._section(story, "Профиль пользователя", styles)
        self._field(story, "Имя", profile.get("name") or "Не указано", styles)
        self._list_field(story, "Цели", profile.get("goals", []), styles)
        self._field(story, "Опыт", profile.get("experience") or "Не указан", styles)
        self._list_field(story, "Интересы", profile.get("interests", []), styles)
        self._list_field(story, "Ограничения", profile.get("constraints", []), styles)

        self._section(story, "Аналитическое резюме", styles)
        story.append(Paragraph(self._safe(analysis.summary), styles["body"]))
        story.append(Spacer(1, 4 * mm))

        self._section(story, "Рекомендации", styles)
        recommendations = analysis.recommendations or []
        if recommendations:
            for index, recommendation in enumerate(recommendations, start=1):
                title = recommendation.get("title", f"Рекомендация {index}")
                reason = recommendation.get("reason", "")
                next_step = recommendation.get("next_step", "")
                story.append(Paragraph(f"{index}. {self._safe(title)}", styles["subheading"]))
                if reason:
                    story.append(Paragraph(f"Почему: {self._safe(reason)}", styles["body"]))
                if next_step:
                    story.append(Paragraph(f"Следующий шаг: {self._safe(next_step)}", styles["body"]))
                story.append(Spacer(1, 3 * mm))
        else:
            story.append(Paragraph("Рекомендации не сформированы.", styles["body"]))

        missing = analysis.missing_information or []
        if missing:
            self._section(story, "Недостающая информация", styles)
            for item in missing:
                story.append(Paragraph(f"• {self._safe(item)}", styles["body"]))

        story.append(Spacer(1, 8 * mm))
        story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#CBD5E1")))
        story.append(Spacer(1, 3 * mm))
        story.append(
            Paragraph(
                "Отчёт создан второй AI-моделью на основе полной истории диалога. "
                "Результат предназначен для информационных целей и может требовать проверки человеком.",
                styles["footer"],
            )
        )

        document.build(story, onFirstPage=self._draw_page, onLaterPages=self._draw_page)
        return buffer.getvalue()

    def _build_styles(self):
        base = getSampleStyleSheet()
        return {
            "brand": ParagraphStyle(
                "Brand",
                parent=base["Normal"],
                fontName=self.fonts.bold,
                fontSize=10,
                leading=12,
                textColor=colors.HexColor("#18B981"),
                alignment=TA_CENTER,
                spaceAfter=5,
            ),
            "title": ParagraphStyle(
                "Title",
                parent=base["Title"],
                fontName=self.fonts.bold,
                fontSize=24,
                leading=29,
                textColor=colors.HexColor("#172033"),
                alignment=TA_CENTER,
            ),
            "heading": ParagraphStyle(
                "Heading",
                parent=base["Heading2"],
                fontName=self.fonts.bold,
                fontSize=15,
                leading=19,
                textColor=colors.HexColor("#172033"),
                spaceBefore=10,
                spaceAfter=7,
            ),
            "subheading": ParagraphStyle(
                "Subheading",
                parent=base["Heading3"],
                fontName=self.fonts.bold,
                fontSize=11,
                leading=15,
                textColor=colors.HexColor("#334155"),
                spaceAfter=3,
            ),
            "body": ParagraphStyle(
                "Body",
                parent=base["BodyText"],
                fontName=self.fonts.regular,
                fontSize=10,
                leading=15,
                textColor=colors.HexColor("#334155"),
                alignment=TA_LEFT,
            ),
            "label": ParagraphStyle(
                "Label",
                parent=base["BodyText"],
                fontName=self.fonts.bold,
                fontSize=10,
                leading=15,
                textColor=colors.HexColor("#5B7CFA"),
            ),
            "footer": ParagraphStyle(
                "Footer",
                parent=base["BodyText"],
                fontName=self.fonts.regular,
                fontSize=8,
                leading=12,
                textColor=colors.HexColor("#64748B"),
            ),
        }

    def _draw_page(self, canvas, document) -> None:
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#172033"))
        canvas.rect(0, A4[1] - 7 * mm, A4[0], 7 * mm, fill=1, stroke=0)
        canvas.setFont(self.fonts.regular, 8)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Страница {document.page}")
        canvas.restoreState()

    @staticmethod
    def _safe(value) -> str:
        return str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _section(self, story, title: str, styles) -> None:
        story.append(Paragraph(title, styles["heading"]))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#D9E2FF")))
        story.append(Spacer(1, 3 * mm))

    def _field(self, story, label: str, value, styles) -> None:
        story.append(Paragraph(label, styles["label"]))
        story.append(Paragraph(self._safe(value), styles["body"]))
        story.append(Spacer(1, 2 * mm))

    def _list_field(self, story, label: str, values, styles) -> None:
        story.append(Paragraph(label, styles["label"]))
        if values:
            for value in values:
                story.append(Paragraph(f"• {self._safe(value)}", styles["body"]))
        else:
            story.append(Paragraph("Не указано", styles["body"]))
        story.append(Spacer(1, 2 * mm))
