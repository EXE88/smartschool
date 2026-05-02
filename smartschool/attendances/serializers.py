from rest_framework import serializers

from smartschool.api_utils import FullCleanModelSerializer

from .models import Attendance


class AttendanceSerializer(FullCleanModelSerializer):
    teacher_name = serializers.CharField(
        source="teacher_assignment.user",
        read_only=True,
    )
    student_name = serializers.CharField(source="student", read_only=True)
    class_name = serializers.CharField(
        source="teacher_assignment.classobj.name",
        read_only=True,
    )
    lesson_name = serializers.CharField(
        source="teacher_assignment.lesson.name",
        read_only=True,
    )

    class Meta:
        model = Attendance
        fields = (
            "id",
            "teacher_assignment",
            "student",
            "teacher_name",
            "student_name",
            "class_name",
            "lesson_name",
            "created_at",
        )
        read_only_fields = (
            "id",
            "teacher_name",
            "student_name",
            "class_name",
            "lesson_name",
            "created_at",
        )

