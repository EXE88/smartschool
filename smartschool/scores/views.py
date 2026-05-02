from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from smartschool.api_utils import get_student_profile, get_teacher_profile

from .models import Score
from .permissions import ScorePermission
from .serializers import ScoreSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List scores",
        description="Returns scores visible to the current user. Staff users see all scores, teachers see scores for their own teaching assignments, and students see only their own scores.",
        parameters=[
            OpenApiParameter("student", int, OpenApiParameter.QUERY),
            OpenApiParameter("teacher_assignment", int, OpenApiParameter.QUERY),
        ],
        tags=["scores"],
    ),
    create=extend_schema(
        summary="Create score",
        description="Creates a score. Staff users can create any valid score; teachers can create scores only for their own teaching assignments.",
        tags=["scores"],
    ),
    retrieve=extend_schema(summary="Retrieve score", tags=["scores"]),
    update=extend_schema(summary="Update score", tags=["scores"]),
    partial_update=extend_schema(summary="Partially update score", tags=["scores"]),
    destroy=extend_schema(summary="Delete score", tags=["scores"]),
)
class ScoreViewSet(viewsets.ModelViewSet):
    serializer_class = ScoreSerializer
    permission_classes = (IsAuthenticated, ScorePermission)

    def get_queryset(self):
        queryset = Score.objects.select_related(
            "teacher_assignment",
            "teacher_assignment__user",
            "teacher_assignment__lesson",
            "teacher_assignment__classobj",
            "student",
        )
        user = self.request.user

        if user.is_staff:
            pass
        else:
            teacher = get_teacher_profile(user)
            student = get_student_profile(user)
            if teacher:
                queryset = queryset.filter(teacher_assignment__user=teacher)
            elif student:
                queryset = queryset.filter(student=student)
            else:
                queryset = queryset.none()

        student_id = self.request.query_params.get("student")
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        assignment_id = self.request.query_params.get("teacher_assignment")
        if assignment_id:
            queryset = queryset.filter(teacher_assignment_id=assignment_id)

        return queryset

    def _ensure_teacher_can_use_assignment(self, serializer):
        if self.request.user.is_staff:
            return

        teacher = get_teacher_profile(self.request.user)
        assignment = serializer.validated_data.get("teacher_assignment")
        if assignment is None and serializer.instance is not None:
            assignment = serializer.instance.teacher_assignment
        if not teacher or not assignment or assignment.user_id != teacher.id:
            raise PermissionDenied("You cannot use this teaching assignment.")

    def perform_create(self, serializer):
        self._ensure_teacher_can_use_assignment(serializer)
        serializer.save()

    def perform_update(self, serializer):
        self._ensure_teacher_can_use_assignment(serializer)
        serializer.save()
