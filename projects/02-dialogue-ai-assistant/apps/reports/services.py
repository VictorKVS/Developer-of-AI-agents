import hashlib

from django.core.files.base import ContentFile

from .models import GeneratedReport
from .renderers import ReportLabPdfRenderer, ReportRenderer


def build_report_renderer() -> ReportRenderer:
    """Return the configured report renderer.

    ReportLab is the default cross-platform renderer for local Windows,
    Docker, Linux and CI environments. Additional renderers can be added
    later without changing the analysis pipeline.
    """

    return ReportLabPdfRenderer()


def generate_pdf_report(conversation, analysis):
    renderer = build_report_renderer()
    pdf_bytes = renderer.render(conversation=conversation, analysis=analysis)
    checksum = hashlib.sha256(pdf_bytes).hexdigest()
    filename = f"mongoose-dialogue-{conversation.public_id}.{renderer.extension}"

    report, _ = GeneratedReport.objects.get_or_create(
        conversation=conversation,
        defaults={"checksum": checksum},
    )
    report.checksum = checksum
    report.file.save(filename, ContentFile(pdf_bytes), save=False)
    report.save()
    return report
