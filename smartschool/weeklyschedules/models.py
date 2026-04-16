from django.core.exceptions import ValidationError
from django.db import models

from basemodels.models import Classes
from teachers.models import TeachingAssignment


class WeeklySchedule(models.Model):
    class WeekDay(models.TextChoices):
        SATURDAY = "saturday", "Saturday"
        SUNDAY = "sunday", "Sunday"
        MONDAY = "monday", "Monday"
        TUESDAY = "tuesday", "Tuesday"
        WEDNESDAY = "wednesday", "Wednesday"
        THURSDAY = "thursday", "Thursday"

    classobj = models.ForeignKey(
        Classes,
        on_delete=models.CASCADE,
        related_name="weekly_schedules",
    )
    weekday = models.CharField(max_length=10, choices=WeekDay.choices)
    period_1 = models.ForeignKey(
        TeachingAssignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="weekly_period_1",
    )
    period_2 = models.ForeignKey(
        TeachingAssignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="weekly_period_2",
    )
    period_3 = models.ForeignKey(
        TeachingAssignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="weekly_period_3",
    )
    period_4 = models.ForeignKey(
        TeachingAssignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="weekly_period_4",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("classobj", "weekday"),
                name="uniq_weekly_schedule_per_class_day",
            ),
        ]
        ordering = ("classobj__name", "weekday")

    def __str__(self):
        return f"{self.classobj} - {self.get_weekday_display()}"

    def _validate_period_assignment(self, field_name, assignment):
        if assignment and assignment.classobj_id != self.classobj_id:
            raise ValidationError(
                {
                    field_name: (
                        "Selected teaching assignment must belong to the selected class."
                    )
                }
            )

    def clean(self):
        super().clean()
        if not self.classobj_id:
            return

        self._validate_period_assignment("period_1", self.period_1)
        self._validate_period_assignment("period_2", self.period_2)
        self._validate_period_assignment("period_3", self.period_3)
        self._validate_period_assignment("period_4", self.period_4)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
