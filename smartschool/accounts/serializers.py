from rest_framework import serializers

from attendances.serializers import AttendanceSerializer
from comments.serializers import TeacherCommentSerializer
from homeworks.serializers import HomeworkSerializer
from scores.serializers import ScoreSerializer


class AccountUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField(allow_blank=True)
    is_staff = serializers.BooleanField()


class AccountProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    firstname = serializers.CharField()
    lastname = serializers.CharField()
    nationalcode = serializers.CharField(required=False)
    role = serializers.CharField()
    classobj = serializers.CharField(required=False)
    grade = serializers.CharField(required=False)
    subject = serializers.CharField(required=False)


class TeachingAssignmentSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    classobj = serializers.CharField()
    lesson = serializers.CharField()
    classobj_id = serializers.IntegerField()
    lesson_id = serializers.IntegerField()
    class_name = serializers.CharField()
    lesson_name = serializers.CharField()


class StudentSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    firstname = serializers.CharField()
    lastname = serializers.CharField()
    classobj = serializers.IntegerField(required=False)
    class_name = serializers.CharField(required=False)
    grade = serializers.CharField(required=False)
    subject = serializers.CharField(required=False)


class AccountDashboardSerializer(serializers.Serializer):
    role = serializers.CharField()
    user = AccountUserSerializer()
    profile = AccountProfileSerializer()
    stats = serializers.DictField()
    teaching_assignments = TeachingAssignmentSummarySerializer(many=True)
    students = StudentSummarySerializer(many=True)
    scores = ScoreSerializer(many=True)
    homeworks = HomeworkSerializer(many=True)
    attendances = AttendanceSerializer(many=True)
    comments = TeacherCommentSerializer(many=True)
