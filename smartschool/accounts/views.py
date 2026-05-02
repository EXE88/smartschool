from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from attendances.models import Attendance
from attendances.serializers import AttendanceSerializer
from comments.models import TeacherComment
from comments.serializers import TeacherCommentSerializer
from homeworks.models import Homework
from homeworks.serializers import HomeworkSerializer
from scores.models import Score
from scores.serializers import ScoreSerializer
from smartschool.api_utils import get_student_profile, get_teacher_profile
from students.models import Student
from teachers.models import TeachingAssignment

from .serializers import AccountDashboardSerializer


def _serialize_user(user):
    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_staff": user.is_staff,
    }


def _serialize_teacher_profile(teacher):
    return {
        "id": teacher.id,
        "firstname": teacher.firstname,
        "lastname": teacher.lastname,
        "nationalcode": teacher.nationalcode,
        "role": "teacher",
    }


def _serialize_student_profile(student):
    return {
        "id": student.id,
        "firstname": student.firstname,
        "lastname": student.lastname,
        "nationalcode": student.nationalcode,
        "role": "student",
        "classobj": str(student.classobj),
        "grade": str(student.grade),
        "subject": str(student.subject),
    }


def _serialize_assignments(queryset):
    return [
        {
            "id": assignment.id,
            "classobj": str(assignment.classobj),
            "lesson": str(assignment.lesson),
            "classobj_id": assignment.classobj_id,
            "lesson_id": assignment.lesson_id,
            "class_name": assignment.classobj.name,
            "lesson_name": assignment.lesson.name,
        }
        for assignment in queryset
    ]


def _serialize_students(queryset):
    return [
        {
            "id": student.id,
            "name": str(student),
            "firstname": student.firstname,
            "lastname": student.lastname,
            "classobj": student.classobj_id,
            "class_name": str(student.classobj),
            "grade": str(student.grade),
            "subject": str(student.subject),
        }
        for student in queryset
    ]


class AccountDashboardAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Current account dashboard",
        description="Returns the current user's role, profile, stats, scores, homeworks, attendances, comments, and teacher assignments where applicable. JWT authentication is handled by /api/token/ and /api/token/refresh/.",
        parameters=[
            OpenApiParameter(
                "limit",
                int,
                OpenApiParameter.QUERY,
                description="Maximum records per collection. Default is 200. Use 0 for no limit.",
            )
        ],
        responses=AccountDashboardSerializer,
        tags=["accounts"],
    )
    def get(self, request):
        limit = self._get_limit()
        user = request.user
        teacher = get_teacher_profile(user)
        student = get_student_profile(user)

        if user.is_staff:
            role = "staff"
            profile = {
                "role": "staff",
                "firstname": user.first_name or user.username,
                "lastname": user.last_name or "",
            }
            assignments = TeachingAssignment.objects.select_related("classobj", "lesson")
            scores = Score.objects.select_related("teacher_assignment", "student")
            homeworks = Homework.objects.select_related("teacher", "classobj", "lesson")
            attendances = Attendance.objects.select_related("teacher_assignment", "student")
            comments = TeacherComment.objects.select_related("teacher", "student")
            students = Student.objects.select_related("classobj", "grade", "subject")
        elif teacher:
            role = "teacher"
            profile = _serialize_teacher_profile(teacher)
            assignments = TeachingAssignment.objects.filter(user=teacher).select_related(
                "classobj",
                "lesson",
            )
            scores = Score.objects.filter(teacher_assignment__user=teacher).select_related(
                "teacher_assignment",
                "teacher_assignment__user",
                "teacher_assignment__lesson",
                "teacher_assignment__classobj",
                "student",
            )
            homeworks = Homework.objects.filter(teacher=teacher).select_related(
                "teacher",
                "classobj",
                "lesson",
            )
            attendances = Attendance.objects.filter(
                teacher_assignment__user=teacher
            ).select_related("teacher_assignment", "student")
            comments = TeacherComment.objects.filter(teacher=teacher).select_related(
                "teacher",
                "student",
                "student__classobj",
            )
            students = Student.objects.filter(
                classobj_id__in=assignments.values_list("classobj_id", flat=True)
            ).select_related("classobj", "grade", "subject").distinct()
        elif student:
            role = "student"
            profile = _serialize_student_profile(student)
            assignments = TeachingAssignment.objects.none()
            scores = Score.objects.filter(student=student).select_related(
                "teacher_assignment",
                "teacher_assignment__user",
                "teacher_assignment__lesson",
                "teacher_assignment__classobj",
                "student",
            )
            homeworks = Homework.objects.filter(classobj=student.classobj).select_related(
                "teacher",
                "classobj",
                "lesson",
            )
            attendances = Attendance.objects.filter(student=student).select_related(
                "teacher_assignment",
                "teacher_assignment__user",
                "teacher_assignment__classobj",
                "teacher_assignment__lesson",
                "student",
            )
            comments = TeacherComment.objects.filter(student=student).select_related(
                "teacher",
                "student",
                "student__classobj",
            )
            students = Student.objects.filter(pk=student.pk).select_related(
                "classobj",
                "grade",
                "subject",
            )
        else:
            role = "unknown"
            profile = {
                "role": "unknown",
                "firstname": user.first_name or user.username,
                "lastname": user.last_name or "",
            }
            assignments = TeachingAssignment.objects.none()
            scores = Score.objects.none()
            homeworks = Homework.objects.none()
            attendances = Attendance.objects.none()
            comments = TeacherComment.objects.none()
            students = Student.objects.none()

        payload = {
            "role": role,
            "user": _serialize_user(user),
            "profile": profile,
            "stats": {
                "scores_count": scores.count(),
                "homeworks_count": homeworks.count(),
                "attendances_count": attendances.count(),
                "comments_count": comments.count(),
                "unchecked_comments_count": comments.filter(checked=False).count(),
                "teaching_assignments_count": assignments.count(),
            },
            "teaching_assignments": _serialize_assignments(self._apply_limit(assignments, limit)),
            "students": _serialize_students(students.order_by("lastname", "firstname", "id")),
            "scores": ScoreSerializer(self._apply_limit(scores, limit), many=True).data,
            "homeworks": HomeworkSerializer(self._apply_limit(homeworks, limit), many=True).data,
            "attendances": AttendanceSerializer(
                self._apply_limit(attendances, limit),
                many=True,
            ).data,
            "comments": TeacherCommentSerializer(
                self._apply_limit(comments, limit),
                many=True,
            ).data,
        }
        return Response(payload)

    def _get_limit(self):
        raw_limit = self.request.query_params.get("limit", "200")
        try:
            limit = int(raw_limit)
        except (TypeError, ValueError):
            return 200
        return max(limit, 0)

    @staticmethod
    def _apply_limit(queryset, limit):
        if limit == 0:
            return queryset
        return queryset[:limit]

