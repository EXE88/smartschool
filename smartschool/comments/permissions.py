from rest_framework import permissions

from smartschool.api_utils import get_student_profile, get_teacher_profile


class TeacherCommentPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if view.action in {"create", "update", "destroy"}:
            return request.user.is_staff or get_teacher_profile(request.user) is not None
        if view.action == "partial_update":
            return (
                request.user.is_staff
                or get_teacher_profile(request.user) is not None
                or get_student_profile(request.user) is not None
            )
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        teacher = get_teacher_profile(request.user)
        if teacher and obj.teacher_id == teacher.id:
            return True

        student = get_student_profile(request.user)
        if student and obj.student_id == student.id:
            if request.method in permissions.SAFE_METHODS:
                return True
            return (
                view.action == "partial_update"
                and set(request.data.keys()).issubset({"checked"})
            )

        return False
