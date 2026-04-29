from django.contrib import admin

from .models import TeacherComment


@admin.register(TeacherComment)
class TeacherCommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "teacher",
        "student",
        "checked",
        "checked_at",
        "created_at",
        "message_preview",
    )
    list_filter = (
        "checked",
        "teacher",
        "student__grade",
        "student__subject",
        "student__classobj",
        "created_at",
        "checked_at",
    )
    search_fields = (
        "message",
        "teacher__firstname",
        "teacher__lastname",
        "teacher__nationalcode",
        "teacher__user__username",
        "student__firstname",
        "student__lastname",
        "student__nationalcode",
        "student__user__username",
    )
    autocomplete_fields = ("teacher", "student")
    list_select_related = (
        "teacher",
        "teacher__user",
        "student",
        "student__user",
        "student__grade",
        "student__subject",
        "student__classobj",
    )
    readonly_fields = ("checked_at", "created_at", "updated_at")
    list_editable = ("checked",)
    ordering = ("-created_at",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "teacher",
                    "student",
                    "message",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "checked",
                    "checked_at",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

