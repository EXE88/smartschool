from rest_framework import serializers

from smartschool.api_utils import FullCleanModelSerializer

from .models import Homework


class HomeworkSerializer(FullCleanModelSerializer):
    teacher_name = serializers.CharField(source="teacher", read_only=True)
    class_name = serializers.CharField(source="classobj.name", read_only=True)
    lesson_name = serializers.CharField(source="lesson.name", read_only=True)

    class Meta:
        model = Homework
        fields = (
            "id",
            "teacher",
            "classobj",
            "lesson",
            "description",
            "due_date",
            "teacher_name",
            "class_name",
            "lesson_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "teacher_name",
            "class_name",
            "lesson_name",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {
            "teacher": {"required": False},
        }
