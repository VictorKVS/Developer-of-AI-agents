# Generated manually for the educational project.

import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Conversation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "public_id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("new", "New"),
                            ("active", "Active"),
                            ("analyzing", "Analyzing"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        db_index=True,
                        default="new",
                        max_length=20,
                    ),
                ),
                (
                    "session_key",
                    models.CharField(blank=True, db_index=True, max_length=64),
                ),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("user", "User"),
                            ("assistant", "Assistant"),
                            ("system", "System"),
                        ],
                        max_length=20,
                    ),
                ),
                ("content", models.TextField()),
                ("sequence_number", models.PositiveIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "conversation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="conversations.conversation",
                    ),
                ),
            ],
            options={"ordering": ["sequence_number"]},
        ),
        migrations.AddConstraint(
            model_name="message",
            constraint=models.UniqueConstraint(
                fields=("conversation", "sequence_number"),
                name="unique_message_sequence_per_conversation",
            ),
        ),
    ]
