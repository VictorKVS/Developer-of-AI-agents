import uuid

from django.db import models


class Conversation(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        ACTIVE = "active", "Active"
        ANALYZING = "analyzing", "Analyzing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
    )
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Conversation {self.public_id} ({self.status})"


class Message(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    sequence_number = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sequence_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "sequence_number"],
                name="unique_message_sequence_per_conversation",
            )
        ]

    def __str__(self) -> str:
        return f"{self.role}: {self.content[:60]}"
