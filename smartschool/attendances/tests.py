from datetime import datetime, timezone as datetime_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from basemodels.models import Classes, Grades, Lessons, Students, Subjects, Teachers
from students.models import Student
from teachers.models import Teacher, TeachingAssignment
from weeklyschedules.models import WeeklySchedule

from .models import Attendance


class AttendanceModelTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.fixed_wednesday = datetime(2026, 4, 15, 9, 0, tzinfo=datetime_timezone.utc)

        self.subject = Subjects.objects.create(name="Mathematics")
        self.grade = Grades.objects.create(name="Grade 1")
        self.class_1 = Classes.objects.create(
            name="Class 1",
            subject=self.subject,
            grade=self.grade,
        )
        self.class_2 = Classes.objects.create(
            name="Class 2",
            subject=self.subject,
            grade=self.grade,
        )
        self.english = Lessons.objects.create(
            name="English",
            grade=self.grade,
            subject=self.subject,
        )
        self.science = Lessons.objects.create(
            name="Science",
            grade=self.grade,
            subject=self.subject,
        )

        self.teachers_list = Teachers.objects.create()
        self.students_list = Students.objects.create()

        self.teacher_user = self.user_model.objects.create_user(
            username="teacher-1",
            password="pass",
        )
        self.student_user = self.user_model.objects.create_user(
            username="student-1",
            password="pass",
        )
        self.other_student_user = self.user_model.objects.create_user(
            username="student-2",
            password="pass",
        )

        self.teachers_list.teachers.add(self.teacher_user)
        self.students_list.students.add(self.student_user, self.other_student_user)

        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            firstname="Teacher",
            lastname="One",
            birthdate="1990-01-01",
            nationalcode="1111111111",
            phonenumber="09120000000",
        )
        self.student = Student.objects.create(
            user=self.student_user,
            firstname="Student",
            lastname="One",
            birthdate="2010-01-01",
            nationalcode="2222222222",
            father_phonenumber="09121111111",
            mother_phonenumber="09122222222",
            home_phonenumber="02112345678",
            subject=self.subject,
            grade=self.grade,
            classobj=self.class_1,
        )
        self.other_student = Student.objects.create(
            user=self.other_student_user,
            firstname="Student",
            lastname="Two",
            birthdate="2010-02-02",
            nationalcode="3333333333",
            father_phonenumber="09123333333",
            mother_phonenumber="09124444444",
            home_phonenumber="02187654321",
            subject=self.subject,
            grade=self.grade,
            classobj=self.class_2,
        )

        self.assignment = TeachingAssignment.objects.create(
            user=self.teacher,
            classobj=self.class_1,
            lesson=self.english,
        )
        self.unscheduled_assignment = TeachingAssignment.objects.create(
            user=self.teacher,
            classobj=self.class_1,
            lesson=self.science,
        )

        self.weekly_schedule = WeeklySchedule.objects.create(
            classobj=self.class_1,
            weekday=WeeklySchedule.WeekDay.WEDNESDAY,
            period_1=self.assignment,
            period_2=self.assignment,
        )

    def _save_attendance_at_fixed_time(self, attendance):
        with patch("django.utils.timezone.now", return_value=self.fixed_wednesday):
            attendance.save()

    def _full_clean_at_fixed_time(self, attendance):
        with patch("django.utils.timezone.now", return_value=self.fixed_wednesday):
            attendance.full_clean()

    def test_attendance_can_be_created_for_scheduled_student(self):
        attendance = Attendance(
            teacher_assignment=self.assignment,
            student=self.student,
        )

        self._save_attendance_at_fixed_time(attendance)

        self.assertEqual(Attendance.objects.count(), 1)

    def test_attendance_rejects_student_outside_assignment_class(self):
        attendance = Attendance(
            teacher_assignment=self.assignment,
            student=self.other_student,
        )

        with self.assertRaises(ValidationError) as error:
            self._full_clean_at_fixed_time(attendance)

        self.assertIn("student", error.exception.message_dict)

    def test_attendance_rejects_when_no_weekly_schedule_exists_for_the_day(self):
        self.weekly_schedule.delete()
        attendance = Attendance(
            teacher_assignment=self.assignment,
            student=self.student,
        )

        with self.assertRaises(ValidationError) as error:
            self._full_clean_at_fixed_time(attendance)

        self.assertIn("teacher_assignment", error.exception.message_dict)

    def test_attendance_rejects_when_assignment_is_not_scheduled_that_day(self):
        attendance = Attendance(
            teacher_assignment=self.unscheduled_assignment,
            student=self.student,
        )

        with self.assertRaises(ValidationError) as error:
            self._full_clean_at_fixed_time(attendance)

        self.assertIn("teacher_assignment", error.exception.message_dict)

    def test_attendance_limit_matches_number_of_scheduled_periods(self):
        first_attendance = Attendance(
            teacher_assignment=self.assignment,
            student=self.student,
        )
        second_attendance = Attendance(
            teacher_assignment=self.assignment,
            student=self.student,
        )
        third_attendance = Attendance(
            teacher_assignment=self.assignment,
            student=self.student,
        )

        self._save_attendance_at_fixed_time(first_attendance)
        self._save_attendance_at_fixed_time(second_attendance)

        with self.assertRaises(ValidationError) as error:
            self._save_attendance_at_fixed_time(third_attendance)

        self.assertEqual(Attendance.objects.count(), 2)
        self.assertIn("teacher_assignment", error.exception.message_dict)

    def test_friday_schedule_is_recognized(self):
        friday_schedule = WeeklySchedule.objects.create(
            classobj=self.class_1,
            weekday=WeeklySchedule.WeekDay.FRIDAY,
            period_1=self.assignment,
        )
        attendance = Attendance(
            teacher_assignment=self.assignment,
            student=self.student,
        )
        fixed_friday = datetime(2026, 4, 17, 9, 0, tzinfo=datetime_timezone.utc)

        with patch("django.utils.timezone.now", return_value=fixed_friday):
            attendance.full_clean()

        self.assertEqual(friday_schedule.weekday, WeeklySchedule.WeekDay.FRIDAY)
