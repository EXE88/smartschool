from rest_framework import serializers

from smartschool.api_utils import FullCleanModelSerializer

from .models import TeacherComment


class TeacherCommentSerializer(FullCleanModelSerializer):
    teacher_name = serializers.CharField(source="teacher", read_only=True)
    student_name = serializers.CharField(source="student", read_only=True)
    student_class = serializers.CharField(source="student.classobj.name", read_only=True)

    class Meta:
        model = TeacherComment
        fields = (
            "id",
            "teacher",
            "student",
            "message",
            "checked",
            "checked_at",
            "teacher_name",
            "student_name",
            "student_class",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "checked_at",
            "teacher_name",
            "student_name",
            "student_class",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {
            "teacher": {"required": False},
        }
