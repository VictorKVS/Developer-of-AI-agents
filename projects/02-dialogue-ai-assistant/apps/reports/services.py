import hashlib
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML

from .models import GeneratedReport


def generate_pdf_report(conversation, analysis):
    html = render_to_string(
        "reports/dialogue_report.html",
        {
            "brand_name": settings.REPORT_BRAND_NAME,
            "conversation": conversation,
            "analysis": analysis,
            "generated_at": timezone.localtime(),
        },
    )
    pdf_bytes = HTML(
        string=html,
        base_url=str(Path(settings.BASE_DIR)),
    ).write_pdf()
    checksum = hashlib.sha256(pdf_bytes).hexdigest()
    filename = f"mongoose-dialogue-{conversation.public_id}.pdf"

    report, _ = GeneratedReport.objects.get_or_create(
        conversation=conversation,
        defaults={"checksum": checksum},
    )
    report.checksum = checksum
    report.file.save(filename, ContentFile(pdf_bytes), save=False)
    report.save()
    return report
