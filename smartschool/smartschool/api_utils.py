from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from students.models import Student
from teachers.models import Teacher


def get_teacher_profile(user):
    if not user or not user.is_authenticated:
        return None
    return Teacher.objects.filter(user=user).first()


def get_student_profile(user):
    if not user or not user.is_authenticated:
        return None
    return Student.objects.filter(user=user).first()


def format_person(person):
    if not person:
        return ""
    return str(person)


def raise_drf_validation_error(exc):
    if hasattr(exc, "message_dict"):
        raise serializers.ValidationError(exc.message_dict)
    if hasattr(exc, "messages"):
        raise serializers.ValidationError(exc.messages)
    raise serializers.ValidationError(str(exc))


class FullCleanModelSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)
