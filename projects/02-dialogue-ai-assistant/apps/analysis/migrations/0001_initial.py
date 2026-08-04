from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("conversations", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserAnalysis",
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
                ("structured_data", models.JSONField(default=dict)),
                ("summary", models.TextField(blank=True)),
                ("recommendations", models.JSONField(default=list)),
                ("confidence", models.FloatField(default=0.0)),
                ("missing_information", models.JSONField(default=list)),
                ("model_name", models.CharField(max_length=120)),
                ("prompt_version", models.CharField(default="v1", max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "conversation",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="analysis",
                        to="conversations.conversation",
                    ),
                ),
            ],
        ),
    ]
