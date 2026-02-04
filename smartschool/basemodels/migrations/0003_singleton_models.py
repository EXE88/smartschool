from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("basemodels", "0002_lessons"),
    ]

    operations = [
        migrations.AddField(
            model_name="teachers",
            name="singleton_id",
            field=models.PositiveSmallIntegerField(default=1, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name="students",
            name="singleton_id",
            field=models.PositiveSmallIntegerField(default=1, editable=False, unique=True),
        ),
    ]
