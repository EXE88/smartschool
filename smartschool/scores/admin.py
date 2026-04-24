from django.contrib import admin

from .models import Score


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "teacher_name",
        "student",
        "lesson_name",
        "value",
        "created_at",
    )
    list_filter = (
        "created_at",
        "teacher_assignment__classobj",
        "teacher_assignment__lesson",
    )
    search_fields = (
        "student__firstname",
        "student__lastname",
        "student__nationalcode",
        "teacher_assignment__user__firstname",
        "teacher_assignment__user__lastname",
        "teacher_assignment__lesson__name",
        "teacher_assignment__classobj__name",
    )
    autocomplete_fields = ("teacher_assignment", "student")
    list_select_related = (
        "teacher_assignment",
        "teacher_assignment__user",
        "teacher_assignment__lesson",
        "teacher_assignment__classobj",
        "student",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)

    @admin.display(ordering="teacher_assignment__user__lastname", description="Teacher")
    def teacher_name(self, obj):
        return obj.teacher

    @admin.display(ordering="teacher_assignment__lesson__name", description="Lesson")
    def lesson_name(self, obj):
        return obj.lesson
