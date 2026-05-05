from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from smartschool.api_utils import get_student_profile, get_teacher_profile

from .models import Attendance
from .permissions import AttendancePermission
from .serializers import AttendanceSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List attendances",
        description="Returns attendance records visible to the current user. Staff users see all records, teachers see records for their own assignments, and students see only their own records.",
        parameters=[
            OpenApiParameter("student", int, OpenApiParameter.QUERY),
            OpenApiParameter("teacher_assignment", int, OpenApiParameter.QUERY),
            OpenApiParameter("status", str, OpenApiParameter.QUERY),
        ],
        tags=["attendances"],
    ),
    create=extend_schema(
        summary="Create attendance",
        description="Creates an attendance record with status=present or status=absent. Teachers can create records only for their own teaching assignments.",
        tags=["attendances"],
    ),
    retrieve=extend_schema(summary="Retrieve attendance", tags=["attendances"]),
    update=extend_schema(summary="Update attendance", tags=["attendances"]),
    partial_update=extend_schema(summary="Partially update attendance", tags=["attendances"]),
    destroy=extend_schema(summary="Delete attendance", tags=["attendances"]),
)
class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = (IsAuthenticated, AttendancePermission)

    def get_queryset(self):
        queryset = Attendance.objects.select_related(
            "teacher_assignment",
            "teacher_assignment__user",
            "teacher_assignment__classobj",
            "teacher_assignment__lesson",
            "student",
            "student__classobj",
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

        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

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


