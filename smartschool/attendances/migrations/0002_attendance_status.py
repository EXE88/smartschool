from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("attendances", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="attendance",
            name="status",
            field=models.CharField(
                choices=[("present", "Present"), ("absent", "Absent")],
                default="present",
                max_length=10,
            ),
        ),
    ]
