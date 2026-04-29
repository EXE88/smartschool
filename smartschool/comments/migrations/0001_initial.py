from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("students", "0003_student_created_at"),
        ("teachers", "0003_alter_teachingassignment_user"),
    ]

    operations = [
        migrations.CreateModel(
            name="TeacherComment",
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
                    "message",
                    models.TextField(
                        help_text="Maximum 1000 characters.",
                        validators=[django.core.validators.MaxLengthValidator(1000)],
                    ),
                ),
                ("checked", models.BooleanField(db_index=True, default=False)),
                ("checked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="received_comments",
                        to="students.student",
                    ),
                ),
                (
                    "teacher",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sent_comments",
                        to="teachers.teacher",
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
                "indexes": [
                    models.Index(
                        fields=["teacher", "student", "checked"],
                        name="comments_te_teache_2ef671_idx",
                    ),
                    models.Index(
                        fields=["student", "checked", "created_at"],
                        name="comments_te_student_d32658_idx",
                    ),
                ],
            },
        ),
    ]

