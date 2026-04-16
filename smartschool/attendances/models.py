from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from students.models import Student
from teachers.models import TeachingAssignment
from weeklyschedules.models import WeeklySchedule


class Attendance(models.Model):
    teacher_assignment = models.ForeignKey(
        TeachingAssignment,
        on_delete=models.CASCADE,
        related_name="attendances",
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attendances",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.student} | {self.teacher_assignment}"

    @staticmethod
    def _weekday_from_date(attendance_date):
        weekday_mapping = {
            5: WeeklySchedule.WeekDay.SATURDAY,
            6: WeeklySchedule.WeekDay.SUNDAY,
            0: WeeklySchedule.WeekDay.MONDAY,
            1: WeeklySchedule.WeekDay.TUESDAY,
            2: WeeklySchedule.WeekDay.WEDNESDAY,
            3: WeeklySchedule.WeekDay.THURSDAY,
            4: WeeklySchedule.WeekDay.FRIDAY,
        }
        return weekday_mapping.get(attendance_date.weekday())

    def _attendance_date(self):
        if not self.created_at:
            return timezone.localdate()

        if timezone.is_aware(self.created_at):
            return timezone.localtime(self.created_at).date()

        return self.created_at.date()

    def _scheduled_period_count(self, weekly_schedule):
        period_assignment_ids = (
            weekly_schedule.period_1_id,
            weekly_schedule.period_2_id,
            weekly_schedule.period_3_id,
            weekly_schedule.period_4_id,
        )
        return sum(
            1
            for assignment_id in period_assignment_ids
            if assignment_id == self.teacher_assignment_id
        )

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

        attendance_date = self._attendance_date()
        weekday = self._weekday_from_date(attendance_date)
        if not weekday:
            raise ValidationError(
                {
                    "created_at": (
                        "Attendance can only be registered on scheduled school days."
                    )
                }
            )

        try:
            weekly_schedule = WeeklySchedule.objects.get(
                classobj_id=self.teacher_assignment.classobj_id,
                weekday=weekday,
            )
        except WeeklySchedule.DoesNotExist:
            raise ValidationError(
                {
                    "teacher_assignment": (
                        "No weekly schedule exists for the selected class on this day."
                    )
                }
            )

        scheduled_period_count = self._scheduled_period_count(weekly_schedule)
        if scheduled_period_count == 0:
            raise ValidationError(
                {
                    "teacher_assignment": (
                        "This lesson is not scheduled for the selected class on this day."
                    )
                }
            )

        existing_attendances = Attendance.objects.filter(
            teacher_assignment_id=self.teacher_assignment_id,
            student_id=self.student_id,
            created_at__date=attendance_date,
        )
        if self.pk:
            existing_attendances = existing_attendances.exclude(pk=self.pk)

        if existing_attendances.count() >= scheduled_period_count:
            raise ValidationError(
                {
                    "teacher_assignment": (
                        "Attendance limit reached for this student on the selected day."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
