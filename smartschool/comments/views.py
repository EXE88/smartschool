from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from smartschool.api_utils import get_student_profile, get_teacher_profile

from .models import TeacherComment
from .permissions import TeacherCommentPermission
from .serializers import TeacherCommentSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List teacher comments",
        description="Returns teacher comments visible to the current user. Staff users see all comments, teachers see sent comments, and students see received comments.",
        parameters=[
            OpenApiParameter("teacher", int, OpenApiParameter.QUERY),
            OpenApiParameter("student", int, OpenApiParameter.QUERY),
            OpenApiParameter("checked", bool, OpenApiParameter.QUERY),
        ],
        tags=["comments"],
    ),
    create=extend_schema(
        summary="Create teacher comment",
        description="Creates a teacher comment for a student. Teachers are automatically set as the sender; staff users can select the teacher explicitly.",
        tags=["comments"],
    ),
    retrieve=extend_schema(summary="Retrieve teacher comment", tags=["comments"]),
    update=extend_schema(summary="Update teacher comment", tags=["comments"]),
    partial_update=extend_schema(
        summary="Partially update teacher comment",
        description="Teachers can update their own comments. Students can only PATCH the checked field on comments addressed to them.",
        tags=["comments"],
    ),
    destroy=extend_schema(summary="Delete teacher comment", tags=["comments"]),
)
class TeacherCommentViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherCommentSerializer
    permission_classes = (IsAuthenticated, TeacherCommentPermission)

    def get_queryset(self):
        queryset = TeacherComment.objects.select_related(
            "teacher",
            "teacher__user",
            "student",
            "student__user",
            "student__classobj",
            "student__grade",
            "student__subject",
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
                queryset = queryset.filter(student=student)
            else:
                queryset = queryset.none()

        teacher_id = self.request.query_params.get("teacher")
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)

        student_id = self.request.query_params.get("student")
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        checked = self.request.query_params.get("checked")
        if checked is not None:
            queryset = queryset.filter(checked=str(checked).lower() in {"1", "true", "yes"})

        return queryset

    def perform_create(self, serializer):
        teacher = get_teacher_profile(self.request.user)
        if self.request.user.is_staff:
            serializer.save()
        else:
            serializer.save(teacher=teacher)

    def perform_update(self, serializer):
        student = get_student_profile(self.request.user)
        teacher = get_teacher_profile(self.request.user)

        if student and not self.request.user.is_staff and not teacher:
            if set(self.request.data.keys()) - {"checked"}:
                raise PermissionDenied("Students can only update the checked field.")
            serializer.save()
            return

        if self.request.user.is_staff:
            serializer.save()
        else:
            serializer.save(teacher=teacher)

