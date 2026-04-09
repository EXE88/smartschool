from django import forms
from django.contrib import admin
from .models import Subjects, Grades, Classes, Lessons, Teachers, Students


class TeachersAdminForm(forms.ModelForm):
    class Meta:
        model = Teachers
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        selected = cleaned.get("teachers")
        if not selected:
            return cleaned
        students_list = Students.objects.first()
        if not students_list:
            return cleaned
        if students_list.students.filter(pk__in=selected.values("pk")).exists():
            self.add_error(
                "teachers",
                "this user is already registered in Students list and cannot be a teacher.",
            )
        return cleaned


class StudentsAdminForm(forms.ModelForm):
    class Meta:
        model = Students
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        selected = cleaned.get("students")
        if not selected:
            return cleaned
        teachers_list = Teachers.objects.first()
        if not teachers_list:
            return cleaned
        if teachers_list.teachers.filter(pk__in=selected.values("pk")).exists():
            self.add_error(
                "students",
                "this user is already registered in Teachers list and cannot be a student.",
            )
        return cleaned

@admin.register(Subjects)
class SubjectsAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)

@admin.register(Grades)
class GradesAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)

@admin.register(Classes)
class ClassesAdmin(admin.ModelAdmin):
    list_display = ("name", "grade", "subject")
    list_filter = ("grade", "subject")
    search_fields = ("name",)
    ordering = ("name",)
    autocomplete_fields = ("grade", "subject")

@admin.register(Lessons)
class LessonsAdmin(admin.ModelAdmin):
    list_display = ("name", "grade", "subject")
    list_filter = ("grade", "subject")
    search_fields = ("name",)
    ordering = ("grade", "subject", "name")
    autocomplete_fields = ("grade", "subject")

@admin.register(Teachers)
class TeachersAdmin(admin.ModelAdmin):
    form = TeachersAdminForm
    list_display = ("id", "teachers_count")
    filter_horizontal = ("teachers",)

    def teachers_count(self, obj):
        return obj.teachers.count()
    teachers_count.short_description = "Teachers"

    def has_add_permission(self, request):
        return not Teachers.objects.exists()

@admin.register(Students)
class StudentsAdmin(admin.ModelAdmin):
    form = StudentsAdminForm
    list_display = ("id", "students_count")
    filter_horizontal = ("students",)

    def students_count(self, obj):
        return obj.students.count()
    students_count.short_description = "Students"

    def has_add_permission(self, request):
        return not Students.objects.exists()
