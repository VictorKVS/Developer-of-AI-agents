from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("conversations", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="GeneratedReport",
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
                ("file", models.FileField(upload_to="reports/%Y/%m/%d/")),
                ("checksum", models.CharField(db_index=True, max_length=64)),
                ("template_version", models.CharField(default="v1", max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "conversation",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="report",
                        to="conversations.conversation",
                    ),
                ),
            ],
        ),
    ]
