from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from students.models import Student
from teachers.models import TeachingAssignment


class Score(models.Model):
    teacher_assignment = models.ForeignKey(
        TeachingAssignment,
        on_delete=models.CASCADE,
        related_name="scores",
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="scores",
    )
    value = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return (
            f"{self.student} | {self.teacher_assignment.lesson} | "
            f"{self.value} | {self.created_at.strftime('%Y-%m-%d')}"
        )

    @property
    def teacher(self):
        return self.teacher_assignment.user

    @property
    def lesson(self):
        return self.teacher_assignment.lesson

    def clean(self):
        super().clean()

        if not self.teacher_assignment_id or not self.student_id:
            return

        if self.student.classobj_id != self.teacher_assignment.classobj_id:
            raise ValidationError(
                {
                    "student": (
                        "Selected student is not in the class assigned to this teacher."
                    )
                }
            )

        if self.student.grade_id != self.teacher_assignment.classobj.grade_id:
            raise ValidationError(
                {"student": "Student grade must match the selected teaching assignment."}
            )

        if self.student.subject_id != self.teacher_assignment.classobj.subject_id:
            raise ValidationError(
                {
                    "student": (
                        "Student subject must match the selected teaching assignment."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
