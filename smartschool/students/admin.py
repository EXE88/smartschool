from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "firstname", "lastname", "grade", "subject", "classobj")
    list_filter = ("grade", "subject", "classobj")
    search_fields = ("firstname", "lastname", "nationalcode", "user__username", "user__email")
    autocomplete_fields = ("user", "subject", "grade", "classobj")
    list_select_related = ("user", "subject", "grade", "classobj")
    ordering = ("lastname", "firstname")
