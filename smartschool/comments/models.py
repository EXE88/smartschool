from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.db import models
from django.utils import timezone

from students.models import Student
from teachers.models import Teacher, TeachingAssignment


class TeacherComment(models.Model):
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="sent_comments",
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="received_comments",
    )
    message = models.TextField(
        validators=[MaxLengthValidator(1000)],
        help_text="Maximum 1000 characters.",
    )
    checked = models.BooleanField(default=False, db_index=True)
    checked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["teacher", "student", "checked"]),
            models.Index(fields=["student", "checked", "created_at"]),
        ]

    def __str__(self):
        return f"{self.teacher} -> {self.student} | {self.message_preview}"

    @property
    def message_preview(self):
        normalized = (self.message or "").strip()
        if len(normalized) <= 60:
            return normalized
        return f"{normalized[:57]}..."

    def clean(self):
        super().clean()

        if self.message is not None:
            self.message = self.message.strip()

        if not self.message:
            raise ValidationError({"message": "Message cannot be empty."})

        if not self.teacher_id or not self.student_id:
            return

        if not TeachingAssignment.objects.filter(
            user_id=self.teacher_id,
            classobj_id=self.student.classobj_id,
        ).exists():
            raise ValidationError(
                {
                    "student": (
                        "Selected teacher is not assigned to the student's class."
                    )
                }
            )

    def save(self, *args, **kwargs):
        if self.checked:
            if self.checked_at is None:
                self.checked_at = timezone.now()
        else:
            self.checked_at = None

        self.full_clean()
        return super().save(*args, **kwargs)

