from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from smartschool.api_utils import get_student_profile, get_teacher_profile

from .models import Homework
from .permissions import HomeworkPermission
from .serializers import HomeworkSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List homeworks",
        description="Returns homeworks visible to the current user. Staff users see all homeworks, teachers see their own homeworks, and students see homeworks for their class.",
        parameters=[
            OpenApiParameter("classobj", int, OpenApiParameter.QUERY),
            OpenApiParameter("lesson", int, OpenApiParameter.QUERY),
            OpenApiParameter("teacher", int, OpenApiParameter.QUERY),
        ],
        tags=["homeworks"],
    ),
    create=extend_schema(
        summary="Create homework",
        description="Creates a homework. Teachers automatically create it as themselves; staff users can select the teacher explicitly.",
        tags=["homeworks"],
    ),
    retrieve=extend_schema(summary="Retrieve homework", tags=["homeworks"]),
    update=extend_schema(summary="Update homework", tags=["homeworks"]),
    partial_update=extend_schema(summary="Partially update homework", tags=["homeworks"]),
    destroy=extend_schema(summary="Delete homework", tags=["homeworks"]),
)
class HomeworkViewSet(viewsets.ModelViewSet):
    serializer_class = HomeworkSerializer
    permission_classes = (IsAuthenticated, HomeworkPermission)

    def get_queryset(self):
        queryset = Homework.objects.select_related(
            "teacher",
            "teacher__user",
            "classobj",
            "lesson",
        )
        user = self.request.user

        if user.is_staff:
            pass
        else:
            teacher = get_teacher_profile(user)
            student = get_student_profile(user)
            if teacher:
                queryset = queryset.filter(teacher=teacher)
            elif student:
                queryset = queryset.filter(classobj=student.classobj)
            else:
                queryset = queryset.none()

        for field in ("classobj", "lesson", "teacher"):
            value = self.request.query_params.get(field)
            if value:
                queryset = queryset.filter(**{f"{field}_id": value})

        return queryset

    def perform_create(self, serializer):
        teacher = get_teacher_profile(self.request.user)
        if self.request.user.is_staff:
            serializer.save()
        else:
            serializer.save(teacher=teacher)

    def perform_update(self, serializer):
        teacher = get_teacher_profile(self.request.user)
        if self.request.user.is_staff:
            serializer.save()
        else:
            serializer.save(teacher=teacher)
