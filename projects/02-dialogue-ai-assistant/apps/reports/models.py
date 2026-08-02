from django.db import models

from apps.conversations.models import Conversation


class GeneratedReport(models.Model):
    conversation = models.OneToOneField(
        Conversation,
        on_delete=models.CASCADE,
        related_name="report",
    )
    file = models.FileField(upload_to="reports/%Y/%m/%d/")
    checksum = models.CharField(max_length=64, db_index=True)
    template_version = models.CharField(max_length=50, default="v1")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Report for {self.conversation.public_id}"
