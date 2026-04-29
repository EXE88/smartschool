from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from basemodels.models import Classes, Lessons
from teachers.models import Teacher, TeachingAssignment


class Homework(models.Model):
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="homeworks",
    )
    classobj = models.ForeignKey(
        Classes,
        on_delete=models.CASCADE,
        related_name="homeworks",
    )
    lesson = models.ForeignKey(
        Lessons,
        on_delete=models.CASCADE,
        related_name="homeworks",
    )
    description = models.TextField()
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.classobj} | {self.lesson} | due {self.due_date}"

    def clean(self):
        super().clean()
        if not (self.teacher_id and self.classobj_id and self.lesson_id):
            return

        if self.due_date and self.due_date < timezone.localdate():
            raise ValidationError({"due_date": "Due date cannot be in the past."})

        assignment_exists = TeachingAssignment.objects.filter(
            user_id=self.teacher_id,
            classobj_id=self.classobj_id,
            lesson_id=self.lesson_id,
        ).exists()
        if not assignment_exists:
            raise ValidationError(
                {
                    "lesson": (
                        "Selected lesson is not assigned to this teacher for the selected class."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
