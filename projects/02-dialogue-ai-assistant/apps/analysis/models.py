from django.db import models

from apps.conversations.models import Conversation


class UserAnalysis(models.Model):
    conversation = models.OneToOneField(
        Conversation,
        on_delete=models.CASCADE,
        related_name="analysis",
    )
    structured_data = models.JSONField(default=dict)
    summary = models.TextField(blank=True)
    recommendations = models.JSONField(default=list)
    confidence = models.FloatField(default=0.0)
    missing_information = models.JSONField(default=list)
    model_name = models.CharField(max_length=120)
    prompt_version = models.CharField(max_length=50, default="v1")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Analysis for {self.conversation.public_id}"
