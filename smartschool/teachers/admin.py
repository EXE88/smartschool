from django.contrib import admin
from .models import Teacher, TeachingAssignment

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "firstname", "lastname", "phonenumber", "created_at")
    list_filter = ("created_at",)
    search_fields = ("firstname", "lastname", "nationalcode", "user__username", "user__email")
    autocomplete_fields = ("user",)
    list_select_related = ("user",)
    ordering = ("lastname", "firstname")

@admin.register(TeachingAssignment)
class TeachingAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "classobj", "lesson", "created_at")
    list_filter = ("classobj", "lesson", "created_at")
    search_fields = (
        "user__firstname",
        "user__lastname",
        "user__nationalcode",
        "user__user__username",
        "user__user__email",
        "classobj__name",
        "lesson__name",
    )
    autocomplete_fields = ("user", "classobj", "lesson")
    list_select_related = ("user", "classobj", "lesson")
    ordering = ("-created_at",)
