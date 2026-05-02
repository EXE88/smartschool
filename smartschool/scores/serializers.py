from rest_framework import serializers

from smartschool.api_utils import FullCleanModelSerializer

from .models import Score


class ScoreSerializer(FullCleanModelSerializer):
    teacher_name = serializers.CharField(source="teacher", read_only=True)
    lesson_name = serializers.CharField(source="lesson", read_only=True)
    student_name = serializers.CharField(source="student", read_only=True)
    class_name = serializers.CharField(
        source="teacher_assignment.classobj.name",
        read_only=True,
    )

    class Meta:
        model = Score
        fields = (
            "id",
            "teacher_assignment",
            "student",
            "value",
            "teacher_name",
            "lesson_name",
            "student_name",
            "class_name",
            "created_at",
        )
        read_only_fields = (
            "id",
            "teacher_name",
            "lesson_name",
            "student_name",
            "class_name",
            "created_at",
        )

