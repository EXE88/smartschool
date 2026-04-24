from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from basemodels.models import Classes, Grades, Lessons, Students, Subjects, Teachers
from students.models import Student
from teachers.models import Teacher, TeachingAssignment

from .models import Score


class ScoreModelTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()

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
        self.lesson = Lessons.objects.create(
            name="Geometry",
            grade=self.grade,
            subject=self.subject,
        )

        self.teachers_list = Teachers.objects.create()
        self.students_list = Students.objects.create()

        self.teacher_user = self.user_model.objects.create_user(
            username="score-teacher",
            password="pass",
        )
        self.student_user = self.user_model.objects.create_user(
            username="score-student-1",
            password="pass",
        )
        self.other_student_user = self.user_model.objects.create_user(
            username="score-student-2",
            password="pass",
        )

        self.teachers_list.teachers.add(self.teacher_user)
        self.students_list.students.add(self.student_user, self.other_student_user)

        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            firstname="Teacher",
            lastname="Score",
            birthdate="1990-01-01",
            nationalcode="4444444444",
            phonenumber="09125555555",
        )
        self.student = Student.objects.create(
            user=self.student_user,
            firstname="Student",
            lastname="ScoreOne",
            birthdate="2010-01-01",
            nationalcode="5555555555",
            father_phonenumber="09126666666",
            mother_phonenumber="09127777777",
            home_phonenumber="02112312312",
            subject=self.subject,
            grade=self.grade,
            classobj=self.class_1,
        )
        self.other_student = Student.objects.create(
            user=self.other_student_user,
            firstname="Student",
            lastname="ScoreTwo",
            birthdate="2010-01-02",
            nationalcode="6666666666",
            father_phonenumber="09128888888",
            mother_phonenumber="09129999999",
            home_phonenumber="02132132132",
            subject=self.subject,
            grade=self.grade,
            classobj=self.class_2,
        )
        self.assignment = TeachingAssignment.objects.create(
            user=self.teacher,
            classobj=self.class_1,
            lesson=self.lesson,
        )

    def test_score_can_be_created_for_student_in_teacher_class(self):
        score = Score.objects.create(
            teacher_assignment=self.assignment,
            student=self.student,
            score_date=date(2026, 4, 24),
            value=Decimal("18.50"),
        )

        self.assertEqual(Score.objects.count(), 1)
        self.assertEqual(score.teacher, self.teacher)
        self.assertEqual(score.lesson, self.lesson)

    def test_score_rejects_student_outside_assignment_class(self):
        score = Score(
            teacher_assignment=self.assignment,
            student=self.other_student,
            score_date=date(2026, 4, 24),
            value=Decimal("17.00"),
        )

        with self.assertRaises(ValidationError) as error:
            score.full_clean()

        self.assertIn("student", error.exception.message_dict)

    def test_score_rejects_future_date(self):
        score = Score(
            teacher_assignment=self.assignment,
            student=self.student,
            score_date=timezone.localdate() + timedelta(days=1),
            value=Decimal("16.00"),
        )

        with self.assertRaises(ValidationError) as error:
            score.full_clean()

        self.assertIn("score_date", error.exception.message_dict)

    def test_score_rejects_value_above_allowed_range(self):
        score = Score(
            teacher_assignment=self.assignment,
            student=self.student,
            score_date=date(2026, 4, 24),
            value=Decimal("20.50"),
        )

        with self.assertRaises(ValidationError) as error:
            score.full_clean()

        self.assertIn("value", error.exception.message_dict)
