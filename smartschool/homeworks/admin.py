from django.contrib import admin

from .models import Homework


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "teacher",
        "classobj",
        "lesson",
        "due_date",
        "created_at",
    )
    list_filter = ("classobj", "lesson", "due_date", "created_at")
    search_fields = (
        "teacher__firstname",
        "teacher__lastname",
        "teacher__user__username",
        "classobj__name",
        "lesson__name",
        "description",
    )
    autocomplete_fields = ("teacher", "classobj", "lesson")
    list_select_related = ("teacher", "classobj", "lesson")
    ordering = ("-created_at",)
