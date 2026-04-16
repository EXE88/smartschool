from django.contrib import admin

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("id", "teacher_assignment", "student", "created_at")
    list_filter = ("created_at", "teacher_assignment", "student")
    search_fields = (
        "student__firstname",
        "student__lastname",
        "student__nationalcode",
        "teacher_assignment__user__firstname",
        "teacher_assignment__user__lastname",
        "teacher_assignment__classobj__name",
        "teacher_assignment__lesson__name",
    )
    autocomplete_fields = ("teacher_assignment", "student")
    list_select_related = (
        "teacher_assignment",
        "teacher_assignment__user",
        "teacher_assignment__classobj",
        "teacher_assignment__lesson",
        "student",
        "student__classobj",
    )
    ordering = ("-created_at",)
